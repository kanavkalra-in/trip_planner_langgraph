"""JSON parsing utilities for LLM responses."""
import json
from typing import Any


def parse_json_response(response: Any) -> Any:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    
    Args:
        response: LLM response object
        
    Returns:
        Parsed JSON object
        
    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    content = response.content if hasattr(response, 'content') else str(response)
    content = content.strip()
    
    # Remove markdown code blocks
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    return json.loads(content)
