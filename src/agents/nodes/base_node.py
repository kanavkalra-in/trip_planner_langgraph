"""Base node class for trip planner graph nodes."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.agents.trip_state import TripState
from gen_ai_core_lib.llm.llm_manager import LLMManager
from gen_ai_core_lib.config.logging_config import logger


class BaseNode(ABC):
    """Base class for all trip planner graph nodes."""
    
    def __init__(self, llm_manager: Optional[LLMManager] = None, node_name: str = ""):
        """
        Initialize the node.
        
        Args:
            llm_manager: Optional LLM manager instance for creating LLMs on-demand.
                       Nodes that need LLMs can use this to get LLM instances.
            node_name: Name of this node (for logging)
        """
        self.llm_manager = llm_manager
        self.node_name = node_name
    
    @abstractmethod
    def execute(self, state: TripState) -> Dict[str, Any]:
        """
        Execute the node logic.
        
        Args:
            state: Current trip state
            
        Returns:
            State updates (partial state dict)
        """
        pass
    
    def __call__(self, state: TripState) -> Dict[str, Any]:
        """Make node callable for LangGraph."""
        logger.info(f"Executing node: {self.node_name}")
        result = self.execute(state)
        logger.info(f"Node {self.node_name} completed successfully")
        return result
