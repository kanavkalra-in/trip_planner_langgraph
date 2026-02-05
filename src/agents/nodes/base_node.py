"""Base node class for trip planner graph nodes."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_core.language_models import BaseChatModel

from src.agents.trip_state import TripState
from gen_ai_core_lib.config.logging_config import logger


class BaseNode(ABC):
    """Base class for all trip planner graph nodes."""
    
    def __init__(self, llm: BaseChatModel, node_name: str):
        """
        Initialize the node.
        
        Args:
            llm: Language model instance
            node_name: Name of this node (for logging)
        """
        self.llm = llm
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
        try:
            result = self.execute(state)
            logger.info(f"Node {self.node_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in node {self.node_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "current_step": self.node_name,
                "errors": [f"Error in {self.node_name}: {str(e)}"]
            }
