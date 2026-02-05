# Running the Project Without Docker

## Quick Start

### 1. Create/Activate Virtual Environment

**Quick Setup (Recommended):**

Use the provided setup script:
```bash
./setup_venv.sh
```

This script will:
- Remove the old virtual environment (if it exists)
- Create a new one with Python 3.12
- Upgrade pip, setuptools, and wheel
- Verify the Python version

**Manual Setup:**

If you prefer to do it manually or the script doesn't work:

```bash
# Remove old venv if it exists and uses Python < 3.10
rm -rf .venv

# Create new virtual environment with Python 3.12 (or 3.10+)
# Option A: If you have python3.12 in PATH
python3.12 -m venv .venv

# Option B: If you have Anaconda Python 3.12
/opt/anaconda3/bin/python3.12 -m venv .venv

# Option C: Use pyenv if installed
pyenv install 3.12.7  # if not already installed
pyenv local 3.12.7
python -m venv .venv
```

**Activate the virtual environment:**

```bash
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify Python version (should be 3.10+)
python --version
```

### 2. Install Dependencies

**Upgrade pip and setuptools first** (required for editable installs with pyproject.toml):
```bash
pip install --upgrade pip setuptools wheel
```

**Install the local dependency first** (gen_ai_core_lib):
```bash
cd /Users/kanavkalra/Data/genAI/projects/gen_ai_core_lib
pip install -e .
cd /Users/kanavkalra/Data/genAI/projects/trip_planner_langgraph
```

**Install the project and all dependencies from pyproject.toml**:
```bash
pip install -e .
```

For development dependencies:
```bash
pip install -e ".[dev]"
```

**Note**: All dependencies are defined in `pyproject.toml`. The project uses the modern Python packaging standard and doesn't require a separate `requirements.txt` file.

### 3. Configure Environment Variables

Make sure your `.env` file exists and contains:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_BASE_URL=http://localhost:8000/api/v1

# Streamlit Configuration
STREAMLIT_PORT=8501

# OpenAI API Key (required for LangGraph)
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the Application

#### Option A: Run Both Services (API + Streamlit) - Recommended

```bash
python -m src.main
# or
python -m src.main both
```

This will start:
- **FastAPI** at `http://localhost:8000`
- **Streamlit** at `http://localhost:8501`

#### Option B: Run API Only

```bash
python -m src.main api
# or
python run_api.py
# or
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at: `http://localhost:8000/docs`

#### Option C: Run Streamlit Only

```bash
python -m src.main streamlit
# or
python run_streamlit.py
# or
streamlit run src/streamlit_app.py
```

Access Streamlit at: `http://localhost:8501`

## Troubleshooting

### Python Version
- **Required**: Python 3.10 or higher
- Check your version: `python --version` (after activating venv)
- **Error: "requires a different Python: 3.9.6 not in '>=3.10'"**
  - Your virtual environment was created with Python 3.9.6
  - Solution: Recreate the virtual environment with Python 3.10+:
    ```bash
    # Deactivate current venv
    deactivate
    
    # Remove old venv
    rm -rf .venv
    
    # Create new venv with Python 3.12 (or 3.10+)
    /opt/anaconda3/bin/python3.12 -m venv .venv
    # OR: python3.12 -m venv .venv  (if in PATH)
    # OR: python3.11 -m venv .venv  (if available)
    
    # Activate and verify
    source .venv/bin/activate
    python --version  # Should show 3.10+
    
    # Now install dependencies
    pip install --upgrade pip setuptools wheel
    ```

### Missing Dependencies
If you get import errors:
```bash
pip install -e ".[dev]"  # Install with dev dependencies
```

### Local Dependency (gen_ai_core_lib)
The project depends on a local package. Make sure:
1. The `gen_ai_core_lib` project exists at the path specified in `pyproject.toml`
2. Install it first:
   ```bash
   cd /Users/kanavkalra/Data/genAI/projects/gen_ai_core_lib
   pip install -e .
   cd /Users/kanavkalra/Data/genAI/projects/trip_planner_langgraph
   pip install -e .
   ```

### Port Already in Use
If ports 8000 or 8501 are already in use:
- Change `API_PORT` and `STREAMLIT_PORT` in your `.env` file
- Or stop the service using those ports

## Development Commands

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/

# Run tests
pytest
```
