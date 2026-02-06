"""
TripState TypedDict definition for LangGraph trip planner.

This defines the state structure that flows through the trip planning graph.
All nodes read from and write to this state.
"""
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from operator import add
from dataclasses import dataclass


@dataclass
class TripRequirements:
    """
    Data class for extracted trip requirements.
    
    This class represents all the structured information extracted from user input.
    All fields are optional to allow partial extraction.
    """
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    travel_start_date: Optional[str] = None  # YYYY-MM-DD format
    travel_end_date: Optional[str] = None  # YYYY-MM-DD format
    daily_itinerary_start_time: Optional[str] = None  # HH:MM, 24-hour format
    daily_itinerary_end_time: Optional[str] = None  # HH:MM, 24-hour format
    budget: Optional[float] = None
    group_size: Optional[int] = None
    preferences: Optional[List[str]] = None
    accommodation_type: Optional[str] = None
    accommodation_amenities: Optional[List[str]] = None
    transport_preferences: Optional[List[str]] = None
    additional_requirements: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TripRequirements":
        """Create TripRequirements from a dictionary."""
        return cls(
            destination=data.get("destination"),
            duration_days=data.get("duration_days"),
            travel_start_date=data.get("travel_start_date"),
            travel_end_date=data.get("travel_end_date"),
            daily_itinerary_start_time=data.get("daily_itinerary_start_time"),
            daily_itinerary_end_time=data.get("daily_itinerary_end_time"),
            budget=data.get("budget"),
            group_size=data.get("group_size"),
            preferences=data.get("preferences"),
            accommodation_type=data.get("accommodation_type"),
            accommodation_amenities=data.get("accommodation_amenities"),
            transport_preferences=data.get("transport_preferences"),
            additional_requirements=data.get("additional_requirements"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TripRequirements to a dictionary."""
        return {
            "destination": self.destination,
            "duration_days": self.duration_days,
            "travel_start_date": self.travel_start_date,
            "travel_end_date": self.travel_end_date,
            "daily_itinerary_start_time": self.daily_itinerary_start_time,
            "daily_itinerary_end_time": self.daily_itinerary_end_time,
            "budget": self.budget,
            "group_size": self.group_size,
            "preferences": self.preferences,
            "accommodation_type": self.accommodation_type,
            "accommodation_amenities": self.accommodation_amenities,
            "transport_preferences": self.transport_preferences,
            "additional_requirements": self.additional_requirements,
        }


class TripView:
    """
    View class for easy access to TripState fields.
    
    This class provides a clean interface to access state fields without
    having to use .get() everywhere. It's easy to maintain and extend.
    """
    def __init__(self, state: Dict[str, Any]):
        self._state = state
    
    # Core trip requirements
    @property
    def destination(self) -> Optional[str]:
        return self._state.get("destination")
    
    @property
    def duration_days(self) -> Optional[int]:
        return self._state.get("duration_days")
    
    @property
    def budget(self) -> Optional[float]:
        return self._state.get("budget")
    
    @property
    def travel_start_date(self) -> Optional[str]:
        return self._state.get("travel_start_date")
    
    @property
    def travel_end_date(self) -> Optional[str]:
        return self._state.get("travel_end_date")
    
    @property
    def daily_start_time(self) -> str:
        """Returns daily itinerary start time, defaulting to 'not specified'."""
        return self._state.get("daily_itinerary_start_time", "not specified")
    
    @property
    def daily_end_time(self) -> str:
        """Returns daily itinerary end time, defaulting to 'not specified'."""
        return self._state.get("daily_itinerary_end_time", "not specified")
    
    @property
    def preferences(self) -> List[str]:
        """Returns preferences list, defaulting to empty list."""
        return self._state.get("preferences", [])
    
    @property
    def group_size(self) -> Optional[int]:
        return self._state.get("group_size")
    
    @property
    def accommodation_type(self) -> str:
        """Returns accommodation type, defaulting to 'not specified'."""
        return self._state.get("accommodation_type", "not specified")
    
    @property
    def accommodation_amenities(self) -> List[str]:
        """Returns accommodation amenities list, defaulting to empty list."""
        return self._state.get("accommodation_amenities", [])
    
    @property
    def transport_preferences(self) -> List[str]:
        """Returns transport preferences list, defaulting to empty list."""
        return self._state.get("transport_preferences", [])
    
    @property
    def additional_requirements(self) -> List[str]:
        """Returns additional requirements list, defaulting to empty list."""
        return self._state.get("additional_requirements", [])
    
    # Other state fields
    @property
    def user_input(self) -> Optional[str]:
        return self._state.get("user_input")
    
    @property
    def extracted_requirements(self) -> Optional[Dict[str, Any]]:
        return self._state.get("extracted_requirements")
    
    @property
    def missing_info(self) -> List[str]:
        return self._state.get("missing_info", [])
    
    @property
    def has_missing_info(self) -> Optional[bool]:
        return self._state.get("has_missing_info")
    
    @property
    def clarifying_questions(self) -> Optional[List[str]]:
        return self._state.get("clarifying_questions")
    
    @property
    def user_responses(self) -> Dict[str, str]:
        return self._state.get("user_responses", {})
    
    @property
    def clarification_loop_count(self) -> int:
        return self._state.get("clarification_loop_count", 0)
    
    @property
    def attractions(self) -> Optional[List[Dict[str, Any]]]:
        return self._state.get("attractions")
    
    @property
    def day_wise_plan(self) -> Optional[List[Dict[str, Any]]]:
        return self._state.get("day_wise_plan")
    
    @property
    def optimized_itinerary(self) -> Optional[List[Dict[str, Any]]]:
        return self._state.get("optimized_itinerary")
    
    @property
    def final_plan(self) -> Optional[str]:
        return self._state.get("final_plan")
    
    @property
    def status(self) -> Optional[str]:
        return self._state.get("status")
    
    @property
    def current_step(self) -> Optional[str]:
        return self._state.get("current_step")
    
    @property
    def errors(self) -> List[str]:
        return self._state.get("errors", [])
    
    # Helper methods for formatting
    def format_preferences(self, separator: str = ", ") -> str:
        """Format preferences as a string."""
        prefs = self.preferences
        return separator.join(prefs) if prefs else "none specified"
    
    def format_budget(self) -> str:
        """Format budget as a string."""
        return f"${self.budget:,.2f}" if self.budget else "not specified"
    
    def format_list_field(self, field_name: str, separator: str = ", ") -> str:
        """Format a list field from state as a string."""
        value = self._state.get(field_name, [])
        if isinstance(value, list):
            return separator.join(value) if value else "none specified"
        return str(value) if value else "none specified"


class TripState(TypedDict):
    """
    State structure for the trip planning graph.
    
    This TypedDict defines all fields that can be present in the state.
    Fields are optional to allow incremental state building.
    Fields with Annotated[List, add] use reducers for proper state merging.
    """
    # User input (initial) - optional to allow incremental building
    user_input: Optional[str]
    
    # Core trip requirements (extracted from user input)
    destination: Optional[str]
    duration_days: Optional[int]
    budget: Optional[float]
    travel_start_date: Optional[str]  # e.g., "2024-06-15"
    travel_end_date: Optional[str]  # e.g., "2024-06-20"
    daily_itinerary_start_time: Optional[str]  # HH:MM, 24-hour format
    daily_itinerary_end_time: Optional[str]  # HH:MM, 24-hour format
    preferences: Annotated[List[str], add]  # Use reducer for list accumulation
    group_size: Optional[int]
    accommodation_type: Optional[str]  # e.g., "hotel", "hostel", "airbnb"
    accommodation_amenities: Annotated[List[str], add]  # Use reducer for list accumulation
    transport_preferences: Annotated[List[str], add]  # Use reducer for list accumulation
    additional_requirements: Annotated[List[str], add]  # Use reducer for list accumulation
    
    # Extracted requirements (from extract_requirements node) - raw dict for backward compatibility
    extracted_requirements: Optional[Dict[str, Any]]
    
    # Missing information tracking (from check_missing_info node)
    missing_info: Annotated[List[str], add]  # Use reducer for list accumulation
    has_missing_info: Optional[bool]
    
    # Clarification questions (from ask_clarifying_questions node)
    clarifying_questions: Optional[List[str]]
    user_responses: Optional[Dict[str, str]]  # Map question -> answer
    clarification_loop_count: Optional[int]  # Track how many times we've asked questions
    
    # Attractions and day-wise plan (from identify_attractions_and_plan node)
    attractions: Optional[List[Dict[str, Any]]]  # List of attraction dicts with name, type, etc.
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
