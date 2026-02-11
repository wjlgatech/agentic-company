<p align="center">
  <img src="assets/icons/agenticom-golden.svg" width="180" alt="Agenticom"/>
</p>

<h1 align="center">AGENTICOM</h1>

<p align="center">
  <strong>Multi-Agent Orchestration for Claude Code & Cursor</strong><br>
  <em>YAML workflows. SQLite state. Zero infrastructure.</em>
</p>

<p align="center">
  <a href="#-install-in-30-seconds">Install</a> •
  <a href="#-run-your-first-workflow">Quick Start</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-python-api">Python API</a>
</p>

---

## Why Agenticom?

Most agent frameworks need Redis, Postgres, Docker, Kubernetes...

**Agenticom needs nothing.** Just `pip install` and go.

```
┌─────────────────────────────────────────────────────┐
│  Other Frameworks          │  Agenticom            │
├─────────────────────────────────────────────────────┤
│  Redis + Postgres + Docker │  SQLite (auto-created)│
│  Complex YAML configs      │  2-line workflow start│
│  Separate infra setup      │  pip install → done   │
│  Context bloat problems    │  Fresh context/step   │
│  No verification           │  Cross-agent verify   │
└─────────────────────────────────────────────────────┘
```

Inspired by [antfarm](https://github.com/jlowin/antfarm) — the same pattern that powers production AI workflows.

---

## Install in 30 Seconds

```bash
pip install agentic-company
agenticom install
```

That's it. You now have 2 production workflows ready to run.

---

## Run Your First Workflow

```bash
agenticom workflow run feature-dev "Add user authentication with JWT"
```

**Real output (not mocked):**

```
🚀 Running workflow: feature-dev
📝 Task: Add user authentication with JWT

✅ Run ID: 27c491eb
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ plan (Planner): completed
   ✅ implement (Developer): completed
   ✅ verify (Verifier): completed
   ✅ test (Tester): completed
   ✅ review (Reviewer): completed

💡 Check status: agenticom workflow status 27c491eb
```

**5 agents. 5 steps. Cross-verification built in.**

---

## What's Included

### 2 Bundled Workflows

| Workflow | Agents | Steps | Use Case |
|----------|--------|-------|----------|
| `feature-dev` | 5 | 5 | Planner → Developer → Verifier → Tester → Reviewer |
| `marketing-campaign` | 5 | 5 | SocialIntel → Competitor → Content → Community → Lead |

```bash
# List all workflows
agenticom workflow list

📋 2 workflows available:

🔹 feature-dev
   Name: Feature Development Team
   Agents: 5 | Steps: 5

🔹 marketing-campaign
   Name: Viral Marketing Campaign
   Agents: 5 | Steps: 5
```

---

## How It Works

### The Antfarm Pattern

Agenticom follows the [antfarm](https://github.com/jlowin/antfarm) architecture:

```
┌──────────────────────────────────────────────────────────────┐
│                     YAML WORKFLOW                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ Step 1  │ → │ Step 2  │ → │ Step 3  │ → │ Step 4  │      │
│  │ Planner │   │Developer│   │Verifier │   │ Tester  │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│       ↓             ↓             ↓             ↓            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLite State (auto-persisted)            │   │
│  │  • Run history  • Step outputs  • Error tracking      │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Key principles:**

1. **Fresh context per step** — No context bloat. Each agent starts clean.
2. **Cross-agent verification** — Verifier agent checks Developer's work.
3. **SQLite state** — Everything persists locally. Resume failed runs.
4. **YAML definitions** — Workflows are data, not code.

---

## CLI Commands

```bash
# Install bundled workflows
agenticom install

# List available workflows
agenticom workflow list

# Run a workflow
agenticom workflow run <workflow-id> "<task description>"

# Check run status
agenticom workflow status <run-id>

# Resume a failed run
agenticom workflow resume <run-id>

# View statistics
agenticom stats

# Remove all data
agenticom uninstall --force
```

### Example: Marketing Campaign

```bash
agenticom workflow run marketing-campaign "Launch AI coding assistant for React developers"
```

```
🚀 Running workflow: marketing-campaign
📝 Task: Launch AI coding assistant for React developers

✅ Run ID: 52d70ac4
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ discover-pain-points (SocialIntelAgent): completed
   ✅ analyze-competitors (CompetitorAnalyst): completed
   ✅ create-content-calendar (ContentCreator): completed
   ✅ plan-outreach (CommunityManager): completed
   ✅ orchestrate-campaign (CampaignLead): completed
```

---

## Python API

```python
from agenticom import AgenticomCore, WorkflowRunner, WorkflowDefinition, StateManager

# Initialize
core = AgenticomCore()

# List workflows
workflows = core.list_workflows()
for wf in workflows:
    print(f"{wf['id']}: {wf['name']} ({wf['agents']} agents)")

# Run a workflow
result = core.run_workflow("feature-dev", "Build REST API for user management")
print(f"Run ID: {result['run_id']}")
print(f"Status: {result['status']}")
print(f"Steps completed: {result['steps_completed']}/{result['total_steps']}")

# Check status
status = core.get_run_status(result['run_id'])

# Get statistics
stats = core.get_stats()
print(f"Total runs: {stats['total_runs']}")
```

---

## Create Custom Workflows

Workflows are YAML files in `~/.agenticom/workflows/`:

```yaml
# my-workflow.yaml
id: my-workflow
name: My Custom Workflow
description: Does something cool

agents:
  - id: researcher
    name: Researcher
    role: Research and gather information
    prompt: |
      You are a research specialist.
      Find relevant information about the given topic.
    tools: [web_search]

  - id: writer
    name: Writer
    role: Create content from research
    prompt: |
      You are a content writer.
      Create clear, engaging content from research findings.
    tools: [text_generation]

steps:
  - id: research
    agent: researcher
    input: |
      TASK: {{task}}
      Find comprehensive information about this topic.
      Reply with STATUS: done when complete.
    expects: "STATUS: done"
    retry: 2

  - id: write
    agent: writer
    input: |
      TASK: {{task}}
      Research findings: {{step_outputs.research}}
      Create a well-structured document.
      Reply with STATUS: done when complete.
    expects: "STATUS: done"
    retry: 2
```

Then run it:

```bash
agenticom workflow run my-workflow "Write about AI trends in 2025"
```

---

## Stats & Monitoring

```bash
agenticom stats
```

```
📊 Agenticom Statistics
========================================
📁 Workflows installed: 2
🔹 Workflow names: Feature Development Team, Viral Marketing Campaign
📈 Total runs: 2
📂 Database: ~/.agenticom/state.db

📊 Runs by status:
   • completed: 2
   • failed: 0
   • pending: 0
```

---

## Installation

```bash
# From PyPI
pip install agentic-company

# From source
git clone https://github.com/wjlgatech/agentic-company
cd agentic-company
pip install -e .
```

### Requirements

- Python 3.10+
- No external services (SQLite is built-in)

---

## Project Structure

```
agenticom/
├── __init__.py           # Package exports
├── cli.py                # CLI commands
├── core.py               # Main orchestration engine
├── state.py              # SQLite state management
├── workflows.py          # YAML workflow parser & runner
└── bundled_workflows/
    ├── feature-dev.yaml
    └── marketing-campaign.yaml
```

---

## Integration with Claude Code / Cursor

Agenticom is designed to work as a tool within Claude Code or Cursor:

```bash
# In your Claude Code session
agenticom workflow run feature-dev "Add caching to the API"
```

The workflow runs in the background, with each step executed by a specialized agent. Results are persisted to SQLite, so you can check status anytime.

---

## Roadmap

### Shipped
- [x] CLI with install/run/status/resume commands
- [x] SQLite state persistence
- [x] YAML workflow definitions
- [x] 2 bundled production workflows
- [x] Cross-agent verification pattern
- [x] Python API

### Coming
- [ ] MCP server integration
- [ ] More bundled workflows
- [ ] Visual workflow editor

---

## Contributing

```bash
git clone https://github.com/wjlgatech/agentic-company
cd agentic-company
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

MIT — Use it, fork it, ship it.

---

<p align="center">
  <strong>Zero infrastructure. Real workflows.</strong><br>
  <br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star on GitHub</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Report Bug</a>
</p>
