"""Node for identifying attractions."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState, TripView
from src.agents.utils.json_parser import parse_json_response
from src.agents.prompts.identify_attractions_prompts import IDENTIFY_ATTRACTIONS_PROMPT
from gen_ai_core_lib.config.logging_config import logger


class IdentifyAttractionsNode(BaseNode):
    """Node that identifies attractions based on requirements."""
    
    def __init__(self, llm):
        super().__init__(llm, "identify_attractions")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", IDENTIFY_ATTRACTIONS_PROMPT),
            ("human", """Destination: {destination}
Duration: {duration} days
Preferences: {preferences}

Identify attractions that match these criteria.""")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Identify attractions based on requirements."""
        view = TripView(state)
        
        if not view.destination:
            return {
                "attractions": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": ["Destination is required to identify attractions"]
            }
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "destination": view.destination,
                "duration": view.duration_days or "not specified",
                "preferences": view.format_preferences()
            })
            
            attractions = parse_json_response(response)
            
            return {
                "attractions": attractions,
                "current_step": self.node_name
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}", exc_info=True)
            return {
                "attractions": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error parsing attractions: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Error identifying attractions: {e}", exc_info=True)
            return {
                "attractions": [],
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error identifying attractions: {str(e)}"]
            }
