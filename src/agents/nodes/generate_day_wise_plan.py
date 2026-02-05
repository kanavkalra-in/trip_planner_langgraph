"""Node for generating day-wise plan."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState
from src.agents.utils.json_parser import parse_json_response
from src.agents.prompts.generate_plan_prompts import GENERATE_DAY_WISE_PLAN_PROMPT
from gen_ai_core_lib.config.logging_config import logger


class GenerateDayWisePlanNode(BaseNode):
    """Node that generates detailed day-wise plan from attractions."""
    
    def __init__(self, llm):
        super().__init__(llm, "generate_day_wise_plan")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_DAY_WISE_PLAN_PROMPT),
            ("human", """Destination: {destination}
Duration: {duration} days
Travel Dates: {travel_dates}
Preferences: {preferences}
Attractions: {attractions}

Create a detailed day-by-day plan with specific times and activities, organizing attractions into logical daily themes.""")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Generate detailed day-wise plan directly from attractions."""
        attractions = state.get("attractions", [])
        duration = state.get("duration_days")
        preferences = state.get("preferences", [])
        travel_dates = state.get("travel_dates", "not specified")
        
        if not attractions:
            return {
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": ["No attractions available to create day-wise plan"]
            }
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "destination": state.get("destination", "Unknown"),
                "duration": duration or len(attractions),
                "travel_dates": travel_dates,
                "preferences": ", ".join(preferences) if preferences else "none specified",
                "attractions": json.dumps(attractions)
            })
            
            day_plan = parse_json_response(response)
            
            return {
                "day_wise_plan": day_plan,
                "current_step": self.node_name
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}", exc_info=True)
            return {
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error parsing day-wise plan: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Error generating day-wise plan: {e}", exc_info=True)
            return {
                "day_wise_plan": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error generating day-wise plan: {str(e)}"]
            }
