# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agenticom is a Python framework for orchestrating multi-agent AI teams. Agents (planner, developer, verifier, tester, reviewer) collaborate through YAML-defined workflows with production safety features: guardrails, memory, approval gates, and observability.

**13 Bundled Workflow YAMLs** (`agenticom/bundled_workflows/`): `feature-dev`, `feature-dev-with-diagnostics`, `feature-dev-with-loopback`, `feature-dev-llm-recovery`, `autonomous-dev-loop`, `marketing-campaign`, `due-diligence`, `compliance-audit`, `patent-landscape`, `security-assessment`, `churn-analysis`, `grant-proposal`, `incident-postmortem`.

## Common Commands

```bash
# Setup (auto-creates .venv)
make install              # pip install -e .
make dev                  # Install with dev + anthropic + openai deps

# Testing
make test                 # pytest tests/ -v
make test-cov             # Tests with HTML coverage report
make test-unit            # Skip integration-marked tests
make test-integration     # Only integration-marked tests
make test-stress          # Stress tests (timeout 300s)
pytest tests/test_agents.py -v              # Single test file
pytest tests/test_agents.py::TestName -v    # Single test class/function

# Code Quality
make lint                 # ruff check + mypy
make format               # black + ruff --fix

# Dev Server
make serve                # uvicorn orchestration.api:app on port 8000 with reload

# CLI
agenticom workflow list
agenticom workflow run <id> "<task description>"
agenticom workflow inspect <id>            # Show step inputs/outputs
agenticom workflow status <run-id>
agenticom workflow resume <run-id>
agenticom dashboard                        # Open web UI

# Database (Alembic)
make db-migrate           # alembic upgrade head
make db-rollback          # alembic downgrade -1

# Docker
make docker-up            # docker-compose up -d (core services)
make full-stack           # monitoring + postgres + celery profiles
```

## Configuration & Environment Variables

Config is loaded from `config/settings.yaml` if it exists, otherwise from environment. Key variables:

```bash
# LLM Provider (pick one)
ANTHROPIC_API_KEY=sk-ant-...      # For OpenClaw/Claude (default provider)
OPENAI_API_KEY=sk-...             # For Nanobot/GPT
LLM_PROVIDER=anthropic            # anthropic | openai | ollama
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7

# Memory Backend
MEMORY_BACKEND=local              # local | redis | postgres | supabase
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Server
PORT=8000
HOST=0.0.0.0
DEBUG=false

# Observability
LOG_LEVEL=INFO
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Celery (optional async task queue)
CELERY_ENABLED=false
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Architecture

### Core packages

- **`orchestration/`** — Framework core. All major subsystems are modules here.
- **`agenticom/`** — CLI entry point and bundled workflow YAML files.
- **`frontend/`** — React + Vite + TypeScript web dashboard (Zustand, TanStack Query, Tailwind).

### Execution flow

1. **YAML workflow** defines agents (with roles/prompts) and steps (with template inputs)
2. **`WorkflowParser`** (`orchestration/workflows/parser.py`) converts YAML → `AgentTeam` with `WorkflowStep` list
3. **`AgentTeam`** (`orchestration/agents/team.py`) executes steps sequentially; each step gets fresh context ("Ralph Loop" pattern to prevent hallucination)
4. **Template substitution**: `{{task}}` injects user input, `{{step_outputs.step_id}}` passes previous step results
5. **LLM execution**: `UnifiedExecutor` (`orchestration/integrations/unified.py`) routes to OpenClaw (Anthropic), Nanobot (OpenAI), or Ollama (local); `auto_setup_executor()` picks the best available backend

### Key subsystems (all under `orchestration/`)

| Module | Purpose |
|---|---|
| `agents/` | Base agent, specialized agents (Planner/Developer/Verifier/Tester/Reviewer), AgentTeam orchestration, TeamBuilder fluent API |
| `workflows/` | YAML parser, template substitution engine |
| `integrations/` | LLM backends: OpenClaw (`openclaw.py`), Nanobot (`nanobot.py`), Ollama (`ollama.py`), unified router |
| `tools/` | MCP bridge, tool registry, PromptEngineer, IntentRefiner (PIR), ConversationalRefiner, SmartRefiner (multi-turn interview → coherent prompt synthesis), HybridRefiner |
| `diagnostics/` | Automated diagnostics: `capture.py` (browser/console), `meta_analyzer.py` (LLM-based root cause), `criteria_builder.py`, `iteration_monitor.py`, `integration.py` |
| `guardrails.py` | Composable pipeline: content filter, PII detection, rate limiting |
| `memory.py` | Local/Redis/PostgreSQL/Supabase memory backends |
| `approval.py` | Auto/Human/Hybrid approval gates |
| `pipeline.py` | Generic step-by-step execution engine |
| `evaluator.py` | Rule-based + LLM-based quality evaluation (`EvaluationResult` with score 0–1) |
| `artifact_manager.py` / `artifacts.py` | Artifact collection and lifecycle management |
| `observability.py` | Prometheus metrics, structlog, distributed tracing |
| `lessons.py` | Lesson/pattern capture from past runs |
| `security.py` | Security controls |
| `api.py` | FastAPI REST API |
| `database.py` | SQLAlchemy ORM (SQLite dev / PostgreSQL prod) |
| `conversation.py` | Natural language workflow builder |

### Workflow YAML structure

```yaml
id: feature-dev
agents:
  - id: planner
    name: Planner
    role: Requirements Analysis & Task Breakdown
    prompt: |
      [Agent instructions]
steps:
  - id: plan
    agent: planner
    input: "{{task}}"
    expects: "STATUS: done"   # Acceptance criteria string
    retry: 2
    on_fail: retry            # retry | skip | escalate | abort
  - id: develop
    agent: developer
    input: "{{step_outputs.plan}}"
    execute: "pytest tests/"  # Optional shell command after step
    artifacts_required: false
```

The YAML parser uses the `id` field (not `role`) for agent-to-role mapping. Template variables with hyphenated step IDs are converted (`{{step_outputs.X}}` → `{X}` format internally).

### MCP integration

`MCPToolBridge` (`tools/mcp_bridge.py`) connects workflow tool references to real MCP servers (PubMed, Ahrefs, Similarweb, etc.) via `MCPToolRegistry` (`tools/registry.py`).

## File Organisation Rules

These are enforced automatically by the pre-commit hook (`scripts/check_root_clutter.py`) — violations are blocked at commit time.

| File type | Correct location | Notes |
|---|---|---|
| Documentation (`*.md`) | `docs/` → `docs/guides/`, `docs/phases/`, `docs/reports/` | `README.md` and `CLAUDE.md` are the only `.md` files allowed at root |
| Test files (`test_*.py`) | `tests/` | Mirrors the module under test; marked `@pytest.mark.integration` if they need a live API key |
| Bundled workflow YAMLs | `agenticom/bundled_workflows/` | No ad-hoc YAMLs at root |
| Workflow run artifacts | `outputs/` (gitignored) | Never committed; generated at runtime |
| One-off scripts / utilities | `scripts/` | Not `orchestration/` and not root |

## Code Style

- **Formatter**: Black, line length 88
- **Linter**: Ruff (rules: E, F, W, I, N, UP, B, C4; E501 ignored)
- **Type checking**: mypy with `disallow_untyped_defs = true`
- **Python**: 3.10+ required
- **Async**: pytest uses `asyncio_mode = "auto"` — async test functions work without decorators

## Entry Points

Three CLI entry points defined in `pyproject.toml`:
- `agentic` → `orchestration.cli:main`
- `agenticom` → `agenticom.cli:main`
- `agenticom-launch` → `orchestration.launcher:main`

## Demo & Examples

- **`demo/`** — SmartChatbox: Real LLM-powered multi-turn interview demo with Claude API integration (`demo/server.py` + `demo/index.html`)
- **`examples/`** — Code examples for using the framework
- **`experiments/`** — Research/evaluation scripts (not for production use)

## Verification Protocol

Before claiming any fix or feature is working, test it from the user's perspective:

```bash
# API/backend changes — test the actual endpoint
curl -s http://localhost:8000/api/endpoint | jq .

# CLI changes — run the actual command
agenticom workflow status <run-id>

# Dashboard/UI changes — verify served content, then check browser console (F12)
curl -s http://localhost:8080/ | grep "my-new-function"

# Common pitfalls for the dashboard Python server:
find . -name "*.pyc" -delete   # Clear stale cache
pkill -9 -f "agenticom dashboard" && agenticom dashboard &
```

**Web UI known gotchas:** Nested template literals → use string concatenation. Unescaped quotes in dynamic content → `.replace(/"/g, '&quot;')`. CORS errors → check server headers.

**Rule:** Only report success after running the above verifications, not after editing source files.
