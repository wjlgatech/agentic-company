<p align="center">
  <img src="assets/icons/agenticom-golden.svg" width="180" alt="Agenticom"/>
</p>

<h1 align="center">🏢 AGENTICOM</h1>

<p align="center">
  <strong>The Missing Orchestration Layer for OpenClaw & Nanobot</strong><br>
  <em>Ship AI Agents to Production in Minutes, Not Months</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Tests-107%20Passing-brightgreen?style=for-the-badge" alt="Tests"/>
  <img src="https://img.shields.io/badge/OpenClaw-Ready-blue?style=for-the-badge" alt="OpenClaw"/>
  <img src="https://img.shields.io/badge/Nanobot-Ready-orange?style=for-the-badge" alt="Nanobot"/>
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge" alt="Python"/>
</p>

<p align="center">
  <a href="#-30-second-install">Install</a> •
  <a href="#-whats-new">What's New</a> •
  <a href="#-why-agenticom">Why Agenticom</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🚀 30-Second Install

```bash
# One command. That's it.
curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash
```

<details>
<summary>Windows PowerShell</summary>

```powershell
irm https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.ps1 | iex
```
</details>

**What happens:**
- ✅ Auto-installs OpenClaw (Anthropic SDK)
- ✅ Auto-installs Nanobot (OpenAI SDK)
- ✅ Creates desktop icon (choose: 🐷 Piglet, 🦀 Claw, or 🐕 Golden)
- ✅ Ready to run in 30 seconds

---

## 🆕 WHAT'S NEW

### 🤝 Multi-Agent Teams with Cross-Verification
*Inspired by [Antfarm](https://github.com/snarktank/antfarm) — but with production-grade safety*

```python
from orchestration import TeamBuilder, AgentRole, create_feature_dev_team

# One line to create a full dev team
team = create_feature_dev_team()

# Or build custom teams
team = (TeamBuilder("my-team")
    .with_planner()       # Breaks down tasks
    .with_developer()     # Writes code
    .with_verifier()      # Checks work (cross-verification!)
    .with_tester()        # Runs tests
    .with_reviewer()      # Final approval
    .step("plan", AgentRole.PLANNER, "Plan: {task}")
    .step("code", AgentRole.DEVELOPER, "Code: {plan}",
          verified_by=AgentRole.VERIFIER)  # ← Agents verify each other!
    .step("review", AgentRole.REVIEWER, "Review: {code}",
          requires_approval=True)  # ← Human in the loop
    .build())

# Run it
result = await team.run("Build user authentication")
```

**Why this matters:** Agents don't self-assess. The Verifier catches what the Developer misses. **39 tests prove it works.**

---

### ⚡ Auto-Backend Detection (OpenClaw + Nanobot)

```python
from orchestration import auto_setup_executor

# Automatically uses Claude if ANTHROPIC_API_KEY is set
# Falls back to GPT if OPENAI_API_KEY is set
# Installs missing SDKs automatically!
executor = auto_setup_executor()

# Connect to any agent
from orchestration import DeveloperAgent
agent = DeveloperAgent()
agent.set_executor(executor.execute)
```

**No more SDK juggling.** Set your API key, Agenticom handles the rest.

---

### 📝 YAML Workflows (Human-Readable Config)

```yaml
# workflows/feature-dev.yaml
id: feature-dev
name: Feature Development

agents:
  - role: planner
    guardrails: [content-filter, pii-detection]
  - role: developer
  - role: verifier

steps:
  - id: plan
    agent: planner
    input: "Create plan for: {task}"

  - id: implement
    agent: developer
    input: "Implement: {plan}"
    verified_by: verifier  # Cross-verification
    max_retries: 3
```

```python
from orchestration import load_workflow
team = load_workflow("workflows/feature-dev.yaml")
```

**Version control your AI workflows.** Review them in PRs like any other code.

---

## 🎯 WHY AGENTICOM?

| Problem | Without Agenticom | With Agenticom |
|---------|------------------|----------------|
| **Agent goes rogue** | 😱 Unfiltered output | ✅ Guardrails block PII, harmful content |
| **Context window bloat** | 😱 Agent forgets mid-task | ✅ Fresh context per step |
| **No verification** | 😱 Agent self-assesses | ✅ Cross-verification between agents |
| **Risky actions** | 😱 Auto-executes everything | ✅ Human approval gates |
| **Black box** | 😱 No idea what happened | ✅ Full observability stack |
| **SDK juggling** | 😱 Different code for Claude/GPT | ✅ One interface, auto-detection |

---

## ✅ VERIFIED FEATURES (107 Tests Passing)

| Feature | Tests | What It Does |
|---------|-------|--------------|
| 🤝 **Agent Teams** | 39 | Multi-agent orchestration with cross-verification |
| 🛡️ **Guardrails** | 20 | PII detection, content filtering, rate limiting |
| 🧠 **Memory** | 5 | Store/search/recall across sessions |
| ✅ **Approvals** | 6 | Human-in-the-loop for risky actions |
| 📊 **Observability** | 4 | Metrics, tracing, structured logging |
| 🔗 **Pipeline** | 8 | Multi-step workflow orchestration |
| 🌐 **REST API** | 17 | FastAPI endpoints for everything |
| 💻 **CLI** | 8 | Command-line interface |

```bash
# Verify yourself
pytest tests/ -v
# 107 passed ✅
```

---

## ⚡ QUICK START

### 1. Set Your API Key

```bash
# For Claude (recommended)
export ANTHROPIC_API_KEY=sk-ant-...

# Or for GPT
export OPENAI_API_KEY=sk-...
```

### 2. Run Your First Team

```python
import asyncio
from orchestration import create_feature_dev_team

team = create_feature_dev_team()
result = asyncio.run(team.run("Add a logout button"))

print(f"Success: {result.success}")
print(f"Steps: {len(result.steps)}")
```

### 3. Add Guardrails

```python
from orchestration import ContentFilter, GuardrailPipeline, DeveloperAgent

# Block sensitive content
guardrails = GuardrailPipeline([
    ContentFilter(blocked_topics=["credentials", "api_keys"])
])

agent = DeveloperAgent()
agent.set_guardrails(guardrails)
# Now all inputs/outputs are filtered!
```

### 4. Start the API Server

```bash
agentic serve --port 8000
# Now you have 17 REST endpoints!
```

---

## 🗺️ ROADMAP

### ✅ Shipped
- [x] Multi-agent teams with cross-verification
- [x] YAML workflow definitions
- [x] OpenClaw + Nanobot auto-integration
- [x] One-click installer with desktop icon
- [x] 107 automated tests

### 🔜 Coming Next
- [ ] **Real-time Dashboard** — Watch agents work live
- [ ] **Git-based Memory** — Knowledge persists in repo history
- [ ] **Cron Scheduling** — Recurring agent workflows
- [ ] **MCP Server** — Connect to Claude Desktop
- [ ] **Nano Banana Video Demos** — AI-generated tutorials

### 🌟 Future Vision
- [ ] **Agent Marketplace** — Share/download pre-built teams
- [ ] **Visual Workflow Builder** — Drag-and-drop agent design
- [ ] **Multi-modal Agents** — Image/video understanding
- [ ] **Distributed Execution** — Scale across machines

---

## 📦 Project Structure

```
agenticom/
├── orchestration/
│   ├── agents/           # Multi-agent teams
│   ├── workflows/        # YAML parser & templates
│   ├── integrations/     # OpenClaw + Nanobot
│   ├── guardrails.py     # Safety layer
│   ├── memory.py         # Context persistence
│   ├── approval.py       # Human-in-the-loop
│   └── observability.py  # Metrics & tracing
├── tests/                # 107 tests
├── assets/icons/         # 🐷🦀🐕
└── install.sh            # One-click installer
```

---

## 🤝 Contributing

```bash
git clone https://github.com/wjlgatech/agentic-company
cd agentic-company
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 📄 License

MIT — Use it, fork it, ship it.

---

<p align="center">
  <strong>Built for the OpenClaw era 🦀</strong><br>
  <em>Every claim backed by passing tests</em><br>
  <br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star on GitHub</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Report Bug</a> •
  <a href="https://github.com/wjlgatech/agentic-company/discussions">💬 Discuss</a>
</p>
