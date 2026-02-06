"""Node for checking missing critical information."""
from typing import Dict, Any
from datetime import datetime, timedelta

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
        travel_start_date = state.get("travel_start_date")
        travel_end_date = state.get("travel_end_date")
        
        # Calculate travel_end_date if only duration_days and travel_start_date are present
        # If travel_end_date is already present, give preference to it (don't recalculate)
        updates = {}
        if not travel_end_date and travel_start_date and duration_days:
            try:
                start_date = datetime.strptime(travel_start_date, "%Y-%m-%d")
                end_date = start_date + timedelta(days=duration_days - 1)  # -1 because start day counts as day 1
                travel_end_date = end_date.strftime("%Y-%m-%d")
                updates["travel_end_date"] = travel_end_date
                logger.info(f"Calculated travel_end_date: {travel_end_date} from start_date: {travel_start_date} and duration: {duration_days} days")
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate travel_end_date: {e}")
        
        # Check for missing critical fields
        missing = []
        if not destination:
            missing.append("destination")
        if not duration_days:
            missing.append("duration_days")
        if not travel_start_date:
            missing.append("travel_start_date")
        if not travel_end_date:
            missing.append("travel_end_date")
        
        has_missing = len(missing) > 0
        updates.update({
            "missing_info": missing,
            "has_missing_info": has_missing,
            "current_step": self.node_name
        })
        
        # If we're stopping due to loop limit, set status and ensure questions exist
        loop_count = state.get("clarification_loop_count", 0)
        if has_missing and loop_count >= self.clarification_loop_limit:
            # Generate questions if not already set
            if not state.get("clarifying_questions"):
                questions = self._generate_questions_for_missing_fields(missing)
                updates["clarifying_questions"] = questions
            updates["status"] = "needs_clarification"
        
        return updates
