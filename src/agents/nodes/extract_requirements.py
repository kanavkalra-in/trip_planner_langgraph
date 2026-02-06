"""Node for extracting structured requirements from user input."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState
from src.agents.utils.json_parser import parse_json_response
from src.agents.prompts.extract_requirements_prompts import EXTRACT_REQUIREMENTS_PROMPT
from gen_ai_core_lib.config.logging_config import logger


class ExtractRequirementsNode(BaseNode):
    """Node that extracts structured requirements from user input."""
    
    def __init__(self, llm):
        super().__init__(llm, "extract_requirements")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_REQUIREMENTS_PROMPT),
            ("human", "User input: {user_input}")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Extract structured requirements from user input and user responses."""
        user_input = state.get("user_input", "")
        user_responses = state.get("user_responses", {})
        
        # Combine user_input with user_responses for extraction
        # When resuming after an interrupt, user_responses contain answers to clarifying questions
        combined_input = user_input
        if user_responses:
            # Format user_responses as additional context
            responses_text = "\n\nUser responses to clarifying questions:\n"
            for key, value in user_responses.items():
                responses_text += f"- {key}: {value}\n"
            combined_input = f"{user_input}\n{responses_text}" if user_input else responses_text
        
        if not combined_input:
            return {
                "extracted_requirements": {},
                "current_step": self.node_name,
                "status": "error",
                "errors": ["No user input provided"]
            }
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({"user_input": combined_input})
            extracted = parse_json_response(response)
            
            # Build partial state update
            updates: Dict[str, Any] = {
                "extracted_requirements": extracted,
                "current_step": self.node_name
            }
            
            # Map extracted values to state fields
            field_mapping = [
                "destination", "duration_days", "budget", "travel_start_date", "travel_end_date",
                "preferences", "group_size", "accommodation_type"
            ]
            for field in field_mapping:
                if field in extracted and extracted[field] is not None:
                    updates[field] = extracted[field]
            
            return updates
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}", exc_info=True)
            return {
                "extracted_requirements": {},
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error parsing extracted requirements: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}", exc_info=True)
            return {
                "extracted_requirements": {},
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error extracting requirements: {str(e)}"]
            }
