"""FastAPI main application with support for running both API and Streamlit."""

import sys
import threading
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to allow imports when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load .env file before importing other modules
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.core.config import settings
from gen_ai_core_lib.dependencies.application_container import ApplicationContainer
from gen_ai_core_lib.config.logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app startup and shutdown."""
    # Startup: Initialize application container
    logger.info("Initializing application container...")
    container = ApplicationContainer()
    app.state.container = container
    logger.info("Application container initialized and stored in app state")
    
    yield
    
    # Shutdown: Cleanup (if needed)
    logger.info("Shutting down application...")


app = FastAPI(
    title="Trip Planner API",
    description="API for Trip Planner application with LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["trip-planner"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Trip Planner API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI application."""
    import uvicorn
    uvicorn.run("src.main:app", host=host, port=port, reload=reload)


def run_streamlit():
    """Run the Streamlit application."""
    streamlit_app = Path(__file__).parent / "streamlit_app.py"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(streamlit_app),
            "--server.port",
            str(settings.streamlit_port),
        ]
    )


def run_both():
    """Run both FastAPI and Streamlit applications."""
    print("Starting Trip Planner services...")
    print(f"FastAPI will run on http://{settings.api_host}:{settings.api_port}")
    print(f"Streamlit will run on http://localhost:{settings.streamlit_port}")
    print("Press Ctrl+C to stop both services\n")
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Run FastAPI in the main thread
    try:
        run_api(
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_reload,
        )
    except KeyboardInterrupt:
        print("\nShutting down services...")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "api":
            run_api(
                host=settings.api_host,
                port=settings.api_port,
                reload=settings.api_reload,
            )
        elif mode == "streamlit":
            run_streamlit()
        elif mode == "both":
            run_both()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python -m src.main [api|streamlit|both]")
            print("Default: runs both services")
            sys.exit(1)
    else:
        # Default: run both services
        run_both()
