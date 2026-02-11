# Agenticom Integration Guide

## What is Agenticom?

Agenticom is **multi-agent orchestration** - it coordinates teams of AI agents to complete complex tasks. Think of it as a "team manager" for AI agents.

## 3 Ways to Use Agenticom

### 1️⃣ As an MCP Server (Recommended)

Add Agenticom as a tool in Claude Code, Cursor, or any MCP-compatible AI assistant.

**Setup for Claude Code:**

```bash
# Install
pip install agenticom

# Add to ~/.claude/claude_desktop_config.json:
{
    "mcpServers": {
        "agenticom": {
            "command": "python",
            "args": ["-m", "orchestration.mcp_server"]
        }
    }
}
```

**Then in Claude Code:**
```
> Use the agenticom_list_teams tool to see available teams
> Use agenticom_run_team with team_id="marketing" and task="Launch campaign for my AI coding tool"
```

**Available MCP Tools:**
| Tool | Description |
|------|-------------|
| `agenticom_list_teams` | List all available agent teams |
| `agenticom_get_team` | Get details about a specific team |
| `agenticom_run_team` | Run a team on a task (returns execution plan) |
| `agenticom_execute_step` | Execute a single step in the workflow |
| `agenticom_create_team` | Create a custom agent team |

---

### 2️⃣ As a CLI Tool

Run multi-agent workflows from your terminal.

```bash
# Install
pip install agenticom

# List available teams
agentic teams list

# Run a marketing campaign
agentic teams run marketing --task "Launch my SaaS product"

# Run with custom config
agentic teams run development \
    --task "Build REST API with FastAPI" \
    --config '{"tech_stack": "python", "testing": true}'

# Create workflow from conversation
agentic create
# (Interactive mode - answers questions to build your team)
```

---

### 3️⃣ As a Python Library

Import and use programmatically in your code.

```python
from agenticom import AgentTeam, TeamBuilder

# Use pre-built teams
from agenticom.teams import MarketingTeam, DevelopmentTeam

# Run marketing campaign
team = MarketingTeam(
    product="AI Coding Assistant",
    competitors=["Copilot", "Cursor"],
    platforms=["twitter", "reddit", "hackernews"]
)
result = await team.run()

# Or build custom teams
team = (
    TeamBuilder("my-custom-team")
    .add_agent("Researcher", "Find information about {topic}")
    .add_agent("Analyzer", "Analyze the research findings")
    .add_agent("Writer", "Write a comprehensive report")
    .with_cross_verification(True)
    .build()
)

result = await team.run("AI agent frameworks comparison")
```

---

## Pre-built Teams

| Team | Agents | Use Case |
|------|--------|----------|
| **Marketing** | SocialIntel → Competitor → Content → Community → Campaign | Viral growth campaigns |
| **Development** | Planner → Developer → Verifier → Tester → Reviewer | Feature development |
| **Research** | Researcher → Analyst → Synthesizer → FactChecker → Writer | Deep research & reports |
| **Content** | Ideator → Writer → Editor → SEO → Publisher | Content at scale |
| **Security** | Scanner → Analyzer → Recommender → Verifier | Security audits |

---

## How It Works With OpenClaw/Nanobot

Agenticom is **NOT a replacement** for Claude or GPT. It's a **coordination layer** that:

1. **Breaks tasks into agent roles** (Planner, Developer, Reviewer, etc.)
2. **Generates specialized prompts** for each agent
3. **Chains outputs** from one agent to the next
4. **Adds guardrails** (validation, approval gates, memory)

```
Your Request
     ↓
┌─────────────────────────────────────────┐
│           AGENTICOM ORCHESTRATION       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Agent 1 │→ │ Agent 2 │→ │ Agent 3 │  │
│  │(Planner)│  │(Builder)│  │(Reviewer│  │
│  └────┬────┘  └────┬────┘  └────┬────┘  │
│       ↓            ↓            ↓       │
│   ┌───────────────────────────────┐     │
│   │    Claude / GPT / Ollama      │     │
│   │    (Actual LLM execution)     │     │
│   └───────────────────────────────┘     │
└─────────────────────────────────────────┘
     ↓
Final Output (verified, reviewed, tested)
```

---

## Quick Start Examples

### Marketing Campaign
```bash
# Via CLI
agentic teams run marketing \
    --task "Launch my AI coding assistant for React developers" \
    --config '{"competitors": ["Copilot", "Cursor"], "duration": 30}'

# Via Python
from agenticom.teams import MarketingTeam
team = MarketingTeam(product="CodeAssist", target="React developers")
await team.run()
```

### Feature Development
```bash
# Via CLI
agentic teams run development \
    --task "Add user authentication with OAuth"

# Via MCP (in Claude Code)
> Run agenticom_run_team with team_id="development" and task="Add OAuth authentication"
```

### Custom Research
```python
from agenticom import TeamBuilder

team = (
    TeamBuilder("competitor-research")
    .add_agent("WebResearcher", "Find all competitors in {market}")
    .add_agent("FeatureAnalyzer", "Compare features across competitors")
    .add_agent("PricingAnalyzer", "Analyze pricing strategies")
    .add_agent("ReportWriter", "Create executive summary")
    .build()
)

result = await team.run(market="AI code assistants")
```
