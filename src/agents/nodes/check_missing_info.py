"""Node for checking missing critical information."""
from typing import Dict, Any

from .base_node import BaseNode
from .constants import QUESTION_TEMPLATES
from src.agents.trip_state import TripState
from gen_ai_core_lib.config.logging_config import logger


class CheckMissingInfoNode(BaseNode):
    """Node that checks for missing critical information."""
    
    def __init__(self, llm, clarification_loop_limit: int = 2):
        super().__init__(llm, "check_missing_info")
        self.clarification_loop_limit = clarification_loop_limit
    
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
        """Check for missing critical information."""
        # Check current state values only
        destination = state.get("destination")
        duration_days = state.get("duration_days")
        travel_dates = state.get("travel_dates")
        
        # Check for missing critical fields
        missing = []
        if not destination:
            missing.append("destination")
        if not duration_days:
            missing.append("duration_days")
        if not travel_dates:
            missing.append("travel_dates")
        
        has_missing = len(missing) > 0
        updates = {
            "missing_info": missing,
            "has_missing_info": has_missing,
            "current_step": self.node_name
        }
        
        # If we're stopping due to loop limit, set status and ensure questions exist
        loop_count = state.get("clarification_loop_count", 0)
        if has_missing and loop_count >= self.clarification_loop_limit:
            # Generate questions if not already set
            if not state.get("clarifying_questions"):
                questions = self._generate_questions_for_missing_fields(missing)
                updates["clarifying_questions"] = questions
            updates["status"] = "needs_clarification"
        
        return updates
