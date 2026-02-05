"""LangGraph-based Trip Planner with modular node architecture."""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

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
        temperature: float = DEFAULT_TEMPERATURE
    ):
        """
        Initialize the trip planner graph.
        
        Args:
            llm_manager: LLM manager instance for creating LLM instances
            model_name: Name of the model to use (default: "gpt-4o")
            clarification_loop_limit: Maximum number of clarification loops (default: 2)
            recursion_limit: Maximum recursion depth for graph execution (default: 50)
            temperature: LLM temperature setting (default: 0.7)
        """
        self.llm_manager = llm_manager
        self.model_name = model_name
        self.clarification_loop_limit = clarification_loop_limit
        self.recursion_limit = recursion_limit
        self.llm = llm_manager.get_llm(model_name=model_name, temperature=temperature)
        
        # Initialize all nodes
        self.nodes = self._create_nodes()
        self.graph = self._build_graph()
    
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
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph with all nodes and edges."""
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
        # If we've exceeded the loop limit, stop; otherwise check missing info again
        workflow.add_conditional_edges(
            "ask_clarifying_questions",
            self._should_continue_after_questions,
            {
                "continue_checking": "check_missing_info",
                "stop_needs_info": END
            }
        )
        
        # Planning flow
        workflow.add_edge("identify_attractions", "generate_day_wise_plan")
        workflow.add_edge("generate_day_wise_plan", "optimize_and_format_final_plan")
        workflow.add_edge("optimize_and_format_final_plan", END)
        
        return workflow.compile()
    
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
    
    def _should_continue_after_questions(self, state: TripState) -> Literal["continue_checking", "stop_needs_info"]:
        """
        Determine if we should continue checking after asking questions.
        
        This prevents infinite loops by stopping if we've exceeded the loop limit.
        The interrupt() call will be detected in the stream, but we also need this
        conditional edge to prevent the graph from continuing to loop.
        
        Args:
            state: Current trip state (after ask_clarifying_questions)
            
        Returns:
            "continue_checking" if we should loop back to check_missing_info,
            "stop_needs_info" if we've exceeded the loop limit
        """
        loop_count = state.get("clarification_loop_count", 0)
        has_missing = state.get("has_missing_info", False)
        
        logger.debug(
            f"Checking if should continue after questions: loop_count={loop_count}, "
            f"limit={self.clarification_loop_limit}, has_missing={has_missing}"
        )
        
        # If we've exceeded the loop limit and still have missing info, stop
        if has_missing and loop_count >= self.clarification_loop_limit:
            logger.warning(
                f"Stopping after asking questions - loop limit ({self.clarification_loop_limit}) reached. "
                f"Current loop count: {loop_count}, missing info: {state.get('missing_info', [])}"
            )
            return "stop_needs_info"
        
        # Otherwise, continue checking (the interrupt will be handled in the stream)
        logger.debug("Continuing to check missing info after asking questions")
        return "continue_checking"
    
    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the trip planning graph.
        
        Uses stream() to properly handle interrupts from ask_clarifying_questions node.
        When an interrupt occurs, returns the state at that point so the API can return
        clarifying questions to the user.
        
        Args:
            initial_state: Initial state dictionary (must include user_input)
            
        Returns:
            Final state after graph execution (or state at interrupt point)
        """
        # Build state with proper defaults
        # Reset loop counter if user provided new responses (fresh attempt)
        user_responses = initial_state.get("user_responses", {})
        loop_count = 0 if user_responses else initial_state.get("clarification_loop_count", 0)
        
        state: TripState = {
            "user_input": initial_state.get("user_input"),
            "destination": initial_state.get("destination"),
            "duration_days": initial_state.get("duration_days"),
            "budget": initial_state.get("budget"),
            "travel_dates": initial_state.get("travel_dates"),
            "preferences": initial_state.get("preferences") or [],
            "group_size": initial_state.get("group_size"),
            "accommodation_type": initial_state.get("accommodation_type"),
            "extracted_requirements": None,
            "missing_info": [],  # Must be list, not None, due to Annotated[List, add]
            "has_missing_info": None,
            "clarifying_questions": None,
            "user_responses": user_responses,
            "clarification_loop_count": loop_count,
            "attractions": None,
            "day_wise_plan": None,
            "optimized_itinerary": None,
            "final_plan": None,
            "status": None,
            "current_step": None,
            "errors": [],  # Must be list, not None, due to Annotated[List, add]
        }
        
        # Run the graph with configurable recursion limit to prevent infinite loops
        # Use stream() to handle interrupts properly - when interrupt() is called,
        # the graph pauses and we detect it in the stream
        config = {"recursion_limit": self.recursion_limit}
        
        # Use stream() to handle interrupts properly
        # When interrupt() is called, the graph pauses and we get the state at that point
        final_state = None
        interrupted = False
        
        try:
            for event in self.graph.stream(state, config=config):
                # Check for interrupt events - when interrupt() is called, LangGraph may emit
                # an event with "__interrupt__" key, or the stream may stop early
                if "__interrupt__" in event:
                    # Graph is paused at an interrupt
                    logger.info("Graph execution interrupted - detected __interrupt__ in event")
                    interrupted = True
                    # The state at interrupt should be in the last node's state before interrupt
                    # If we have a final_state, use it; otherwise use initial state
                    if final_state is None:
                        final_state = state
                    break
                else:
                    # Update final_state with the latest state from the event
                    # Events are keyed by node name, get the last one
                    for node_name, node_state in event.items():
                        final_state = node_state
                        logger.debug(f"Node {node_name} completed, state updated")
                        
                        # Check if this node's state indicates an interrupt (status = "needs_clarification")
                        if isinstance(node_state, dict) and node_state.get("status") == "needs_clarification":
                            logger.info(f"Graph execution interrupted at node {node_name} - needs clarification")
                            interrupted = True
                            break
                    
                    if interrupted:
                        break
        except Exception as e:
            # If stream raises an exception related to interrupts, handle it
            logger.error(f"Error during graph stream execution: {e}", exc_info=True)
            # If we have a final_state with clarifying questions, return it
            if final_state and final_state.get("status") == "needs_clarification":
                logger.info("Returning state with clarifying questions despite exception")
                return final_state
            raise
        
        # If no final state was set (shouldn't happen), return the initial state
        if final_state is None:
            logger.warning("No final state returned from graph execution")
            final_state = state
            
        return final_state
