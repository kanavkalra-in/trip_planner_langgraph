"""LangGraph-based Trip Planner with modular node architecture."""
from typing import Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from gen_ai_core_lib.llm.llm_manager import LLMManager
from gen_ai_core_lib.config.logging_config import logger
from src.agents.trip_state import TripState
from src.agents.nodes.extract_requirements import ExtractRequirementsNode
from src.agents.nodes.check_missing_info import CheckMissingInfoNode
from src.agents.nodes.ask_clarifying_questions import AskClarifyingQuestionsNode
from src.agents.nodes.identify_attractions import IdentifyAttractionsNode
from src.agents.nodes.generate_day_wise_plan import GenerateDayWisePlanNode
from src.agents.nodes.optimize_and_format_final_plan import OptimizeAndFormatFinalPlanNode


class TripPlannerGraph:
    """
    LangGraph-based trip planner with modular node architecture.
    
    Each node is a separate class with a single, well-defined responsibility.
    The graph orchestrates the flow between nodes.
    """
    
    # Configuration constants
    DEFAULT_CLARIFICATION_LOOP_LIMIT = 2
    DEFAULT_RECURSION_LIMIT = 50
    DEFAULT_TEMPERATURE = 0.7
    
    def __init__(
        self, 
        llm_manager: LLMManager, 
        model_name: str = "gpt-4o",
        clarification_loop_limit: int = DEFAULT_CLARIFICATION_LOOP_LIMIT,
        recursion_limit: int = DEFAULT_RECURSION_LIMIT,
        temperature: float = DEFAULT_TEMPERATURE,
        checkpointer = None
    ):
        """
        Initialize the trip planner graph.
        
        Args:
            llm_manager: LLM manager instance for creating LLM instances
            model_name: Name of the model to use (default: "gpt-4o")
            clarification_loop_limit: Maximum number of clarification loops (default: 2)
            recursion_limit: Maximum recursion depth for graph execution (default: 50)
            temperature: LLM temperature setting (default: 0.7)
            checkpointer: Optional checkpointer for state persistence (defaults to MemorySaver)
        """
        self.llm_manager = llm_manager
        self.model_name = model_name
        self.clarification_loop_limit = clarification_loop_limit
        self.recursion_limit = recursion_limit
        self.temperature = temperature
        
        # Eager initialization
        self.llm = llm_manager.get_llm(model_name=model_name, temperature=temperature)
        self.nodes = self._create_nodes()
        self.graph = self._build_graph(checkpointer=checkpointer)
    
    def _create_nodes(self) -> Dict[str, Any]:
        """Create and return all node instances."""
        return {
            "extract_requirements": ExtractRequirementsNode(self.llm),
            "check_missing_info": CheckMissingInfoNode(
                self.llm, 
                clarification_loop_limit=self.clarification_loop_limit
            ),
            "ask_clarifying_questions": AskClarifyingQuestionsNode(self.llm),
            "identify_attractions": IdentifyAttractionsNode(self.llm),
            "generate_day_wise_plan": GenerateDayWisePlanNode(self.llm),
            "optimize_and_format_final_plan": OptimizeAndFormatFinalPlanNode(self.llm),
        }
    
    def _build_graph(self, checkpointer=None):
        """
        Build the LangGraph StateGraph with all nodes and edges.
        
        Args:
            checkpointer: Optional checkpointer for state persistence (defaults to MemorySaver)
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(TripState)
        
        # Add all nodes
        for node_name, node_instance in self.nodes.items():
            workflow.add_node(node_name, node_instance)
        
        # Define the flow
        workflow.set_entry_point("extract_requirements")
        
        # After extracting requirements, check for missing info
        workflow.add_edge("extract_requirements", "check_missing_info")
        
        # Conditional edge: if missing info, ask questions; otherwise proceed
        workflow.add_conditional_edges(
            "check_missing_info",
            self._should_ask_questions,
            {
                "ask_questions": "ask_clarifying_questions",
                "continue": "identify_attractions",
                "stop_needs_info": END
            }
        )
        
        # After asking questions, conditionally loop back or stop
        # If we've exceeded the loop limit, stop; otherwise re-extract requirements with user responses
        workflow.add_conditional_edges(
            "ask_clarifying_questions",
            self._should_continue_after_questions,
            {
                "re_extract": "extract_requirements",
                "stop_needs_info": END
            }
        )
        
        # Planning flow
        workflow.add_edge("identify_attractions", "generate_day_wise_plan")
        workflow.add_edge("generate_day_wise_plan", "optimize_and_format_final_plan")
        workflow.add_edge("optimize_and_format_final_plan", END)
        
        # Use checkpointer for interrupt support (required by LangGraph)
        # In production, use a persistent checkpointer (e.g., database-backed)
        if checkpointer is None:
            checkpointer = MemorySaver()
        
        return workflow.compile(checkpointer=checkpointer)
    
    def _should_ask_questions(self, state: TripState) -> Literal["ask_questions", "continue", "stop_needs_info"]:
        """
        Determine if we should ask clarifying questions.
        
        Args:
            state: Current trip state
            
        Returns:
            "ask_questions" if missing info exists and we haven't exceeded loop limit,
            "stop_needs_info" if we've hit the loop limit and still have missing info,
            "continue" if no missing info
        """
        has_missing = state.get("has_missing_info", False)
        loop_count = state.get("clarification_loop_count", 0)
        
        # If we've already asked questions multiple times without new responses, stop and require info
        if has_missing and loop_count >= self.clarification_loop_limit:
            missing_info = state.get("missing_info", [])
            logger.warning(
                f"Stopping trip planning - missing critical information after {loop_count} iterations. "
                f"Missing: {missing_info}"
            )
            return "stop_needs_info"
        
        return "ask_questions" if has_missing else "continue"
    
    def _should_continue_after_questions(self, state: TripState) -> Literal["re_extract", "stop_needs_info"]:
        """
        Determine if we should continue after asking questions.
        
        When interrupt() is called, the graph pauses. This conditional edge is evaluated
        when the graph resumes (after user provides responses via Command(resume=...)).
        
        Args:
            state: Current trip state (after ask_clarifying_questions)
            
        Returns:
            "re_extract" if we should re-extract requirements with user responses,
            "stop_needs_info" if we've exceeded loop limit
        """
        loop_count = state.get("clarification_loop_count", 0)
        has_missing = state.get("has_missing_info", False)
        missing_info = state.get("missing_info", [])
        user_responses = state.get("user_responses", {})
        
        logger.debug(
            f"Checking if should continue after questions: loop_count={loop_count}, "
            f"limit={self.clarification_loop_limit}, has_missing={has_missing}, "
            f"has_user_responses={bool(user_responses)}"
        )
        
        # If we've exceeded the loop limit and still have missing info, stop
        if has_missing and loop_count >= self.clarification_loop_limit:
            logger.warning(
                f"Stopping after asking questions - loop limit ({self.clarification_loop_limit}) reached. "
                f"Current loop count: {loop_count}, missing info: {missing_info}"
            )
            return "stop_needs_info"
        
        # If we have user responses, re-extract requirements to process them
        # This will update the state with extracted fields from user responses
        if user_responses:
            logger.info(
                f"Re-extracting requirements with user responses. "
                f"Response keys: {list(user_responses.keys())}"
            )
            return "re_extract"
        
        # If no user responses but we're here, something unexpected happened
        # Still try to re-extract (extract_requirements handles missing user_responses gracefully)
        logger.warning("No user_responses found after ask_clarifying_questions, but continuing anyway")
        return "re_extract"
    
    def run(
        self, 
        initial_state: Dict[str, Any], 
        thread_id: str,
        resume_value: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Run the trip planning graph with interrupt support.
        
        Following LangGraph best practices from https://docs.langchain.com/oss/python/langgraph/interrupts:
        - Uses checkpointer to persist state
        - Uses thread_id to identify execution context
        - Detects interrupts via __interrupt__ field in stream events
        - Resumes with Command(resume=...) when resume_value is provided
        
        Args:
            initial_state: Initial state dictionary (must include user_input)
            thread_id: Thread ID for state persistence (typically session_id)
            resume_value: Optional value to resume from interrupt (becomes return value of interrupt())
            
        Returns:
            Final state after graph execution, or state at interrupt point with __interrupt__ field
        """
        # Build config with thread_id for checkpointer (following LangGraph pattern)
        # Format: config = {"configurable": {"thread_id": "thread-1"}}
        config = {"configurable": {"thread_id": thread_id}}
        
        # If resuming, use Command(resume=...) as input
        # Otherwise, use initial_state
        if resume_value is not None:
            # Resuming from interrupt - the resume_value becomes the return value of interrupt()
            # Pattern: graph.invoke(Command(resume=True), config=config)
            # The checkpointer will automatically load the previous state for this thread_id
            # and resume execution from the node that called interrupt()
            input_data = Command(resume=resume_value)
            logger.info(
                f"Resuming graph execution for thread_id: {thread_id} "
                f"with resume_value keys: {list(resume_value.keys()) if isinstance(resume_value, dict) else 'N/A'}"
            )
        else:
            # New execution - build state from initial_state
            # Pattern: graph.invoke({"input": "data"}, config=config)
            state: TripState = {
                "user_input": initial_state.get("user_input"),
                "destination": initial_state.get("destination"),
                "duration_days": initial_state.get("duration_days"),
                "budget": initial_state.get("budget"),
                "travel_start_date": initial_state.get("travel_start_date"),
                "travel_end_date": initial_state.get("travel_end_date"),
                "preferences": initial_state.get("preferences") or [],
                "group_size": initial_state.get("group_size"),
                "accommodation_type": initial_state.get("accommodation_type"),
                "extracted_requirements": None,
                "missing_info": [],
                "has_missing_info": None,
                "clarifying_questions": None,
                "user_responses": initial_state.get("user_responses") or {},
                "clarification_loop_count": 0,
                "attractions": None,
                "day_wise_plan": None,
                "optimized_itinerary": None,
                "final_plan": None,
                "status": None,
                "current_step": None,
                "errors": [],
            }
            input_data = state
            logger.info(f"Starting new graph execution for thread_id: {thread_id}")
        
        # Use invoke() to get the final state with interrupt information
        # Following LangGraph interrupt pattern: https://docs.langchain.com/oss/python/langgraph/interrupts
        # When interrupt() is called, invoke() returns the result with __interrupt__ field
        # According to docs, invoke() is the recommended method for interrupt detection
        result = self.graph.invoke(input_data, config=config)
        
        # Check if execution was interrupted
        # According to LangGraph docs, interrupts appear as __interrupt__ field in the result
        # Format: result["__interrupt__"] is a list of Interrupt objects, each with .value attribute
        # The interrupt value (dict passed to interrupt()) is in result["__interrupt__"][0].value
        if "__interrupt__" in result:
            logger.info(f"Graph execution interrupted for thread_id: {thread_id}")
            
            # Extract the interrupt value from the Interrupt object
            # The interrupt value contains the state updates passed to interrupt()
            interrupt_info = result["__interrupt__"]
            interrupt_value = {}
            
            if interrupt_info and len(interrupt_info) > 0:
                interrupt_obj = interrupt_info[0]
                # Extract the value from the Interrupt object
                if hasattr(interrupt_obj, 'value'):
                    interrupt_value = interrupt_obj.value
                elif isinstance(interrupt_obj, dict):
                    interrupt_value = interrupt_obj
                
                # Merge the interrupt value into the result, ensuring it takes precedence
                # This ensures values like clarifying_questions, current_step, etc. from interrupt() 
                # overwrite any conflicting values from previous nodes
                result.update(interrupt_value)
                logger.debug(f"Merged interrupt value into result. Interrupt keys: {list(interrupt_value.keys())}")
            
            return result
        
        # Execution completed normally
        logger.info(f"Graph execution completed for thread_id: {thread_id}")
        return result
