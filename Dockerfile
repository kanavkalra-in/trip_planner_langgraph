# Multi-stage Dockerfile for Trip Planner Application

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel first (cached layer)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install all external Python dependencies first
# This layer is cached separately and only invalidates when dependencies change
RUN pip install --no-cache-dir --no-warn-script-location \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    streamlit>=1.28.0 \
    langgraph>=0.0.40 \
    langchain>=0.1.0 \
    langchain-core>=0.1.0 \
    langchain-openai>=0.0.5 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-dotenv>=1.0.0 \
    httpx>=0.25.0

# Now copy source code (this layer invalidates on source changes,
# but Python dependencies are already installed and cached above)
COPY gen_ai_core_lib /build/gen_ai_core_lib
WORKDIR /build/gen_ai_core_lib
# Install in non-editable mode for production (better for multi-stage builds)
RUN pip install --no-cache-dir .

# Copy trip_planner_langgraph project files
WORKDIR /build
COPY trip_planner_langgraph/ ./trip_planner_langgraph/

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser trip_planner_langgraph/ .

# Add src to Python path (required for imports)
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run both services
CMD ["python", "-m", "src.main", "both"]
