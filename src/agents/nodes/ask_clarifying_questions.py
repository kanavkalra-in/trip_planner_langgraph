"""Node for asking clarifying questions."""
from typing import Dict, Any
from langgraph.types import interrupt

from .base_node import BaseNode
from .constants import QUESTION_TEMPLATES
from src.agents.trip_state import TripState, TripView


class AskClarifyingQuestionsNode(BaseNode):
    """Node that asks clarifying questions for missing information."""
    
    def __init__(self, llm):
        super().__init__(llm, "ask_clarifying_questions")
    
    def _generate_questions_for_missing_fields(self, missing_fields: list[str]) -> list[str]:
        """
        Generate clarifying questions for missing fields.
        
        Args:
            missing_fields: List of field names that are missing
            
        Returns:
            List of question strings
        """
        return [
            QUESTION_TEMPLATES[field]
            for field in missing_fields
            if field in QUESTION_TEMPLATES
        ]
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """
        Ask clarifying questions for missing information.
        
        When interrupt() is called:
        - First time: pauses execution immediately (raises GraphInterrupt internally)
        - When resumed: interrupt() returns the resume value (user_responses)
        """
        view = TripView(state)
        missing_info = view.missing_info
        
        if not missing_info:
            return {
                "clarifying_questions": [],
                "current_step": self.node_name,
                "status": "in_progress"
            }
        
        # Generate questions for missing fields
        questions = self._generate_questions_for_missing_fields(missing_info)
        
        # Increment loop counter to track how many times we've asked
        current_loop_count = view.clarification_loop_count
        
        # Call interrupt() - this will:
        # - First time: pause execution immediately (raises GraphInterrupt internally)
        # - When resuming: return the resume value (user_responses dict from Command(resume=...))
        resume_value = interrupt({
            "clarifying_questions": questions,
            "missing_fields": missing_info,
            "clarification_loop_count": current_loop_count + 1,
            "current_step": self.node_name,
            "status": "needs_clarification"
        })
        
        # If interrupt() returned a value, we're resuming from an interrupt
        # The resume_value contains the user_responses dict passed via Command(resume=...)
        if resume_value:
            # Process user responses and update state
            return {
                "user_responses": resume_value,
                "clarification_loop_count": current_loop_count + 1,
                "current_step": self.node_name,
                "status": "in_progress"
            }
        
        # This code should never be reached when interrupt() is called for the first time
        # interrupt() should pause execution immediately by raising GraphInterrupt internally
        # If we reach here, the interrupt didn't work as expected
        # Return the interrupt state anyway to prevent errors
        return {
            "clarifying_questions": questions,
            "missing_fields": missing_info,
            "clarification_loop_count": current_loop_count + 1,
            "current_step": self.node_name,
            "status": "needs_clarification"
        }