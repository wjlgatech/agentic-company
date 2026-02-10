# Agentic Company Dockerfile
# Multi-stage build for optimized production image

# ============== Builder Stage ==============
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir build wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels .

# ============== Runtime Stage ==============
FROM python:3.11-slim as runtime

# Security: Create non-root user
RUN groupadd -r agentic && useradd -r -g agentic agentic

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY orchestration/ ./orchestration/
COPY pyproject.toml ./

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /app/logs /app/data && \
    chown -R agentic:agentic /app

# Switch to non-root user
USER agentic

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/live || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "orchestration.api:app", "--host", "0.0.0.0", "--port", "8000"]

# ============== Development Stage ==============
FROM runtime as development

USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov pytest-asyncio black ruff mypy

USER agentic

# Override command for development
CMD ["python", "-m", "uvicorn", "orchestration.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
