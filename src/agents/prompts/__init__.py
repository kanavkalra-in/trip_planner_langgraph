"""Prompts for trip planner nodes."""

from .extract_requirements_prompts import EXTRACT_REQUIREMENTS_PROMPT
from .identify_attractions_prompts import IDENTIFY_ATTRACTIONS_PROMPT
from .generate_plan_prompts import GENERATE_DAY_WISE_PLAN_PROMPT
from .optimize_plan_prompts import OPTIMIZE_AND_FORMAT_PLAN_PROMPT

__all__ = [
    "EXTRACT_REQUIREMENTS_PROMPT",
    "IDENTIFY_ATTRACTIONS_PROMPT",
    "GENERATE_DAY_WISE_PLAN_PROMPT",
    "OPTIMIZE_AND_FORMAT_PLAN_PROMPT",
]
