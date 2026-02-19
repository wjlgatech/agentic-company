# Agentic Company Installation & Setup Guide

Complete guide for installing and running the Agentic Company AI Orchestration System.

## Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Verification & Health Checks](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/wjlgatech/agentic.git
cd agentic
pip install -e ".[dev]"

# Set API keys
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"  # optional

# Verify installation
agentic health

# Start the API server
agentic serve --port 8000

# Or use Docker (recommended for production)
docker-compose up -d
```

---

## Prerequisites

### Required

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python --version` |
| pip | 21.0+ | `pip --version` |
| Git | 2.0+ | `git --version` |

### Optional (for full features)

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker | 20.0+ | Containerized deployment |
| Docker Compose | 2.0+ | Multi-service orchestration |
| Node.js | 18+ | Web UI development |
| Redis | 7.0+ | Caching & task queue |
| PostgreSQL | 14+ | Production database |

### API Keys Required

```bash
# Required - Main LLM provider
ANTHROPIC_API_KEY=sk-ant-...

# Optional - Alternative providers
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## Installation Methods

### Method 1: pip install (Simplest)

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install from PyPI (when published)
pip install agentic

# Or install from source
pip install -e ".[dev]"
```

### Method 2: Docker (Recommended for Production)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t agentic:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY agentic:latest
```

### Method 3: Development Setup

```bash
# Clone repository
git clone https://github.com/wjlgatech/agentic.git
cd agentic

# Install with all development dependencies
pip install -e ".[dev,supabase,anthropic,openai]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify
pytest -v
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
# ===================
# Required
# ===================
ANTHROPIC_API_KEY=sk-ant-your-key-here

# ===================
# Optional - LLM Providers
# ===================
OPENAI_API_KEY=sk-your-key-here
DEFAULT_LLM_PROVIDER=anthropic  # or openai

# ===================
# Optional - Database
# ===================
DATABASE_URL=postgresql://user:pass@localhost:5432/agentic
REDIS_URL=redis://localhost:6379/0

# ===================
# Optional - Supabase
# ===================
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# ===================
# Optional - Server
# ===================
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO
DEBUG=false

# ===================
# Optional - Observability
# ===================
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Configuration File (Alternative)

Create `config/settings.yaml`:

```yaml
# config/settings.yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  debug: false

llm:
  default_provider: anthropic
  anthropic:
    model: claude-sonnet-4-20250514
    max_tokens: 4096
  openai:
    model: gpt-4
    max_tokens: 4096

guardrails:
  enabled: true
  content_filter:
    enabled: true
    blocked_topics: ["harmful", "illegal"]
  rate_limit:
    enabled: true
    max_requests_per_minute: 60

memory:
  backend: local  # or supabase, redis
  max_entries: 1000

observability:
  tracing_enabled: true
  metrics_enabled: true
  log_level: INFO
```

### Validate Configuration

```bash
# Check configuration is valid
agentic config validate

# Show current configuration
agentic config show
```

---

## Running the Application

### CLI Mode

```bash
# Check system health
agentic health

# Run a workflow
agentic workflow run content-research --input "AI trends 2024"

# List available workflows
agentic workflow list

# Check workflow status
agentic workflow status <workflow-id>

# View metrics
agentic metrics show
```

### API Server Mode

```bash
# Start development server
agentic serve --port 8000 --reload

# Start production server
agentic serve --port 8000 --workers 4

# Or use uvicorn directly
uvicorn orchestration.api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Mode

```bash
# Start all services (API + Redis + Prometheus + Grafana)
docker-compose up -d

# Start with monitoring stack
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f orchestration

# Stop all services
docker-compose down
```

### Makefile Commands

```bash
make install      # Install dependencies
make dev          # Install dev dependencies
make test         # Run tests
make lint         # Run linters
make format       # Format code
make serve        # Start API server
make docker-build # Build Docker image
make docker-up    # Start Docker services
make clean        # Clean build artifacts
```

---

## Verification

### Health Checks

```bash
# CLI health check
agentic health

# Expected output:
# ✅ System Health: OK
# ├── LLM Connection: OK (anthropic)
# ├── Memory Backend: OK (local)
# ├── Guardrails: OK (3 active)
# └── API Server: OK (port 8000)
```

### API Health Endpoints

```bash
# General health
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "0.1.0", ...}

# Kubernetes liveness probe
curl http://localhost:8000/live
# Response: {"status": "alive"}

# Kubernetes readiness probe
curl http://localhost:8000/ready
# Response: {"status": "ready", "checks": {...}}
```

### Run Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=orchestration --cov-report=html

# Run specific test categories
pytest tests/test_guardrails.py -v
pytest tests/test_api.py -v
pytest tests/test_real_user.py -v

# Run stress tests
pytest tests/test_stress.py -v --timeout=300
```

---

## Troubleshooting

### Common Issues

#### 1. "ANTHROPIC_API_KEY not set"

```bash
# Solution: Set the environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key"

# Or add to .env file
echo 'ANTHROPIC_API_KEY=sk-ant-your-key' >> .env
```

#### 2. "Port 8000 already in use"

```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
agentic serve --port 8001
```

#### 3. "Module not found: orchestration"

```bash
# Reinstall in development mode
pip install -e .

# Verify installation
pip show agentic
```

#### 4. Docker build fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### 5. Tests failing

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run with verbose output
pytest -v --tb=long

# Check for missing dependencies
pip check
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with debug output
agentic --verbose health
```

### Logs Location

| Component | Log Location |
|-----------|--------------|
| CLI | `~/.agentic/logs/cli.log` |
| API Server | `./logs/api.log` |
| Docker | `docker-compose logs` |
| Celery Workers | `./logs/celery.log` |

---

## Production Deployment

### Docker Production

```bash
# Build production image
docker build -t agentic:prod --target runtime .

# Run with production settings
docker run -d \
  --name agentic \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e LOG_LEVEL=WARNING \
  -e WORKERS=4 \
  --restart unless-stopped \
  agentic:prod
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic
  template:
    metadata:
      labels:
        app: agentic
    spec:
      containers:
      - name: agentic
        image: agentic:prod
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: anthropic-api-key
        livenessProbe:
          httpGet:
            path: /live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### System Requirements (Production)

| Users | CPU | RAM | Storage |
|-------|-----|-----|---------|
| 1-10 | 2 cores | 2GB | 10GB |
| 10-100 | 4 cores | 4GB | 50GB |
| 100-1000 | 8 cores | 8GB | 100GB |
| 1000+ | 16+ cores | 16GB+ | 500GB+ |

### Monitoring Setup

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

---

## Support

- **Documentation**: https://agentic.dev/docs
- **Issues**: https://github.com/wjlgatech/agentic/issues
- **Discord**: https://discord.gg/agentic

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2024-01 | Initial release |
| 0.2.0 | 2024-02 | Web UI, improved CLI |
| 0.3.0 | 2024-03 | Scalability, PostgreSQL |
| 1.0.0 | 2024-04 | Production ready |
