# =========================================================
# Stage 1: Build TypeScript + React Frontend
# =========================================================
FROM node:22-slim AS frontend-builder
WORKDIR /frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source code and compile production assets
COPY frontend/ ./
RUN npm run build

# =========================================================
# Stage 2: Production Python Backend + Static UI
# =========================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Copy dependency specifications for layer caching
COPY pyproject.toml uv.lock* ./

# Install production dependencies using UV
RUN uv sync --no-dev --no-install-project

# Copy application backend source code
COPY src/ ./src/

# Copy compiled static React UI from Stage 1 into /app/static
COPY --from=frontend-builder /frontend/dist ./static/

# Place the virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose Cloud Run port
EXPOSE 8080

# Start FastAPI application (serves both API and React UI)
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]

