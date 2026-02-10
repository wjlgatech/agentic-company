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

## 🚀 Agentic Teams & Workflows Gallery

Build powerful AI teams that work together. Here are ready-to-use examples to inspire your own implementations:

### 🏢 Business Teams

| Team | Description | Use Case |
|------|-------------|----------|
| **Sales Intelligence** | Lead researcher + Qualifier + Email Composer | Automated outreach with personalized messaging |
| **Customer Success** | Ticket Analyzer + Solution Finder + Response Writer | 24/7 support with escalation handling |
| **Market Research** | Trend Spotter + Competitor Analyst + Report Generator | Weekly market intelligence reports |
| **Financial Analyst** | Data Collector + Risk Assessor + Insight Summarizer | Investment due diligence automation |

### 🛠️ Technical Teams

| Team | Description | Use Case |
|------|-------------|----------|
| **Code Review Squad** | Security Scanner + Performance Analyzer + Documentation Checker | Automated PR reviews with actionable feedback |
| **DevOps Pipeline** | Deployer + Monitor + Incident Responder | Self-healing infrastructure management |
| **Data Engineering** | Ingester + Transformer + Quality Checker | ETL pipelines with data validation |
| **API Integration** | Connector Builder + Tester + Documentation Writer | Rapid third-party integrations |

### 🎨 Creative Teams

| Team | Description | Use Case |
|------|-------------|----------|
| **Content Studio** | Researcher + Writer + Editor + SEO Optimizer | Blog posts optimized for search and engagement |
| **Social Media Manager** | Trend Analyzer + Content Creator + Scheduler | Multi-platform content strategy |
| **Brand Voice** | Style Analyzer + Copy Writer + Consistency Checker | On-brand communications at scale |
| **Visual Designer** | Brief Interpreter + Asset Creator + Brand Validator | Design asset generation |

### 📋 Pre-Built Workflow Templates

```yaml
# Example: Content Research Pipeline
workflows:
  content-research:
    steps:
      - name: gather-sources
        agent: researcher
        guardrails: [rate_limit, content_filter]
      - name: analyze-data
        agent: analyst
        memory: persist
      - name: generate-insights
        agent: writer
        evaluator: quality_score > 0.8
      - name: human-review
        approval: required
        timeout: 24h
```

### 🧩 Reusable Skills Library

| Skill | Category | Description |
|-------|----------|-------------|
| `web-scraper` | Data | Intelligent web scraping with retry logic |
| `pdf-parser` | Data | Extract structured data from PDFs |
| `sentiment-analyzer` | NLP | Analyze tone and sentiment of text |
| `email-composer` | Communication | Generate professional emails |
| `code-generator` | Development | Generate code with best practices |
| `data-visualizer` | Analytics | Create charts and graphs |
| `meeting-summarizer` | Productivity | Extract action items from transcripts |
| `document-qa` | Knowledge | Answer questions from document collections |

### 💡 Quick Start Templates

<details>
<summary><b>🔍 Research Assistant (Click to expand)</b></summary>

```python
from orchestration import Pipeline, FunctionStep, ContentFilter, LocalMemoryStore

research_pipeline = Pipeline(
    name="research-assistant",
    guardrails=[ContentFilter(blocked_topics=["harmful"])],
    memory=LocalMemoryStore(),
)

research_pipeline.add_step(FunctionStep("search", search_web))
research_pipeline.add_step(FunctionStep("analyze", analyze_results))
research_pipeline.add_step(FunctionStep("summarize", create_summary))
```
</details>

<details>
<summary><b>📧 Email Automation (Click to expand)</b></summary>

```python
from orchestration import Pipeline, HumanApprovalGate

email_pipeline = Pipeline(
    name="email-automation",
    approval_gate=HumanApprovalGate(timeout_hours=4),
)

email_pipeline.add_step(FunctionStep("draft", compose_email))
email_pipeline.add_step(FunctionStep("personalize", add_personalization))
email_pipeline.add_step(FunctionStep("review", await_human_approval))
email_pipeline.add_step(FunctionStep("send", send_email))
```
</details>

<details>
<summary><b>📊 Data Processing (Click to expand)</b></summary>

```python
from orchestration import Pipeline, RuleBasedEvaluator

data_pipeline = Pipeline(
    name="data-processor",
    evaluator=RuleBasedEvaluator(min_quality=0.9),
)

data_pipeline.add_step(FunctionStep("ingest", load_data))
data_pipeline.add_step(FunctionStep("clean", clean_data))
data_pipeline.add_step(FunctionStep("transform", transform_data))
data_pipeline.add_step(FunctionStep("validate", validate_output))
```
</details>

### 🏗️ Build Your Own Team

```python
# Define your custom agentic team in minutes
from orchestration import Team, Agent, Pipeline

# Create specialized agents
researcher = Agent("researcher", skills=["web-search", "pdf-parser"])
analyst = Agent("analyst", skills=["data-analysis", "visualization"])
writer = Agent("writer", skills=["content-generation", "editing"])

# Assemble your team
my_team = Team(
    name="content-intelligence",
    agents=[researcher, analyst, writer],
    workflow="sequential",  # or "parallel", "hybrid"
    memory_shared=True,
)

# Run with full observability
result = await my_team.execute("Analyze competitor pricing strategies")
```

---

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
