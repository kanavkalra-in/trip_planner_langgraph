"""Streamlit application for Trip Planner."""

import streamlit as st
import httpx
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from src.core.config import settings

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Page configuration
st.set_page_config(
    page_title="Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API base URL - try Streamlit secrets first, then env, then default
API_BASE_URL = st.secrets.get(
    "API_BASE_URL",
    f"http://localhost:{settings.api_port}/api/v1"
)


def main():
    """Main Streamlit application."""
    st.title("✈️ Trip Planner")
    st.markdown("Plan your perfect trip with AI-powered recommendations")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        api_url = st.text_input(
            "API URL",
            value=API_BASE_URL,
            help="Base URL for the Trip Planner API",
        )
        st.divider()
        st.markdown("### About")
        st.markdown(
            "This application helps you plan trips using LangGraph and AI."
        )
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Plan Trip", "My Trips", "About"])
    
    with tab1:
        plan_trip_tab(api_url)
    
    with tab2:
        my_trips_tab(api_url)
    
    with tab3:
        about_tab()


def plan_trip_tab(api_url: str):
    """Trip planning tab."""
    st.header("Plan Your Trip")
    
    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "Destination",
                placeholder="e.g., Paris, France",
                help="Enter your travel destination",
            )
            duration = st.number_input(
                "Duration (days)",
                min_value=1,
                max_value=30,
                value=3,
                help="Number of days for your trip",
            )
        
        with col2:
            budget = st.number_input(
                "Budget (USD)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
                help="Your travel budget",
            )
            preferences = st.multiselect(
                "Preferences",
                options=[
                    "Adventure",
                    "Culture",
                    "Food",
                    "Nature",
                    "Nightlife",
                    "Relaxation",
                    "Shopping",
                    "Sports",
                ],
                help="Select your travel preferences",
            )
        
        submitted = st.form_submit_button("Plan Trip", use_container_width=True)
        
        if submitted:
            if not destination:
                st.error("Please enter a destination")
            else:
                with st.spinner("Planning your trip..."):
                    try:
                        response = plan_trip_api(
                            api_url,
                            destination,
                            duration,
                            budget,
                            preferences,
                        )
                        if response:
                            display_trip_plan(response)
                    except Exception as e:
                        st.error(f"Error planning trip: {str(e)}")


def my_trips_tab(api_url: str):
    """My trips tab."""
    st.header("My Trips")
    
    if st.button("Refresh", use_container_width=True):
        st.rerun()
    
    # TODO: Implement trip listing
    st.info("Trip history will be displayed here once implemented.")


def about_tab():
    """About tab."""
    st.header("About Trip Planner")
    st.markdown(
        """
        ### Welcome to Trip Planner!
        
        This application uses LangGraph and AI to help you plan amazing trips.
        
        **Features:**
        - 🎯 AI-powered trip planning
        - 📅 Customizable itineraries
        - 💰 Budget management
        - 🎨 Preference-based recommendations
        
        **Technology Stack:**
        - LangGraph for AI workflows
        - FastAPI for backend APIs
        - Streamlit for user interface
        
        **Getting Started:**
        1. Enter your destination
        2. Set your trip duration and budget
        3. Select your preferences
        4. Get your personalized itinerary!
        """
    )


def plan_trip_api(
    api_url: str,
    destination: str,
    duration: Optional[int],
    budget: Optional[float],
    preferences: Optional[list],
) -> Optional[dict]:
    """
    Call the trip planning API.
    
    Args:
        api_url: Base API URL
        destination: Travel destination
        duration: Trip duration in days
        budget: Travel budget
        preferences: List of preferences
        
    Returns:
        Trip plan response or None
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{api_url}/trip/plan",
                json={
                    "destination": destination,
                    "duration": duration,
                    "budget": budget,
                    "preferences": preferences or [],
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {str(e)}")
        return None


def display_trip_plan(trip_plan: dict):
    """Display the trip plan in the UI."""
    st.success("Trip plan generated successfully!")
    
    st.subheader(f"📍 {trip_plan.get('destination', 'Unknown')}")
    
    if trip_plan.get("estimated_cost"):
        st.metric("Estimated Cost", f"${trip_plan['estimated_cost']:.2f}")
    
    st.divider()
    
    itinerary = trip_plan.get("itinerary", [])
    if itinerary:
        st.subheader("📅 Itinerary")
        for day_plan in itinerary:
            day_num = day_plan.get("day", 0)
            activities = day_plan.get("activities", [])
            
            with st.expander(f"Day {day_num}", expanded=True):
                for activity in activities:
                    time = activity.get("time", "")
                    activity_name = activity.get("activity", "")
                    st.markdown(f"**{time}** - {activity_name}")
    else:
        st.info("No itinerary generated yet.")


if __name__ == "__main__":
    main()
