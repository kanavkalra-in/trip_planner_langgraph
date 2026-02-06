"""Node for extracting structured requirements from user input."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState, TripView
from src.agents.utils.json_parser import parse_json_response
from src.agents.prompts.extract_requirements_prompts import EXTRACT_REQUIREMENTS_PROMPT
from gen_ai_core_lib.llm.llm_manager import get_default_llm_manager
from gen_ai_core_lib.config.logging_config import logger


class ExtractRequirementsNode(BaseNode):
    """Node that extracts structured requirements from user input."""
    
    def __init__(
        self, 
        model_name: str = "gpt-4o",
        temperature: float = 0.7
    ):
        super().__init__(None, "extract_requirements")
        self.model_name = model_name
        self.temperature = temperature
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_REQUIREMENTS_PROMPT),
            ("human", "User input: {user_input}")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Extract structured requirements from user input and user responses."""
        view = TripView(state)
        user_input = view.user_input or ""
        user_responses = view.user_responses
        
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
            llm_manager = get_default_llm_manager()
            llm = llm_manager.get_llm(model_name=self.model_name, temperature=self.temperature)
            chain = self.prompt | llm
            response = chain.invoke({"user_input": combined_input})
            extracted = parse_json_response(response)
            
            # Build partial state update
            updates: Dict[str, Any] = {
                "extracted_requirements": extracted,
                "current_step": self.node_name
            }
            
            # Map all extracted values to state fields
            # This ensures all extracted information flows through the graph state
            field_mapping = [
                "destination",
                "duration_days",
                "budget",
                "travel_start_date",
                "travel_end_date",
                "daily_itinerary_start_time",
                "daily_itinerary_end_time",
                "group_size",
                "accommodation_type",
            ]
            
            # Map simple fields
            for field in field_mapping:
                if field in extracted and extracted[field] is not None:
                    updates[field] = extracted[field]
            
            # Map list fields (these use Annotated[List, add] reducers in TripState)
            list_fields = [
                "preferences",
                "accommodation_amenities",
                "transport_preferences",
                "additional_requirements",
            ]
            for field in list_fields:
                if field in extracted and extracted[field] is not None:
                    # Ensure it's a list
                    value = extracted[field]
                    if isinstance(value, list):
                        updates[field] = value
                    elif value:  # If it's a single value, wrap it in a list
                        updates[field] = [value]
            
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
