"""API routes for Trip Planner."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Annotated, Dict, Any
import uuid

from gen_ai_core_lib.dependencies.session_dependencies import get_session_from_headers
from gen_ai_core_lib.session.session_manager import Session
from gen_ai_core_lib.config.logging_config import logger
from src.agents.trip_planner_graph import TripPlannerGraph
from src.api.dependencies import get_trip_planner

router = APIRouter()


class TripRequest(BaseModel):
    """Request model for trip planning - chat conversation only."""
    user_input: Optional[str] = None  # Required for new requests, optional when resuming
    user_responses: Optional[Dict[str, str]] = None  # For responding to clarifying questions (resume value)
    thread_id: Optional[str] = None  # Optional thread_id for resuming existing conversation


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
    thread_id: Optional[str] = None  # Thread ID for resuming this conversation


@router.post("/trip/plan", response_model=TripResponse)
async def plan_trip(
    request: TripRequest,
    session: Annotated[Session, Depends(get_session_from_headers)],
    planner: Annotated[TripPlannerGraph, Depends(get_trip_planner)],
):
    """
    Plan a trip based on chat conversation with interrupt support.
    
    Following LangGraph interrupt patterns (https://docs.langchain.com/oss/python/langgraph/interrupts):
    - Uses thread_id (session_id) for state persistence
    - Detects interrupts via __interrupt__ field
    - Resumes with user_responses when provided
    
    Args:
        request: Trip planning request
            - user_input: Required for new requests
            - user_responses: Optional, used to resume from interrupt
        session: User session (automatically created or retrieved from headers/cookies)
        planner: Trip planner graph (injected via dependency injection, singleton)
        
    Returns:
        TripResponse with itinerary, clarifying questions, or final plan
    """
    
    # Generate or use provided thread_id for state persistence
    # Each trip planning conversation gets a unique thread_id, allowing multiple
    # concurrent conversations even within the same session
    if request.thread_id:
        # Resuming existing conversation - use provided thread_id
        thread_id = request.thread_id
        logger.info(f"Resuming conversation with thread_id: {thread_id}")
    else:
        # New conversation - generate unique thread_id
        # This ensures uniqueness both within and outside the session
        thread_id = str(uuid.uuid4())
        logger.info(f"Starting new conversation with thread_id: {thread_id}")
    
    # Determine if we're resuming from an interrupt
    is_resuming = request.user_responses is not None and len(request.user_responses) > 0
    
    if is_resuming:
        # Resuming from interrupt - user_responses becomes the resume value
        # The resume value is passed to Command(resume=...) and becomes the return value of interrupt()
        resume_value = request.user_responses
        logger.info(f"Resuming graph execution with user responses: {list(resume_value.keys())}")
        result = planner.run({}, thread_id=thread_id, resume_value=resume_value)
    else:
        # New execution - user_input is required
        if not request.user_input:
            raise HTTPException(
                status_code=400, 
                detail="user_input is required for new trip planning requests"
            )
        
        initial_state = {
            "user_input": request.user_input,
            "user_responses": {},
        }
        logger.info(f"Starting new trip planning request: {request.user_input[:100]}...")
        result = planner.run(initial_state, thread_id=thread_id)
    
    # Check if execution was interrupted
    if "__interrupt__" in result:
        # Extract interrupt value - contains the state update from interrupt() call
        interrupt_info = result["__interrupt__"]
        logger.info(f"Graph execution interrupted. Interrupt info: {interrupt_info}")
        
        # The interrupt value is a list of Interrupt objects
        # Extract the state update from the first interrupt
        interrupt_value = {}
        if interrupt_info and len(interrupt_info) > 0:
            interrupt_obj = interrupt_info[0]
            if hasattr(interrupt_obj, 'value'):
                interrupt_value = interrupt_obj.value
            elif isinstance(interrupt_obj, dict):
                interrupt_value = interrupt_obj
        
        # Merge interrupt state with result state
        final_state = {**result, **interrupt_value}
        status = final_state.get("status", "needs_clarification")
    else:
        # Execution completed normally
        final_state = result
        status = final_state.get("status", "completed")
    
    # Extract itinerary from day_wise_plan or optimized_itinerary
    itinerary = None
    if final_state.get("optimized_itinerary"):
        itinerary = final_state["optimized_itinerary"]
    elif final_state.get("day_wise_plan"):
        itinerary = final_state["day_wise_plan"]
    
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
        thread_id=thread_id,  # Always return thread_id so client can use it for resuming
    )


