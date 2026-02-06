"""Node for optimizing and formatting final plan."""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base_node import BaseNode
from src.agents.trip_state import TripState, TripView
from src.agents.prompts.optimize_plan_prompts import OPTIMIZE_AND_FORMAT_PLAN_PROMPT
from gen_ai_core_lib.config.logging_config import logger


class OptimizeAndFormatFinalPlanNode(BaseNode):
    """Node that optimizes and formats the final plan for output."""
    
    def __init__(self, llm):
        super().__init__(llm, "optimize_and_format_final_plan")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_AND_FORMAT_PLAN_PROMPT),
            ("human", """Destination: {destination}
Duration: {duration} days
Budget: {budget}
Itinerary: {itinerary}

Optimize this itinerary for efficiency and format it into a beautiful, readable travel plan.""")
        ])
    
    def execute(self, state: TripState) -> Dict[str, Any]:
        """Optimize and format the final plan for output."""
        view = TripView(state)
        day_plan = view.day_wise_plan or []
        
        if not day_plan:
            return {
                "final_plan": "Unable to generate final plan - no day-wise plan available.",
                "current_step": self.node_name,
                "status": "error"
            }
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "destination": view.destination or "Unknown",
                "duration": view.duration_days or "Unknown",
                "budget": view.format_budget(),
                "itinerary": json.dumps(day_plan)
            })
            
            final_plan = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "final_plan": final_plan,
                "optimized_itinerary": day_plan,  # Keep for backward compatibility
                "current_step": self.node_name,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error optimizing and formatting final plan: {e}", exc_info=True)
            # Fallback formatting without optimization
            fallback = f"Trip Plan for {view.destination or 'Unknown'} ({view.duration_days or 'Unknown'} days)\n\n"
            for day in day_plan:
                fallback += f"Day {day.get('day', '?')}: {day.get('theme', '')}\n"
                for activity in day.get('activities', []):
                    fallback += f"  {activity.get('time', '')}: {activity.get('activity', '')}\n"
                fallback += "\n"
            
            return {
                "final_plan": fallback,
                "optimized_itinerary": day_plan,
                "current_step": self.node_name,
                "status": "error",
                "errors": [f"Error optimizing and formatting final plan: {str(e)}"]
            }
