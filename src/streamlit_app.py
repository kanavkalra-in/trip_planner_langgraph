"""Streamlit application for Trip Planner."""

import streamlit as st
import httpx
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os
from src.core.trip_planner_container import settings

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

# API base URL - from environment variable or default
API_BASE_URL = os.getenv(
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
    """Trip planning tab - pure chat interface."""
    st.header("💬 Trip Planning Chat")
    st.markdown("Start a conversation to plan your perfect trip!")
    
    # Initialize session state for chat and trip planning
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "Hi! I'm your trip planning assistant. Tell me about the trip you'd like to plan - where do you want to go, when, and for how long?"
        })
    if "accumulated_responses" not in st.session_state:
        st.session_state.accumulated_responses = {}
    if "current_trip_plan" not in st.session_state:
        st.session_state.current_trip_plan = None
    if "last_api_response" not in st.session_state:
        st.session_state.last_api_response = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None  # Store thread_id for resuming conversations
    if "feedback_sent" not in st.session_state:
        st.session_state.feedback_sent = False  # Track if feedback has been sent
    
    # Display chat history (always on top)
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                if message.get("is_loading"):
                    # Show loading message
                    st.markdown(message["content"])
                    # Show a spinner indicator
                    st.caption("⏳ Processing...")
                else:
                    st.markdown(message["content"])
    
    # Chat input - always available at the top
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # If there's already a trip plan, treat new input as updated_user_input (iteration)
        # This will override the existing itinerary
        if st.session_state.current_trip_plan:
            # Clear the existing plan to show it's being updated
            st.session_state.current_trip_plan = None
            st.session_state.feedback_sent = False
        
        # Add user message to chat
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Add temporary loading message
        loading_message = {
            "role": "assistant",
            "content": "🔄 Planning your trip and fetching details...",
            "is_loading": True
        }
        st.session_state.chat_messages.append(loading_message)
        st.session_state.is_processing = True
        
        # Rerun to show loading message
        st.rerun()
    
    # Process message if we have a loading message at the end
    if (st.session_state.get("is_processing", False) and 
        st.session_state.chat_messages and 
        st.session_state.chat_messages[-1].get("is_loading")):
        # Remove loading message
        st.session_state.chat_messages.pop()
        
        # Get the last user message
        user_message = None
        for msg in reversed(st.session_state.chat_messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
        
        if user_message:
            # Process the user input
            process_user_message(api_url, user_message)
        
        # Clear processing flag
        st.session_state.is_processing = False
        
        st.rerun()
    
    # Show current trip plan if available (below chat)
    if st.session_state.current_trip_plan:
        st.divider()
        display_trip_plan_with_feedback(api_url, st.session_state.current_trip_plan)
    
    # Add a button to start over
    if st.button("🔄 Start New Trip", use_container_width=True):
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": "Hi! I'm your trip planning assistant. Tell me about the trip you'd like to plan - where do you want to go, when, and for how long?"
        }]
        st.session_state.accumulated_responses = {}
        st.session_state.current_trip_plan = None
        st.session_state.last_api_response = None
        st.session_state.thread_id = None  # Clear thread_id for new trip
        st.session_state.feedback_sent = False
        st.rerun()


def process_user_message(api_url: str, user_input: str):
    """Process a user message in the chat and call the API."""
    # Determine if we're resuming (user providing responses to clarifying questions)
    # or if we have an existing plan (treat as iteration/updated input)
    is_resuming = (
        st.session_state.get("thread_id") is not None and
        st.session_state.get("pending_questions") is not None
    )
    
    # If we have an existing completed plan, treat new input as updated_user_input (iteration)
    has_existing_plan = (
        st.session_state.current_trip_plan is not None and
        st.session_state.current_trip_plan.get("status") == "completed"
    )
    
    if is_resuming:
        # Resuming: user is providing responses to clarifying questions
        # Map user input to the missing fields/questions
        accumulated = st.session_state.accumulated_responses.copy()
        # Store user input as response (you might want to parse this better)
        accumulated["last_input"] = user_input
        st.session_state.accumulated_responses = accumulated
        
        request_data = {
            "thread_id": st.session_state.thread_id,  # Include thread_id for resuming
            "user_responses": accumulated,  # User responses to clarifying questions
        }
    elif has_existing_plan:
        # User is providing additional instructions on top of existing plan
        # This will override the existing itinerary
        request_data = {
            "updated_user_input": user_input,  # Additional instructions
            "thread_id": st.session_state.thread_id,  # Include thread_id to continue same conversation
        }
    else:
        # New conversation or continuing
        accumulated = st.session_state.accumulated_responses.copy()
        accumulated["last_input"] = user_input
        st.session_state.accumulated_responses = accumulated
        
        request_data = {
            "user_input": user_input,  # Current user input
            "thread_id": st.session_state.thread_id,  # Include thread_id if available
        }
    
    # Call the API with loading indicator
    try:
        # The loading message is already shown in chat, but we can add additional feedback
        with st.spinner("🔄 Fetching trip details and planning your itinerary..."):
            response = plan_trip_api(
                api_url,
                user_input=request_data.get("user_input"),
                user_responses=request_data.get("user_responses"),
                thread_id=request_data.get("thread_id"),
                updated_user_input=request_data.get("updated_user_input"),
            )
        
        if response:
            # Store the response
            st.session_state.last_api_response = response
            
            # Store thread_id from response (for resuming conversations)
            if response.get("thread_id"):
                st.session_state.thread_id = response["thread_id"]
            
            # Handle the response
            status = response.get("status", "unknown")
            
            if status == "needs_clarification":
                # Store clarification state
                st.session_state.pending_questions = response.get("clarifying_questions", [])
                st.session_state.missing_info = response.get("missing_info", [])
                
                # Add assistant message with questions
                questions = response.get("clarifying_questions", [])
                if questions:
                    question_text = "I need a bit more information to plan your trip:\n\n"
                    for i, question in enumerate(questions, 1):
                        question_text += f"{i}. {question}\n"
                    question_text += "\nPlease provide the information above."
                    
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": question_text
                    })
                
                # Update accumulated responses with extracted requirements from API
                if response.get("extracted_requirements"):
                    extracted = response["extracted_requirements"]
                    # Store extracted requirements for context
                    for key, value in extracted.items():
                        if value is not None:
                            accumulated[key] = str(value) if not isinstance(value, (list, dict)) else value
                    st.session_state.accumulated_responses = accumulated
            
            elif status == "completed":
                # Store the trip plan (this will override any existing plan)
                st.session_state.current_trip_plan = response
                
                # Clear clarification state
                st.session_state.pending_questions = None
                st.session_state.missing_info = None
                # Keep thread_id even after completion (in case user wants to continue)
                st.session_state.feedback_sent = False  # Reset feedback flag for new plan
                
                # Add assistant message
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "Great! I've created your trip plan. Here are the details:"
                })
            
            elif status == "error":
                errors = response.get("errors", [])
                error_msg = "I encountered an error while planning your trip."
                if errors:
                    error_msg += f"\n\nErrors: {', '.join(errors)}"
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            
    except Exception as e:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"Sorry, I encountered an error: {str(e)}. Please try again."
        })


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
    user_input: Optional[str] = None,
    user_responses: Optional[dict] = None,
    thread_id: Optional[str] = None,
    updated_user_input: Optional[str] = None,
    thumbs_up: Optional[bool] = None,
    thumbs_down: Optional[bool] = None,
) -> Optional[dict]:
    """
    Call the trip planning API with thread_id support for resuming conversations.
    
    Args:
        api_url: Base API URL
        user_input: Natural language user input (required for new requests)
        user_responses: User responses to clarifying questions (for resuming)
        thread_id: Thread ID for resuming existing conversation
        updated_user_input: Additional user instructions for iteration
        thumbs_up: User thumbs up feedback
        thumbs_down: User thumbs down feedback
        
    Returns:
        Trip plan response or None
    """
    try:
        with httpx.Client(timeout=120.0) as client:  # Increased timeout for LangGraph processing
            request_data = {}
            
            # Include user_input if provided (for new requests)
            if user_input:
                request_data["user_input"] = user_input
            
            # Include user_responses if provided (for resuming)
            if user_responses:
                request_data["user_responses"] = user_responses
            
            # Include updated_user_input if provided (for iteration)
            if updated_user_input:
                request_data["updated_user_input"] = updated_user_input
            
            # Include feedback if provided
            if thumbs_up is not None:
                request_data["thumbs_up"] = thumbs_up
            
            if thumbs_down is not None:
                request_data["thumbs_down"] = thumbs_down
            
            # Include thread_id if provided (for resuming or continuing)
            if thread_id:
                request_data["thread_id"] = thread_id
            
            response = client.post(
                f"{api_url}/trip/plan",
                json=request_data,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {str(e)}")
        return None






def display_trip_plan_with_feedback(api_url: str, trip_plan: dict):
    """Display the trip plan in the UI with feedback buttons."""
    status = trip_plan.get("status", "unknown")
    
    # Show feedback buttons at the top if plan is completed and feedback not sent
    if status == "completed" and not st.session_state.get("feedback_sent", False):
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("👍 Thumbs Up", use_container_width=True, key="thumbs_up_btn"):
                send_feedback(api_url, thumbs_up=True)
        with col2:
            if st.button("👎 Thumbs Down", use_container_width=True, key="thumbs_down_btn"):
                send_feedback(api_url, thumbs_down=True)
    
    # Display the trip plan
    display_trip_plan(trip_plan)


def send_feedback(api_url: str, thumbs_up: bool = False, thumbs_down: bool = False):
    """Send feedback (thumbs up/down) to the API."""
    try:
        response = plan_trip_api(
            api_url,
            thread_id=st.session_state.get("thread_id"),
            thumbs_up=thumbs_up if thumbs_up else None,
            thumbs_down=thumbs_down if thumbs_down else None,
        )
        if response:
            st.session_state.feedback_sent = True
            # Show confirmation message in chat
            feedback_type = "👍" if thumbs_up else "👎"
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Thank you for your {feedback_type} feedback!"
            })
            st.rerun()
    except Exception as e:
        st.error(f"Error sending feedback: {str(e)}")


def display_trip_plan(trip_plan: dict):
    """Display the trip plan in the UI."""
    status = trip_plan.get("status", "unknown")
    
    # Handle different statuses
    if status == "needs_clarification":
        # This should be handled by handle_trip_plan_response, but keep as fallback
        st.warning("⚠️ Additional information needed to plan your trip")
        
        missing_info = trip_plan.get("missing_info", [])
        clarifying_questions = trip_plan.get("clarifying_questions", [])
        
        if missing_info:
            st.write("**Missing Information:**")
            for info in missing_info:
                st.write(f"• {info.replace('_', ' ').title()}")
        
        if clarifying_questions:
            st.subheader("Questions:")
            for i, question in enumerate(clarifying_questions, 1):
                st.write(f"{i}. {question}")
        
        # Show what we have so far
        if trip_plan.get("extracted_requirements"):
            with st.expander("📋 Extracted Information So Far", expanded=False):
                import json
                st.json(trip_plan["extracted_requirements"])
        
        return
    
    elif status == "error":
        st.error("❌ An error occurred while planning your trip")
        errors = trip_plan.get("errors", [])
        if errors:
            for error in errors:
                st.error(f"• {error}")
        return
    
    # Check if there are warnings (e.g., proceeding with missing info)
    errors = trip_plan.get("errors", [])
    if errors:
        for error in errors:
            if "Proceeding with partial information" in error:
                st.warning(f"⚠️ {error}")
            else:
                st.error(f"❌ {error}")
    
    elif status == "in_progress":
        st.info("Trip planning is in progress...")
        return
    
    # Status is "completed" - show the full plan
    st.success("Trip plan generated successfully!")
    
    destination = trip_plan.get("destination", "Unknown")
    st.subheader(f"📍 {destination}")
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        if trip_plan.get("estimated_cost"):
            st.metric("Estimated Cost", f"${trip_plan['estimated_cost']:,.2f}")
    with col2:
        if trip_plan.get("day_wise_plan"):
            st.metric("Trip Duration", f"{len(trip_plan['day_wise_plan'])} days")
    with col3:
        if trip_plan.get("attractions"):
            st.metric("Attractions", len(trip_plan["attractions"]))
    
    st.divider()
    
    # Show final plan if available (formatted text)
    if trip_plan.get("final_plan"):
        st.subheader("📋 Complete Trip Plan")
        st.markdown(trip_plan["final_plan"])
        st.divider()
    
    # Show itinerary/day-wise plan
    itinerary = trip_plan.get("itinerary") or trip_plan.get("day_wise_plan", [])
    if itinerary:
        st.subheader("📅 Day-by-Day Itinerary")
        for day_plan in itinerary:
            day_num = day_plan.get("day", 0)
            theme = day_plan.get("theme", "")
            date = day_plan.get("date", "")
            activities = day_plan.get("activities", [])
            
            day_title = f"Day {day_num}"
            if theme:
                day_title += f": {theme}"
            if date:
                day_title += f" ({date})"
            
            with st.expander(day_title, expanded=True):
                if activities:
                    for activity in activities:
                        time = activity.get("time", "")
                        activity_name = activity.get("activity", "")
                        location = activity.get("location", "")
                        duration = activity.get("duration_hours", "")
                        notes = activity.get("notes", "")
                        
                        activity_text = f"**{time}** - {activity_name}"
                        if location:
                            activity_text += f" @ {location}"
                        if duration:
                            activity_text += f" ({duration}h)"
                        
                        st.markdown(activity_text)
                        if notes:
                            st.caption(notes)
                else:
                    st.info("No activities scheduled for this day")
    else:
        st.info("No itinerary generated yet.")
    
    # Show attractions if available
    if trip_plan.get("attractions"):
        st.divider()
        st.subheader("🎯 Recommended Attractions")
        attractions = trip_plan["attractions"]
        for i, attr in enumerate(attractions[:10], 1):  # Show first 10
            with st.expander(f"{i}. {attr.get('name', 'Unknown')} ({attr.get('type', 'Unknown')})"):
                if attr.get("description"):
                    st.write(attr["description"])
                col1, col2 = st.columns(2)
                with col1:
                    if attr.get("estimated_time_hours"):
                        st.metric("Time", f"{attr['estimated_time_hours']} hours")
                with col2:
                    if attr.get("cost_estimate"):
                        st.metric("Cost", attr["cost_estimate"])
        
        if len(attractions) > 10:
            st.info(f"... and {len(attractions) - 10} more attractions")
    
    # Show extracted requirements for reference
    if trip_plan.get("extracted_requirements"):
        with st.expander("📝 Extracted Requirements"):
            import json
            st.json(trip_plan["extracted_requirements"])


if __name__ == "__main__":
    main()
