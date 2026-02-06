"""Dependencies for API routes."""

from typing import Annotated

from fastapi import Depends

from gen_ai_core_lib.dependencies.application_container import ApplicationContainer
from gen_ai_core_lib.dependencies.llm_dependencies import get_container
from src.agents.trip_planner_graph import TripPlannerGraph
from src.services.container import TripPlannerContainer


# Global container instance (initialized once)
_container: TripPlannerContainer | None = None


def get_trip_planner(
    app_container: Annotated[ApplicationContainer, Depends(get_container)]
) -> TripPlannerGraph:
    """
    Get the TripPlannerGraph instance via dependency injection.
    
    The container is initialized once with the LLM manager.
    The graph is a singleton and can be safely reused across requests.
    
    Args:
        app_container: Application container with LLM manager
        
    Returns:
        TripPlannerGraph instance (singleton)
    """
    global _container
    
    if _container is None:
        _container = TripPlannerContainer()
        _container.llm_manager.override(app_container.get_llm_manager())
    
    return _container.planner()
