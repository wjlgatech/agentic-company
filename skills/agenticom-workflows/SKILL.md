---
name: agenticom-workflows
description: "Python-based multi-agent workflow orchestration. Use when user mentions agenticom, asks to run a multi-step workflow (feature dev, marketing campaign), or wants to install/uninstall/check status of agenticom workflows. Alternative to antfarm with Python API, guardrails, memory, and approval gates."
user-invocable: false
---

# Agenticom

Multi-agent workflow pipelines for OpenClaw. Each workflow is a sequence of specialized agents (planner, developer, verifier, tester, reviewer) that execute steps with cross-verification. Python-based with SQLite state persistence.

## Installation

```bash
# Clone and install
git clone https://github.com/wjlgatech/agentic-company.git ~/.openclaw/workspace/agenticom
cd ~/.openclaw/workspace/agenticom && pip install -e .

# Install bundled workflows
agenticom install
```

## Workflows

| Workflow | Pipeline | Use for |
|----------|----------|---------|
| `feature-dev` | plan → implement → verify → test → review | New features, refactors |
| `marketing-campaign` | discover → analyze → create → outreach → orchestrate | Launch campaigns |

## Core Commands

```bash
# Install all bundled workflows
agenticom install

# Full uninstall
agenticom uninstall [--force]

# Start a run
agenticom workflow run <workflow-id> "<task description>"

# Check run status
agenticom workflow status <run-id>

# List all runs
agenticom stats

# Resume a failed run
agenticom workflow resume <run-id>

# List available workflows
agenticom workflow list
```

## Before Starting a Run

The task string is the contract between you and the agents. A vague task produces bad results.

**Always include in the task string:**
1. What to build/fix (specific, not vague)
2. Key technical details and constraints
3. Acceptance criteria

Get the user to confirm the plan and acceptance criteria before running.

## Example Session

```bash
$ agenticom workflow list
📋 2 workflows available:

🔹 feature-dev
   Name: Feature Development Team
   Agents: 5 | Steps: 5

🔹 marketing-campaign
   Name: Viral Marketing Campaign
   Agents: 5 | Steps: 5

$ agenticom workflow run feature-dev "Add JWT authentication to the REST API"
🚀 Running workflow: feature-dev
📝 Task: Add JWT authentication to the REST API

✅ Run ID: 27c491eb
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ plan (Planner): completed
   ✅ implement (Developer): completed
   ✅ verify (Verifier): completed
   ✅ test (Tester): completed
   ✅ review (Reviewer): completed

$ agenticom workflow status 27c491eb
🔹 Run ID: 27c491eb
📋 Workflow: feature-dev
📝 Task: Add JWT authentication to the REST API
📊 Status: completed
📈 Progress: 5/5 steps
```

## How It Works

- Steps execute sequentially with context passing between agents
- Each agent gets fresh context (no bloat from previous messages)
- SQLite tracks all state in `~/.agenticom/state.db`
- Failed steps can be resumed with `agenticom workflow resume`

## Agenticom vs Antfarm

| Feature | Antfarm | Agenticom |
|---------|---------|-----------|
| Language | TypeScript | Python |
| Cron polling | Yes | No (direct execution) |
| Guardrails | No | Yes (content filter, rate limiter) |
| Memory | No | Yes (persistent remember/recall) |
| Approval Gates | No | Yes (auto/human/hybrid) |
| Multi-backend | No | Yes (Ollama FREE, Claude, GPT) |
| REST API | No | Yes (27 endpoints) |
| Dashboard | Yes | CLI-based |

## Python API (for advanced users)

```python
from agenticom import AgenticomCore

core = AgenticomCore()

# List workflows
workflows = core.list_workflows()

# Run a workflow
result = core.run_workflow("feature-dev", "Add caching to API")
print(f"Run ID: {result['run_id']}")
print(f"Status: {result['status']}")

# Check status
status = core.get_run_status(result['run_id'])
```

## Creating Custom Workflows

Workflows are YAML files in `~/.agenticom/workflows/`:

```yaml
id: my-workflow
name: My Custom Workflow

agents:
  - id: researcher
    name: Researcher
    role: Research and gather information
    prompt: |
      You are a research specialist.
      Find relevant information about the given topic.

steps:
  - id: research
    agent: researcher
    input: |
      TASK: {{task}}
      Research this topic thoroughly.
      Reply with STATUS: done when complete.
    expects: "STATUS: done"
    retry: 2
```

## Additional Features

Agenticom includes production features beyond workflow orchestration:

```bash
# Use with FREE local LLM (Ollama)
export OLLAMA_MODEL=llama3.2

# Use with Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Use with GPT
export OPENAI_API_KEY=sk-...
```

For guardrails, memory, approval gates, and REST API - see the full documentation at https://github.com/wjlgatech/agentic-company
