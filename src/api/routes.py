"""API routes for Trip Planner."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Annotated, Dict, Any

from gen_ai_core_lib.dependencies.application_container import ApplicationContainer
from gen_ai_core_lib.dependencies.llm_dependencies import get_container
from gen_ai_core_lib.dependencies.session_dependencies import get_session_from_headers
from gen_ai_core_lib.session.session_manager import Session
from gen_ai_core_lib.config.logging_config import logger
from src.agents.trip_planner_graph import TripPlannerGraph

router = APIRouter()


class TripRequest(BaseModel):
    """Request model for trip planning - chat conversation only."""
    user_input: str  # Required: natural language user input
    user_responses: Optional[Dict[str, str]] = None  # For responding to clarifying questions


class TripResponse(BaseModel):
    """Response model for trip planning."""
    destination: Optional[str] = None
    itinerary: Optional[List[dict]] = None
    day_wise_plan: Optional[List[dict]] = None
    estimated_cost: Optional[float] = None
    status: str
    final_plan: Optional[str] = None
    extracted_requirements: Optional[Dict[str, Any]] = None
    missing_info: Optional[List[str]] = None
    clarifying_questions: Optional[List[str]] = None
    attractions: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None


@router.post("/trip/plan", response_model=TripResponse)
async def plan_trip(
    request: TripRequest,
    session: Annotated[Session, Depends(get_session_from_headers)],
    container: Annotated[ApplicationContainer, Depends(get_container)],
):
    """
    Plan a trip based on chat conversation.
    
    This endpoint uses LangGraph to plan trips with support for:
    - Natural language input (user_input) - required
    - User responses to clarifying questions (user_responses)
    - Clarifying questions when information is missing
    - Full trip planning workflow
    
    Args:
        request: Trip planning request with user_input and optional user_responses
        session: User session (automatically created or retrieved from headers/cookies)
        container: Application container with access to LLM manager, memory manager, etc.
        
    Returns:
        TripResponse with itinerary, clarifying questions, or final plan
    """
    try:
        # Access services from container
        llm_manager = container.get_llm_manager()
        
        # Create trip planner graph
        planner = TripPlannerGraph(llm_manager, model_name="gpt-4o")
        
        # Build initial state from request - chat conversation only
        initial_state = {
            "user_input": request.user_input,
            "user_responses": request.user_responses or {},
        }
        
        # Run the trip planner graph
        logger.info("Running trip planner graph")
        final_state = planner.run(initial_state)
        
        # Extract itinerary from day_wise_plan or optimized_itinerary
        itinerary = None
        if final_state.get("optimized_itinerary"):
            itinerary = final_state["optimized_itinerary"]
        elif final_state.get("day_wise_plan"):
            itinerary = final_state["day_wise_plan"]
        
        # Get status from state (graph nodes set this appropriately)
        # Default to "in_progress" if not set (shouldn't happen with proper graph execution)
        status = final_state.get("status", "in_progress")
        
        return TripResponse(
            destination=final_state.get("destination"),
            itinerary=itinerary,
            day_wise_plan=final_state.get("day_wise_plan"),
            estimated_cost=final_state.get("budget"),
            status=status,
            final_plan=final_state.get("final_plan"),
            extracted_requirements=final_state.get("extracted_requirements"),
            missing_info=final_state.get("missing_info"),
            clarifying_questions=final_state.get("clarifying_questions"),
            attractions=final_state.get("attractions"),
            errors=final_state.get("errors"),
        )
    except Exception as e:
        logger.error(f"Error planning trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


