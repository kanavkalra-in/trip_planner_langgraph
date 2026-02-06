#!/usr/bin/env python3
"""Script to run the FastAPI server."""

import uvicorn
from src.core.trip_planner_container import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
