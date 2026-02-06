"""Node for identifying attractions and generating day-wise plan (merged)."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState, TripView
from src.agents.utils.json_parser import parse_json_response
from src.agents.prompts.identify_attractions_and_plan_prompts import IDENTIFY_ATTRACTIONS_AND_GENERATE_PLAN_PROMPT
from gen_ai_core_lib.config.logging_config import logger


class IdentifyAttractionsAndPlanNode(BaseNode):
    """Node that identifies attractions and generates detailed day-wise plan in one step."""
    
    def __init__(self, llm):
        super().__init__(llm, "identify_attractions_and_plan")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", IDENTIFY_ATTRACTIONS_AND_GENERATE_PLAN_PROMPT),
            ("human", """Destination: {destination}
Duration: {duration} days
Travel Start Date: {travel_start_date}
Travel End Date: {travel_end_date}
Daily Start Time: {daily_start_time}
Daily End Time: {daily_end_time}
Preferences: {preferences}
Group Size: {group_size}
Budget: {budget}
Accommodation Type: {accommodation_type}
Accommodation Amenities: {accommodation_amenities}
Transport Preferences: {transport_preferences}
Additional Requirements: {additional_requirements}

Identify attractions that match these criteria and create a detailed day-by-day plan with specific times and activities, organizing attractions into logical daily themes.""")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Identify attractions and generate day-wise plan in one step."""
        view = TripView(state)
        
        if not view.destination:
            return {
                "attractions": [],
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": ["Destination is required to identify attractions and create plan"]
            }
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "destination": view.destination,
                "duration": view.duration_days or "not specified",
                "travel_start_date": view.travel_start_date or "not specified",
                "travel_end_date": view.travel_end_date or "not specified",
                "daily_start_time": view.daily_start_time,
                "daily_end_time": view.daily_end_time,
                "preferences": view.format_preferences(),
                "group_size": view.group_size or "not specified",
                "budget": view.format_budget(),
                "accommodation_type": view.accommodation_type,
                "accommodation_amenities": view.format_list_field("accommodation_amenities"),
                "transport_preferences": view.format_list_field("transport_preferences"),
                "additional_requirements": view.format_list_field("additional_requirements"),
            })
            
            result = parse_json_response(response)
            
            # Extract attractions and day_wise_plan from the response
            attractions = result.get("attractions", [])
            day_wise_plan = result.get("day_wise_plan", [])
            
            # Validate that we got both expected keys
            if not attractions:
                logger.warning("No attractions returned from merged node")
            if not day_wise_plan:
                logger.warning("No day_wise_plan returned from merged node")
            
            return {
                "attractions": attractions,
                "day_wise_plan": day_wise_plan,
                "current_step": self.node_name
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}", exc_info=True)
            return {
                "attractions": [],
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error parsing response: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Error identifying attractions and generating plan: {e}", exc_info=True)
            return {
                "attractions": [],
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error identifying attractions and generating plan: {str(e)}"]
            }
