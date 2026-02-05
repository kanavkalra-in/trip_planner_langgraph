# Trip Planner LangGraph

A modern trip planning application built with LangGraph, FastAPI, and Streamlit.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Docker Deployment](#docker-deployment)
- [Code Structure](#code-structure)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Configuration](#configuration)
- [License](#license)
- [Contributing](#contributing)

## Features

- 🎯 AI-powered trip planning using LangGraph
- 🚀 FastAPI backend with RESTful APIs
- 🎨 Streamlit web interface
- 📦 Modern Python project structure with `pyproject.toml`
- 🔧 Type hints and modern Python practices
- 🐳 Docker support with docker-compose

## Project Structure

```
trip_planner_langgraph/
├── src/                      # Source code directory
│   ├── __init__.py
│   ├── main.py              # FastAPI application (main entry point)
│   ├── streamlit_app.py     # Streamlit web application
│   ├── api/                 # API layer
│   │   ├── __init__.py
│   │   └── routes.py        # API route definitions
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   └── config.py        # Configuration management
│   ├── agents/              # LangGraph agents (for future implementation)
│   │   └── __init__.py
│   └── utils/               # Utility functions (for future implementation)
│       └── __init__.py
├── tests/                   # Test files (for future implementation)
├── config/                  # Configuration files (optional)
├── pyproject.toml           # Project configuration and dependencies
├── Dockerfile               # Production Docker image
├── Dockerfile.dev           # Development Docker image
├── docker-compose.yml       # Production Docker Compose
├── docker-compose.dev.yml   # Development Docker Compose
├── run_api.py              # Helper script to run API
├── run_streamlit.py        # Helper script to run Streamlit
├── .dockerignore           # Docker ignore rules
├── .gitignore              # Git ignore rules
├── env.example             # Environment variables template
└── README.md               # This file
```

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone and navigate to project
git clone <repository-url>
cd trip_planner_langgraph

# 2. Create .env file
cp env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run with Docker Compose
docker-compose up --build
```

Access the application:
- FastAPI: http://localhost:8000
- Streamlit: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Using Python (Local Development)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Create .env file
cp env.example .env
# Edit .env and add your configuration

# 4. Run the application
python -m src.main
```

## Installation

### Prerequisites

- Python 3.10 or higher (for local development)
- pip or poetry
- Docker and Docker Compose (for containerized deployment)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd trip_planner_langgraph
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

For development dependencies:
```bash
pip install -e ".[dev]"
```

4. Create a `.env` file from the example:
```bash
cp env.example .env
# Edit .env and add your configuration
```

Example `.env` file:
```env
OPENAI_API_KEY=your_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
STREAMLIT_PORT=8501
```

## Usage

### Running Both Services Together (Recommended)

Run both FastAPI and Streamlit from a single command:

```bash
# Run both API and Streamlit (default)
python -m src.main

# Or explicitly specify "both"
python -m src.main both
```

This will start:
- FastAPI at `http://localhost:8000` (or configured port)
- Streamlit at `http://localhost:8501` (or configured port)

### Running Services Individually

#### FastAPI Only

```bash
# Using the main module
python -m src.main api

# Or using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### Streamlit Only

```bash
# Using the main module
python -m src.main streamlit

# Or using streamlit directly
streamlit run src/streamlit_app.py
```

The Streamlit app will be available at `http://localhost:8501`

## Docker Deployment

### Quick Start with Docker Compose

1. Create a `.env` file:
```bash
cp env.example .env
# Edit .env and add your OPENAI_API_KEY and other settings
```

2. Build and run with Docker Compose:
```bash
# Production mode
docker-compose up --build

# Development mode (with hot-reload and dev dependencies)
docker-compose -f docker-compose.dev.yml up --build
```

This will start both FastAPI and Streamlit services:
- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

3. Stop the services:
```bash
# Production
docker-compose down

# Development
docker-compose -f docker-compose.dev.yml down
```

### Development Mode

For development with hot-reload and mounted volumes:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

This uses `Dockerfile.dev` which includes:
- Development dependencies
- Source code mounted as volumes for live updates
- Hot-reload enabled for FastAPI

### Docker Commands

#### Build the Docker image:
```bash
docker build -t trip-planner:latest .
```

#### Run the container:
```bash
docker run -d \
  --name trip-planner \
  -p 8000:8000 \
  -p 8501:8501 \
  --env-file .env \
  trip-planner:latest
```

#### Run with custom command (API only):
```bash
docker run -d \
  --name trip-planner-api \
  -p 8000:8000 \
  --env-file .env \
  trip-planner:latest \
  python -m src.main api
```

#### Run with custom command (Streamlit only):
```bash
docker run -d \
  --name trip-planner-streamlit \
  -p 8501:8501 \
  --env-file .env \
  trip-planner:latest \
  python -m src.main streamlit
```

#### View logs:
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f trip-planner
```

#### Stop and remove container:
```bash
# Docker Compose
docker-compose down

# Docker
docker stop trip-planner && docker rm trip-planner
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Single service running both API and Streamlit (default)
- Environment variable support via `.env` file
- Health checks
- Automatic restart on failure
- Port mapping configuration

To run services separately, uncomment the alternative configuration in `docker-compose.yml`.

### API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/trip/plan` - Plan a new trip
- `GET /api/v1/trip/{trip_id}` - Get trip details
- `GET /api/v1/trip` - List all trips

### Example API Request

```bash
curl -X POST "http://localhost:8000/api/v1/trip/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris, France",
    "duration": 5,
    "budget": 2000.0,
    "preferences": ["Culture", "Food"]
  }'
```

## Code Structure

### Module Overview

- **`src/main.py`**: Main entry point for the application. Contains FastAPI app initialization and functions to run both API and Streamlit services.

- **`src/streamlit_app.py`**: Streamlit web interface for trip planning. Provides user-friendly UI to interact with the trip planning API.

- **`src/api/routes.py`**: FastAPI route definitions. Contains all API endpoints for trip planning operations.

- **`src/core/config.py`**: Configuration management using `pydantic-settings`. Handles environment variable loading and application settings.

- **`src/agents/`**: Reserved for LangGraph agents implementation (future).

- **`src/utils/`**: Reserved for utility functions and helpers (future).

### Architecture

The application follows a layered architecture:

```
┌─────────────────────────────────────┐
│      Streamlit UI (Frontend)        │
│      src/streamlit_app.py           │
└──────────────┬──────────────────────┘
               │ HTTP Requests
┌──────────────▼──────────────────────┐
│      FastAPI API (Backend)          │
│      src/main.py + src/api/routes.py │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Core Services                   │
│      src/core/config.py              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      LangGraph Agents (Future)       │
│      src/agents/                     │
└──────────────────────────────────────┘
```

## Development

### Code Formatting

```bash
black src/
ruff check src/
```

### Type Checking

```bash
mypy src/
```

### Running Tests

```bash
pytest
```

## Configuration

Configuration is managed through environment variables using `.env` file and `pydantic-settings`. The `.env` file is automatically loaded when you run the application.

**Important:** The `.env` file is gitignored for security. Copy `env.example` to `.env` and configure your settings:

```bash
cp env.example .env
```

Available environment variables:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Streamlit Configuration
STREAMLIT_PORT=8501

# OpenAI API Key (for LangGraph)
OPENAI_API_KEY=your_openai_api_key_here

# Database (optional, for future use)
# DATABASE_URL=sqlite:///./trip_planner.db
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
