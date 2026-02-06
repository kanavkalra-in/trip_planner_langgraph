"""
TripState TypedDict definition for LangGraph trip planner.

This defines the state structure that flows through the trip planning graph.
All nodes read from and write to this state.
"""
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from operator import add


class TripState(TypedDict):
    """
    State structure for the trip planning graph.
    
    This TypedDict defines all fields that can be present in the state.
    Fields are optional to allow incremental state building.
    Fields with Annotated[List, add] use reducers for proper state merging.
    """
    # User input (initial) - optional to allow incremental building
    user_input: Optional[str]
    destination: Optional[str]
    duration_days: Optional[int]
    budget: Optional[float]
    travel_start_date: Optional[str]  # e.g., "2024-06-15"
    travel_end_date: Optional[str]  # e.g., "2024-06-20"
    preferences: Annotated[List[str], add]  # Use reducer for list accumulation
    group_size: Optional[int]
    accommodation_type: Optional[str]  # e.g., "hotel", "hostel", "airbnb"
    
    # Extracted requirements (from extract_requirements node)
    extracted_requirements: Optional[Dict[str, Any]]
    
    # Missing information tracking (from check_missing_info node)
    missing_info: Annotated[List[str], add]  # Use reducer for list accumulation
    has_missing_info: Optional[bool]
    
    # Clarification questions (from ask_clarifying_questions node)
    clarifying_questions: Optional[List[str]]
    user_responses: Optional[Dict[str, str]]  # Map question -> answer
    clarification_loop_count: Optional[int]  # Track how many times we've asked questions
    
    # Attractions (from identify_attractions node)
    attractions: Optional[List[Dict[str, Any]]]  # List of attraction dicts with name, type, etc.
    
    # Day-wise plan (from generate_day_wise_plan node)
    day_wise_plan: Optional[List[Dict[str, Any]]]  # List of day plans
    
    # Optimized itinerary (from optimize_itinerary node)
    optimized_itinerary: Optional[List[Dict[str, Any]]]
    
    # Final formatted plan (from format_final_plan node)
    final_plan: Optional[str]
    
    # Status tracking
    status: Optional[str]  # "in_progress", "needs_clarification", "completed", "error"
    
    # Metadata
    current_step: Optional[str]  # Track which node is currently executing
    errors: Annotated[List[str], add]  # Use reducer for error accumulation
