"""Node for optimizing and formatting final plan."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState, TripView
from src.agents.prompts.optimize_plan_prompts import OPTIMIZE_AND_FORMAT_PLAN_PROMPT
from gen_ai_core_lib.llm.llm_manager import get_default_llm_manager


class OptimizeAndFormatFinalPlanNode(BaseNode):
    """Node that optimizes and formats the final plan for output."""
    
    def __init__(
        self, 
        model_name: str = "gpt-4o",
        temperature: float = 0.7
    ):
        super().__init__(None, "optimize_and_format_final_plan")
        self.model_name = model_name
        self.temperature = temperature
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_AND_FORMAT_PLAN_PROMPT),
            ("human", """Destination: {destination}
Duration: {duration} days
Budget: {budget}
Itinerary: {itinerary}

Optimize this itinerary for efficiency and format it into a beautiful, readable travel plan.""")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """
        Optimize and format the final plan for output.
        """
        view = TripView(state)
        day_plan = view.day_wise_plan or []
        
        if not day_plan:
            return {
                "final_plan": "Unable to generate final plan - no day-wise plan available.",
                "current_step": self.node_name,
                "status": "error"
            }
        
        llm_manager = get_default_llm_manager()
        llm = llm_manager.get_llm(model_name=self.model_name, temperature=self.temperature)
        chain = self.prompt | llm
        response = chain.invoke({
            "destination": view.destination or "Unknown",
            "duration": view.duration_days or "Unknown",
            "budget": view.format_budget(),
            "itinerary": json.dumps(day_plan)
        })
        
        final_plan = response.content if hasattr(response, 'content') else str(response)
        
        # Return the final plan without interruption - allows continuous chat flow
        return {
            "final_plan": final_plan,
            "optimized_itinerary": day_plan,  # Keep for backward compatibility
            "current_step": self.node_name,
            "status": "completed"
        }
