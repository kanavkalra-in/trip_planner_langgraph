"""Node for asking clarifying questions."""
from typing import Dict, Any
from langgraph.types import interrupt

from .base_node import BaseNode
from .constants import QUESTION_TEMPLATES
from src.agents.trip_state import TripState


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
        """Ask clarifying questions for missing information."""
        missing_info = state.get("missing_info", [])
        if not missing_info:
            return {
                "clarifying_questions": [],
                "current_step": self.node_name,
                "status": "in_progress"
            }
        
        # Generate questions for missing fields
        questions = self._generate_questions_for_missing_fields(missing_info)
        
        # Increment loop counter to track how many times we've asked
        current_loop_count = state.get("clarification_loop_count", 0)
        
        # Interrupt execution to wait for user input
        return interrupt({
            "clarifying_questions": questions,
            "missing_fields": missing_info,
            "clarification_loop_count": current_loop_count + 1,
            "current_step": self.node_name,
            "status": "needs_clarification"
        })
