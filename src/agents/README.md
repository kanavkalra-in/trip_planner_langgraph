# LangGraph Trip Planner

A LangGraph-based trip planner with strict node responsibilities and deterministic planning.

## Architecture

The trip planner uses a StateGraph with the following nodes:

1. **extract_requirements**: Extracts structured requirements from user input (does not invent missing data)
2. **check_missing_info**: Identifies missing critical information
3. **ask_clarifying_questions**: Generates questions for missing information (loops back to check_missing_info)
4. **identify_attractions**: Identifies relevant attractions based on requirements
5. **create_itinerary_outline**: Creates high-level itinerary structure
6. **generate_day_wise_plan**: Generates detailed day-by-day plan with times
7. **optimize_itinerary**: Optimizes itinerary for efficiency
8. **format_final_plan**: Formats final plan for output

## Usage

### Basic Usage

```python
from gen_ai_core_lib.dependencies.application_container import ApplicationContainer
from src.agents import TripPlannerGraph

# Initialize
container = ApplicationContainer()
llm_manager = container.get_llm_manager()
planner = TripPlannerGraph(llm_manager, model_name="gpt-4o")

# Run planner
initial_state = {
    "user_input": "I want to visit Paris for 5 days from June 15-20, 2024. Budget is $2000."
}
final_state = planner.run(initial_state)

# Get final plan
print(final_state["final_plan"])
```

### Handling Clarifications

When the planner needs more information, it will set `clarifying_questions` in the state. You need to collect user responses and re-run:

```python
# First run - may have missing info
state = planner.run({"user_input": "I want to plan a trip"})

if state.get("clarifying_questions"):
    # Collect user responses
    responses = {}
    for question in state["clarifying_questions"]:
        answer = input(f"{question}: ")
        # Map question to field name
        if "destination" in question.lower():
            responses["destination"] = answer
        # ... map other questions
    
    # Re-run with responses
    state = planner.run({
        "user_input": state["user_input"],
        "user_responses": responses
    })
```

### Using via API

The trip planner is integrated into the FastAPI application. You can use it via:

1. **REST API**: Make POST requests to `/api/v1/trip/plan`
2. **Streamlit UI**: Run the Streamlit app for an interactive interface

```bash
# Start the API server
python run_api.py

# Or start both API and Streamlit
python -m src.main both
```

The API accepts both natural language input (`user_input`) and structured parameters (destination, duration, budget, etc.). It returns a response that may include:
- `final_plan`: Complete formatted trip plan (when status is "completed")
- `clarifying_questions`: Questions when information is missing (when status is "needs_clarification")
- `itinerary` or `day_wise_plan`: Structured itinerary data
- `attractions`: List of recommended attractions

## State Structure

The `TripState` TypedDict includes:
- User input fields (destination, duration, budget, etc.)
- Extracted requirements
- Missing information tracking
- Clarifying questions and user responses
- Attractions list
- Itinerary outline
- Day-wise plan
- Optimized itinerary
- Final formatted plan

See `trip_state.py` for the complete definition.

## Key Features

- **No data invention**: Nodes only use provided information
- **Clarification loop**: Automatically loops back when information is missing
- **Deterministic planning**: Planning nodes produce consistent results
- **Strict responsibilities**: Each node has a single, well-defined purpose
