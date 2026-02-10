# Agentic Company - AI Agent Orchestration System

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/wjlgatech/agentic-company)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive framework for building production-ready AI agent workflows with guardrails, memory, observability, and approval gates.

## Features

- **Guardrails**: Content filtering, PII detection, rate limiting
- **Memory System**: Local, Redis, and PostgreSQL backends
- **Evaluator-Optimizer**: Rule-based and LLM evaluation with optimization loops
- **Approval Gates**: Human-in-the-loop workflows with auto/manual/hybrid modes
- **Observability**: Metrics, tracing, structured logging, OpenTelemetry integration
- **Pipeline Orchestration**: Multi-step workflow composition
- **CLI & API**: Full-featured command line and REST API
- **Web Dashboard**: React-based monitoring and management UI
- **Scalability**: Celery task queue, PostgreSQL persistence

## Quick Start

```bash
# Install
pip install agentic-company

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Check health
agentic health

# Start API server
agentic serve

# Or use Docker
docker-compose up -d
```

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | Installation and setup guide |
| [docs/API.md](docs/API.md) | API reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Agentic Company                              │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │    CLI      │  │   REST API  │  │  Dashboard  │   Interfaces │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Pipeline   │  │  Guardrails │  │  Evaluator  │   Core       │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Memory    │  │  Approval   │  │ Observability│             │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Redis     │  │ PostgreSQL  │  │   Celery    │  Infrastructure
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

## Usage Examples

### CLI

```bash
# Check system health
agentic health

# Run a workflow
agentic workflow run content-research --input "AI trends 2024"

# Search memory
agentic recall "machine learning"

# View metrics
agentic metrics show
```

### Python API

```python
from orchestration import (
    Pipeline, PipelineConfig, FunctionStep,
    GuardrailPipeline, ContentFilter, RateLimiter,
    RuleBasedEvaluator, LocalMemoryStore
)

# Create guardrails
guardrails = GuardrailPipeline([
    ContentFilter(blocked_topics=["harmful"]),
    RateLimiter(max_requests=60),
])

# Create pipeline
pipeline = Pipeline(
    config=PipelineConfig(name="content-processor"),
    guardrails=guardrails,
    evaluator=RuleBasedEvaluator(min_length=100),
    memory=LocalMemoryStore(),
)

# Add steps
pipeline.add_step(FunctionStep("process", lambda x, ctx: f"Processed: {x}"))

# Run
import asyncio
result, steps = asyncio.run(pipeline.run("Hello world"))
```

### REST API

```bash
# Run workflow
curl -X POST http://localhost:8000/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "research", "input_data": "AI trends"}'

# Search memory
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "limit": 10}'

# Get metrics
curl http://localhost:8000/metrics
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
LLM_PROVIDER=anthropic
MEMORY_BACKEND=local
LOG_LEVEL=INFO
PORT=8000
```

Or use `config/settings.yaml`:

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514

guardrails:
  enabled: true
  rate_limit_enabled: true

memory:
  backend: local
  max_entries: 1000
```

## Development

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Start dev server
make serve
```

## Docker

```bash
# Start all services
docker-compose up -d

# With monitoring
docker-compose --profile monitoring up -d

# With PostgreSQL
docker-compose --profile postgres up -d

# Full stack
docker-compose --profile monitoring --profile postgres --profile celery up -d
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=orchestration

# Run stress tests
pytest tests/test_stress.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: https://github.com/wjlgatech/agentic-company/issues
- **Discussions**: https://github.com/wjlgatech/agentic-company/discussions
