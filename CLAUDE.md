# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agenticom is a Python framework for orchestrating multi-agent AI teams. Agents (planner, developer, verifier, tester, reviewer) collaborate through YAML-defined workflows with production safety features: guardrails, memory, approval gates, and observability. Inspired by Antfarm but adds MCP integration for real tool execution.

**9 Bundled Workflows**: 2 core (feature-dev, marketing-campaign) + 7 enterprise (due-diligence, compliance-audit, patent-landscape, security-assessment, churn-analysis, grant-proposal, incident-postmortem).

## Common Commands

```bash
# Setup
make install              # pip install -e .
make dev                  # Install with dev + LLM provider deps

# Testing
make test                 # pytest tests/ -v
pytest tests/test_agents.py -v              # Run single test file
pytest tests/test_agents.py::TestName -v    # Run single test class/function

# Code Quality
make lint                 # ruff check + mypy
make format               # black + ruff --fix

# Dev Server
make serve                # uvicorn on port 8000 with reload

# CLI
agenticom workflow list
agenticom workflow run <id> "<task description>"
agenticom workflow inspect <id>            # Show step inputs/outputs
agenticom workflow status <run-id>
agenticom workflow resume <run-id>
agenticom dashboard                        # Open web UI
```

## Architecture

### Core packages

- **`orchestration/`** — Framework core. All major subsystems are modules here.
- **`agenticom/`** — CLI entry point and bundled workflow YAML files (`agenticom/bundled_workflows/`).
- **`frontend/`** — React + Vite + TypeScript web dashboard (Zustand, TanStack Query, Tailwind).

### Execution flow

1. **YAML workflow** defines agents (with roles/prompts) and steps (with template inputs)
2. **`WorkflowParser`** (`orchestration/workflows/parser.py`) converts YAML → `AgentTeam` with `WorkflowStep` list
3. **`AgentTeam`** (`orchestration/agents/team.py`) executes steps sequentially; each step gets fresh context ("Ralph Loop" pattern to prevent hallucination)
4. **Template substitution**: `{{task}}` injects user input, `{{step_outputs.step_id}}` passes previous step results
5. **LLM execution**: `UnifiedExecutor` (`orchestration/integrations/unified.py`) routes to OpenClaw (Anthropic), Nanobot (OpenAI), or Ollama (local)

### Key subsystems (all under `orchestration/`)

| Module | Purpose |
|---|---|
| `agents/` | Base agent, specialized agents (Planner/Developer/Verifier/Tester/Reviewer), AgentTeam orchestration, TeamBuilder fluent API |
| `workflows/` | YAML parser, template substitution engine |
| `integrations/` | LLM backends: OpenClaw, Nanobot, Ollama + `auto_setup_executor()` |
| `tools/` | MCP bridge, tool registry, PromptEngineer, IntentRefiner (PIR), ConversationalRefiner, SmartRefiner (multi-turn interview → coherent prompt synthesis), HybridRefiner |
| `guardrails.py` | Composable pipeline: content filter, PII detection, rate limiting |
| `memory.py` | Local/Redis/PostgreSQL memory backends |
| `approval.py` | Auto/Human/Hybrid approval gates |
| `pipeline.py` | Generic step-by-step execution engine |
| `evaluator.py` | Rule-based + LLM-based quality evaluation |
| `observability.py` | Prometheus metrics, structlog, distributed tracing |
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
    expects: "STATUS: done"
    retry: 2
  - id: develop
    agent: developer
    input: "{{step_outputs.plan}}"
```

The YAML parser uses the `id` field (not `role`) for agent-to-role mapping. Template variables with hyphenated step IDs are converted (`{{step_outputs.X}}` → `{X}` format internally).

### MCP integration

`MCPToolBridge` (`tools/mcp_bridge.py`) connects workflow tool references to real MCP servers (PubMed, Ahrefs, Similarweb, etc.) via `MCPToolRegistry` (`tools/registry.py`).

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

## Debugging Web Applications

**IMPORTANT:** When implementing or debugging web features (dashboard, frontend, etc.):

1. **Always check the browser console first**
   - Press `F12` (or `Cmd+Option+I` on Mac)
   - Look for JavaScript errors (red messages)
   - Check Network tab for API failures
   - Example: "Uncaught SyntaxError" indicates a JavaScript syntax error

2. **Common issues:**
   - Nested template literals cause syntax errors → Use string concatenation instead
   - Unescaped quotes in dynamic content → Always escape with `.replace(/"/g, '&quot;')`
   - API returning data but UI empty → JavaScript error preventing execution
   - CORS errors → Check server headers

3. **Debugging workflow:**
   ```javascript
   // Add console.log to trace execution
   console.log('Loading data...', data);

   // Add error handling
   try {
     await someOperation();
   } catch (err) {
     console.error('Operation failed:', err);
   }
   ```

4. **Test API endpoints independently:**
   ```bash
   curl http://localhost:3000/api/workflows
   curl http://localhost:3000/api/runs
   ```
