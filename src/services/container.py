"""
Dependency Injection Container for Trip Planner.

Uses dependency-injector library for proper dependency injection.
Manages the lifecycle of TripPlannerGraph and its dependencies.
"""

from dependency_injector import containers, providers
from langgraph.checkpoint.memory import MemorySaver

from src.agents.trip_planner_graph import TripPlannerGraph


class TripPlannerContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for Trip Planner.
    
    Manages singleton instances of:
    - Checkpointer (shared across all requests)
    - TripPlannerGraph (created lazily on first use)
    """
    
    # Checkpointer (singleton, shared across requests)
    checkpointer = providers.Singleton(MemorySaver)
    
    # TripPlannerGraph (singleton, lazy initialization)
    planner = providers.Singleton(
        TripPlannerGraph,
        checkpointer=checkpointer,
    )
