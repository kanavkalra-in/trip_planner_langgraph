"""
Dependency Injection Container for Trip Planner.

Uses dependency-injector library for proper dependency injection.
Manages the lifecycle of TripPlannerGraph and its dependencies.
"""

from dependency_injector import containers, providers
from langgraph.checkpoint.memory import MemorySaver

from gen_ai_core_lib.llm.llm_manager import LLMManager
from src.agents.trip_planner_graph import TripPlannerGraph


class TripPlannerContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for Trip Planner.
    
    Manages singleton instances of:
    - Checkpointer (shared across all requests)
    - TripPlannerGraph (created lazily on first use)
    """
    
    # Configuration
    config = providers.Configuration()
    config.model_name.from_value("gpt-4o")
    
    # LLM Manager (injected from ApplicationContainer)
    llm_manager = providers.Dependency(instance_of=LLMManager)
    
    # Checkpointer (singleton, shared across requests)
    checkpointer = providers.Singleton(MemorySaver)
    
    # TripPlannerGraph (singleton, lazy initialization)
    planner = providers.Singleton(
        TripPlannerGraph,
        llm_manager=llm_manager,
        model_name=config.model_name,
        checkpointer=checkpointer,
    )
