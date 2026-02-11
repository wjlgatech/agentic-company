---
name: agenticom
description: "Multi-agent workflow orchestration. Run feature-dev, marketing-campaign, or custom workflows with 5 specialized agents that verify each other's work."
metadata: {"nanobot":{"emoji":"🤖","requires":{"bins":["python3","pip"]},"install":[{"id":"pip","kind":"pip","package":"agentic-company","bins":["agenticom"],"label":"Install Agenticom (pip)"}]}}
---

# Agenticom Skill

Multi-agent workflow pipelines for Nanobot. Each workflow is a sequence of specialized agents (planner, developer, verifier, tester, reviewer) that execute steps with cross-verification.

## Installation

```bash
# Clone and install
git clone https://github.com/wjlgatech/agentic-company.git ~/.nanobot/workspace/agenticom
cd ~/.nanobot/workspace/agenticom && pip install -e .

# Install bundled workflows
agenticom install
```

## Workflows

| Workflow | Pipeline | Use for |
|----------|----------|---------|
| `feature-dev` | plan → implement → verify → test → review | New features, refactors |
| `marketing-campaign` | discover → analyze → create → outreach → orchestrate | Launch campaigns |

## Example Prompts

### 🏠 Real Estate Marketing Team
```
Use agenticom marketing-campaign to create a digital marketing strategy
for a luxury real estate agency. Include buyer personas, competitor audit,
30-day content calendar, and 90-day launch plan.
```

### 🧬 Deep Research Team
```
Use agenticom feature-dev to research CAR-T therapy resistance mechanisms.
Scout literature, categorize findings, verify claims, generate hypotheses,
and write a review article.
```

### 🚀 Idea to Product
```
Use agenticom feature-dev to validate my startup idea: "AI expense tracker."
Research market, analyze competitors, design MVP, build financial model,
and create go-to-market plan.
```

## Commands

List workflows:
```bash
agenticom workflow list
```

Run a workflow:
```bash
agenticom workflow run marketing-campaign "Go-to-market for B2B HR SaaS"
```

Check status:
```bash
agenticom workflow status <run-id>
```

Resume failed run:
```bash
agenticom workflow resume <run-id>
```

View statistics:
```bash
agenticom stats
```

## LLM Backends

Use with FREE local LLM (Ollama):
```bash
export OLLAMA_MODEL=llama3.2
agenticom workflow run feature-dev "Add caching"
```

Use with Claude:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
agenticom workflow run feature-dev "Add caching"
```

Use with GPT:
```bash
export OPENAI_API_KEY=sk-...
agenticom workflow run feature-dev "Add caching"
```

## How It Works

- Steps execute sequentially with context passing between agents
- Each agent gets fresh context (no bloat from previous messages)
- SQLite tracks all state in `~/.agenticom/state.db`
- Failed steps can be resumed with `agenticom workflow resume`

## Features Beyond Antfarm

| Feature | Description |
|---------|-------------|
| Guardrails | Content filter, rate limiter |
| Memory | Persistent remember/recall |
| Approval Gates | Auto/Human/Hybrid |
| Multi-Backend | Ollama FREE, Claude, GPT |
| REST API | 27 endpoints |
| Caching | LLM response cache |

Full documentation: https://github.com/wjlgatech/agentic-company
