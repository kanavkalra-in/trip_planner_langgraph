"""Configuration management."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

# Try to load .env file from multiple possible locations
# This works both locally and in Docker
env_paths = [
    Path.cwd() / ".env",  # Current working directory (Docker-friendly)
    Path(__file__).parent.parent.parent / ".env",  # Project root (local dev)
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override existing env vars
        break


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # Streamlit Settings
    streamlit_port: int = 8501
    
    # LangGraph/OpenAI Settings
    openai_api_key: Optional[str] = None
    
    # Serper API Settings (for flight search)
    serper_api_key: Optional[str] = None
    
    # Database Settings (for future use)
    database_url: Optional[str] = None
    
    # Pydantic v2 style configuration
    model_config = SettingsConfigDict(
        # Try to load from .env in current working directory, but don't fail if it doesn't exist
        # In Docker, env vars are passed directly via docker-compose, so .env file is optional
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Don't require .env file - environment variables can be set directly
        env_ignore_empty=True,
        # Ignore extra environment variables (e.g., langchain_tracing_v2 from LangChain/LangSmith)
        extra="ignore",
    )


# Instantiate settings - this will work even if .env doesn't exist
# because Pydantic Settings can read from environment variables directly
# In Docker, environment variables are passed via docker-compose, so .env is optional
settings = Settings()
