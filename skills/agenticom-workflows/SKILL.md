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

## Example Prompts

### 🏠 Real Estate Marketing Team
```
Use agenticom marketing-campaign to create a complete digital marketing
strategy for a luxury real estate agency in Miami targeting international
buyers. Include: buyer personas, competitor audit, 30-day content calendar,
influencer outreach list, and 90-day launch plan with KPIs.
```

### 🧬 Biomedical Research Deep Dive
```
Use agenticom feature-dev to research CAR-T cell therapy resistance in
solid tumors. Scout literature (2020-2024), categorize resistance mechanisms,
verify claims against primary data, generate 5 novel hypotheses, and write
a 15-page review article with citations.
```

### 🚀 Idea to Product with PMF
```
Use agenticom feature-dev to validate my startup idea: "An AI copilot for
freelance consultants that turns client calls into SOWs and invoices."
Research market size, analyze competitors, design MVP spec, build financial
model, and create go-to-market plan for first 100 customers.
```

## Example Session

```bash
$ agenticom workflow run marketing-campaign "Go-to-market for B2B SaaS targeting HR teams"

🚀 Running workflow: marketing-campaign
📝 Task: Go-to-market for B2B SaaS targeting HR teams

✅ Run ID: 27c491eb
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ discover (Trend Scout): Identified 3 buyer personas, pain points
   ✅ analyze (Competitor Analyst): Audited 8 competitors, found gaps
   ✅ create (Content Creator): 30-day calendar, email sequences
   ✅ outreach (Partnership Builder): 25 targets, pitch templates
   ✅ orchestrate (Launch Planner): 90-day plan with KPIs
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
