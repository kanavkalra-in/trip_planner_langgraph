"""Prompts for trip planner nodes."""

from .extract_requirements_prompts import EXTRACT_REQUIREMENTS_PROMPT
from .identify_attractions_and_plan_prompts import IDENTIFY_ATTRACTIONS_AND_GENERATE_PLAN_PROMPT
from .optimize_plan_prompts import OPTIMIZE_AND_FORMAT_PLAN_PROMPT

__all__ = [
    "EXTRACT_REQUIREMENTS_PROMPT",
    "IDENTIFY_ATTRACTIONS_AND_GENERATE_PLAN_PROMPT",
    "OPTIMIZE_AND_FORMAT_PLAN_PROMPT",
]
