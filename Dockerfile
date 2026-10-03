# Use official Astral UV image with Python 3.12 for blazingly fast builds
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Prevent python from buffering stdout/stderr and writing bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Copy dependency specifications first for Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install production dependencies only using UV
RUN uv sync --no-dev --no-install-project

# Copy application source code
COPY src/ ./src/

# Place the virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose standard Cloud Run container port
EXPOSE 8080

# Start FastAPI application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
