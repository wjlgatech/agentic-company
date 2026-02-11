<div align="center">
  <img src="assets/mascot.png" alt="Agenticom Golden Retriever" width="200">
  <h1>Agenticom: Multi-Agent Team Orchestration</h1>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/tests-14%2F14%20passed-brightgreen" alt="Tests">
    <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status">
  </p>
</div>

🐕 **Agenticom** is a multi-agent workflow orchestration framework inspired by [Antfarm](https://github.com/snarktank/antfarm).

⚡️ **One agent makes mistakes. Five agents cross-verify.**

## 📢 News

- **2026-02-11** 🔧 **Critical fixes**: YAML parser + CLI execution now work properly!
- **2026-02-11** 🎉 Added Web Dashboard + Golden Retriever mascot
- **2026-02-11** ✨ Core features verified with stress tests
- **2026-02-11** 🚀 Initial release with OpenClaw + Nanobot skill integrations

## ⚠️ Current Status: Alpha Framework

**Agenticom is a FRAMEWORK, not a turnkey product.** It provides:

### ✅ What Works

| Feature | Status | Notes |
|---------|--------|-------|
| 🛡️ **Guardrails** | ✅ Working | Content filter, rate limiter |
| 🧠 **Memory** | ✅ Working | Persistent remember/recall |
| ✅ **Approval Gates** | ✅ Working | Auto/Human/Hybrid patterns |
| 💾 **Caching** | ✅ Working | LLM response cache |
| 📊 **Observability** | ✅ Working | Prometheus-style metrics |
| 📋 **YAML Workflows** | ✅ Working | Parser loads bundled workflows |
| 🖥️ **CLI** | ✅ Working | `workflow list`, `run --dry-run` |
| 🌐 **Dashboard** | ✅ Working | Visual workflow management |
| ⚡ **Multi-Backend** | ✅ Working | Ollama/Claude/GPT abstraction |

### ⚠️ What Requires Your Implementation

| Feature | Status | What You Need to Build |
|---------|--------|------------------------|
| 🌐 **Web Scraping** | ❌ Not Implemented | Integrate Brave/Google Search API |
| 📱 **Social Media** | ❌ Not Implemented | Connect Twitter/Reddit/LinkedIn APIs |
| 📊 **Analytics** | ❌ Not Implemented | Add Google Analytics, Mixpanel |
| 🔧 **Tool Execution** | ❌ Not Implemented | Build actual tool runners |

**The bundled workflows (`marketing-campaign`, `feature-dev`) define WHAT agents should do via prompts, but the tools they reference (like `web_search`, `social_api`) are declarative placeholders that you must implement.**

<details>
<summary><b>View Test Results (Critical Fixes Verified)</b></summary>

```
🧪 AGENTICOM CRITICAL FIX TEST SUITE
============================================================
TestYAMLParserFix:
  ✅ feature-dev.yaml loads correctly
  ✅ marketing-campaign.yaml loads correctly
  ✅ Parser preserves persona from prompt field
  ✅ Parser correctly uses 'id' for role mapping

TestCLIWorkflowExecution:
  ✅ CLI dry-run mode works
  ✅ CLI workflow run is not mocked
  ✅ CLI shows helpful error when no LLM backend

TestWorkflowListDiscovery:
  ✅ Workflow list discovers actual YAML files

TestAgentTeamExecution:
  ✅ Agent correctly requires executor
  ✅ AgentTeam has async run method

TestWorkflowExecutorWiring:
  ✅ load_workflow() correctly leaves executors unset
  ✅ load_workflow(auto_setup=True) correctly requires LLM backend
  ✅ load_ready_workflow() correctly requires LLM backend
  ✅ load_ready_workflow correctly exported

============================================================
RESULTS: 14/14 tests passed
```

**Critical Fixes Applied (2026-02-11):**
1. **YAML Parser**: Now correctly uses `id` field for role mapping (was using `role` which contained descriptions)
2. **CLI Execution**: Replaced mock `time.sleep()` with real workflow execution
3. **Error Handling**: Clear messages when LLM backend not configured

</details>

## 📦 Install

**1-Click** (auto-detects OpenClaw/Nanobot/Standalone)

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash
```

**From source**

```bash
git clone https://github.com/wjlgatech/agentic-company.git
cd agentic-company && pip install -e . && agenticom install
```

## 🚀 Quick Start

**1. Configure LLM backend (required)**

```bash
# Option A: Ollama (FREE - local)
ollama serve && ollama pull llama3.2

# Option B: Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Option C: GPT
export OPENAI_API_KEY=sk-...
```

**2. Preview a workflow (dry-run)**

```bash
# See what a workflow will do without executing
agenticom workflow run feature-dev -i "Add login button" --dry-run
```

**3. Run a workflow**

```bash
# Actually execute the workflow (requires LLM backend)
agenticom workflow run feature-dev -i "Add a hello world function"
```

**4. Open dashboard**

```bash
agenticom dashboard
```

> ⚠️ **Note**: Workflows execute via LLM prompts. Tools like `web_search` and `social_api` in marketing workflows are **declarative** - you must implement actual tool execution for real-world use.

## 🌐 Web Dashboard

For non-technical users who prefer a visual interface:

```bash
agenticom dashboard
```

Opens at `http://localhost:8080` with:
- 📊 **Stats Overview** - Success rate, running, failed
- 🎯 **Quick Start** - Run workflows from browser
- 📋 **Kanban Board** - Visual pipeline view
- 🌙 **Dark Mode** - Auto-detect system preference

## 📋 Workflows

| Workflow | Pipeline | Use for |
|----------|----------|---------|
| `feature-dev` | plan → implement → verify → test → review | Research, product design |
| `marketing-campaign` | discover → analyze → create → outreach → orchestrate | Go-to-market |

## 🎯 Real-World Examples

<details>
<summary><b>🏠 Real Estate Marketing Team</b></summary>

```
Use agenticom marketing-campaign to create a digital marketing strategy
for a luxury real estate agency in Miami targeting international buyers.

Include: buyer personas, competitor audit (Douglas Elliman, Compass, Sotheby's),
30-day content calendar, influencer outreach list, 90-day launch plan with KPIs.
```

</details>

<details>
<summary><b>🧬 Biomedical Research Deep Dive</b></summary>

```
Use agenticom feature-dev to research CAR-T cell therapy resistance in solid tumors.

Scout literature (2020-2024), categorize resistance mechanisms, verify claims
against primary data, generate 5 novel hypotheses, write 15-page review article.
```

</details>

<details>
<summary><b>🚀 Idea to Product with PMF</b></summary>

```
Use agenticom feature-dev to validate my startup idea: "An AI copilot for
freelance consultants that turns client calls into SOWs and invoices."

Research market, analyze competitors, design MVP, build financial model,
create go-to-market plan for first 100 customers.
```

</details>

## 🦞 Use with OpenClaw

[OpenClaw](https://github.com/openclaw/openclaw) - Personal AI assistant for WhatsApp, Telegram, Slack, Discord.

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash
```

Then tell your assistant: *"Use agenticom to build a marketing strategy for my SaaS"*

## 🐈 Use with Nanobot

[Nanobot](https://github.com/HKUDS/nanobot) - Ultra-lightweight personal AI assistant.

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash
```

Then tell your assistant: *"Use agenticom feature-dev to research and design a mobile app"*

## 🖥️ CLI Reference

| Command | Description |
|---------|-------------|
| `agenticom install` | Install bundled workflows |
| `agenticom workflow list` | List available workflows |
| `agenticom workflow run <id> <task>` | Start a run |
| `agenticom workflow status <run-id>` | Check status |
| `agenticom workflow resume <run-id>` | Resume failed run |
| `agenticom dashboard` | **Open web UI** |
| `agenticom stats` | Show statistics |

## ⚔️ vs Antfarm

| Feature | Antfarm | Agenticom |
|---------|---------|-----------|
| Language | TypeScript | Python |
| Execution | Cron polling | Direct |
| **Guardrails** | ❌ | ✅ |
| **Memory** | ❌ | ✅ |
| **Approval Gates** | ❌ | ✅ |
| **Multi-Backend** | ❌ | ✅ Ollama/Claude/GPT |
| **Observability** | ❌ | ✅ Prometheus |
| **Dashboard** | ✅ | ✅ |

## 🐍 Python API

### Load & Run Workflows (Recommended)

```python
import asyncio
from orchestration import load_ready_workflow

# Load workflow with LLM executor auto-configured
team = load_ready_workflow('feature-dev.yaml')

# Execute
result = asyncio.run(team.run("Add a login button"))
print(result.final_output)
```

### Manual Setup (More Control)

```python
from orchestration import load_workflow, auto_setup_executor

# Load without executor
team = load_workflow('feature-dev.yaml')

# Configure executor manually
executor = auto_setup_executor()
for agent in team.agents.values():
    agent.set_executor(lambda p, c: executor.execute(p, c))

# Execute
result = asyncio.run(team.run("Add a login button"))
```

---

## 🛠️ Verified Features

<details>
<summary><b>🛡️ Guardrails</b></summary>

```python
from orchestration.guardrails import ContentFilter, GuardrailPipeline

pipeline = GuardrailPipeline([
    ContentFilter(blocked_patterns=["password", r"sk-[a-zA-Z0-9]{20,}"])
])
result = pipeline.check("My password is secret")
# result[0].passed = False (blocked!)
```

</details>

<details>
<summary><b>🧠 Memory</b></summary>

```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("User prefers Python", tags=["preference"])
results = memory.search("Python")  # Returns matching memories
```

</details>

<details>
<summary><b>💾 Caching</b></summary>

```python
from orchestration.cache import LocalCache, cached

cache = LocalCache()
cache.set("key", "value", ttl=60)

@cached(ttl=300)
def expensive_llm_call(prompt):
    return llm.generate(prompt)
```

</details>

<details>
<summary><b>📊 Observability</b></summary>

```python
from orchestration.observability import MetricsCollector

metrics = MetricsCollector()
metrics.increment("steps_total", labels={"status": "success"})
metrics.observe("step_duration", 1.5)
```

</details>

## 📁 Project Structure

```
├── agenticom/              # CLI (antfarm-style)
│   ├── cli.py              # Commands
│   ├── dashboard.py        # Web UI
│   ├── state.py            # SQLite persistence
│   └── bundled_workflows/  # Ready-to-use workflows
│
├── orchestration/          # Core features
│   ├── guardrails.py       # Content filtering
│   ├── memory.py           # Persistent memory
│   ├── approval.py         # Approval gates
│   ├── cache.py            # Response caching
│   ├── observability.py    # Metrics
│   └── integrations/       # Ollama, Claude, GPT
│
├── skills/                 # Assistant skills
│   ├── agenticom-workflows/  # OpenClaw skill
│   └── agenticom-nanobot/    # Nanobot skill
│
└── docs/
    └── TEST_RESULTS.md     # Verified test evidence
```

## License

MIT

---

<p align="center">
  <strong>🐕 Your AI got coworkers.</strong><br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Bug</a>
</p>
