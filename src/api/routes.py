"""API routes for Trip Planner."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Annotated

from gen_ai_core_lib.dependencies.application_container import ApplicationContainer
from gen_ai_core_lib.dependencies.llm_dependencies import get_container
from gen_ai_core_lib.dependencies.session_dependencies import get_session_from_headers
from gen_ai_core_lib.session.session_manager import Session

router = APIRouter()


class TripRequest(BaseModel):
    """Request model for trip planning."""
    destination: str
    duration: Optional[int] = None
    budget: Optional[float] = None
    preferences: Optional[List[str]] = None


class TripResponse(BaseModel):
    """Response model for trip planning."""
    destination: str
    itinerary: List[dict]
    estimated_cost: Optional[float] = None
    status: str


@router.post("/trip/plan", response_model=TripResponse)
async def plan_trip(
    request: TripRequest,
    session: Annotated[Session, Depends(get_session_from_headers)],
    container: Annotated[ApplicationContainer, Depends(get_container)],
):
    """
    Plan a trip based on destination and preferences.
    
    Args:
        request: Trip planning request with destination and preferences
        session: User session (automatically created or retrieved from headers/cookies)
        container: Application container with access to LLM manager, memory manager, etc.
        
    Returns:
        TripResponse with itinerary and details
    """
    try:
        # Access services from container
        session_manager = container.get_session_manager()
        llm_manager = container.get_llm_manager()
        memory_manager = container.get_memory_manager()
        
        # TODO: Integrate with LangGraph for trip planning
        # This is a placeholder implementation
        # Session is available for tracking user context across requests
        itinerary = [
            {
                "day": 1,
                "activities": [
                    {"time": "09:00", "activity": "Check-in at hotel"},
                    {"time": "12:00", "activity": "Lunch at local restaurant"},
                    {"time": "14:00", "activity": "Explore city center"},
                ],
            },
            {
                "day": 2,
                "activities": [
                    {"time": "10:00", "activity": "Visit museums"},
                    {"time": "15:00", "activity": "Shopping"},
                ],
            },
        ]
        
        return TripResponse(
            destination=request.destination,
            itinerary=itinerary,
            estimated_cost=request.budget,
            status="planned",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trip/{trip_id}")
async def get_trip(trip_id: str):
    """
    Get trip details by ID.
    
    Args:
        trip_id: Unique trip identifier
        
    Returns:
        Trip details
    """
    # TODO: Implement trip retrieval from database
    return {
        "trip_id": trip_id,
        "destination": "Example Destination",
        "status": "active",
    }


@router.get("/trip")
async def list_trips(limit: int = 10, offset: int = 0):
    """
    List all trips.
    
    Args:
        limit: Maximum number of trips to return
        offset: Number of trips to skip
        
    Returns:
        List of trips
    """
    # TODO: Implement trip listing from database
    return {
        "trips": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }
