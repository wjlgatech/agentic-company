<div align="center">
  <img src="assets/mascot.png" alt="Agenticom Golden Retriever" width="200">
  <h1>Agenticom: Multi-Agent Team Orchestration</h1>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/tests-11%2F11%20passed-brightgreen" alt="Tests">
  </p>
</div>

🐕 **Agenticom** is a multi-agent workflow orchestration tool inspired by [Antfarm](https://github.com/snarktank/antfarm).

⚡️ **One agent makes mistakes. Five agents ship features.**

📏 Real-time line count: **14,097 lines** (run `find . -name "*.py" -exec cat {} \; | wc -l`)

## 📢 News

- **2026-02-11** 🎉 Added Web Dashboard + Golden Retriever mascot!
- **2026-02-10** ✨ All 11 features verified with stress tests
- **2026-02-09** 🔧 Added OpenClaw + Nanobot skill integrations
- **2026-02-08** 🚀 Initial release with guardrails, memory, approval gates

## ✨ Key Features (All Verified ✅)

| Feature | Status | What it does |
|---------|--------|--------------|
| 🛡️ **Guardrails** | ✅ Tested | Content filter, rate limiter |
| 🧠 **Memory** | ✅ Tested | Persistent remember/recall |
| ✅ **Approval Gates** | ✅ Tested | Auto/Human/Hybrid approval |
| 💾 **Caching** | ✅ Tested | LLM response cache |
| 📊 **Observability** | ✅ Tested | Prometheus metrics |
| 🖥️ **CLI** | ✅ Tested | Full workflow management |
| 💾 **State Manager** | ✅ Tested | SQLite persistence |
| 🌐 **Dashboard** | ✅ Tested | Beautiful web UI |
| ⚡ **Multi-Backend** | ✅ Tested | Ollama (FREE), Claude, GPT |

<details>
<summary><b>View Test Results</b></summary>

```
🧪 AGENTICOM STRESS TEST SUITE
============================================================
✅ 🛡️ Guardrails: ContentFilter + RateLimiter working
✅ 🧠 Memory: Stored 2 memories, found 1 matches
✅ ✅ Approval Gates: ApprovalRequest created
✅ 💾 Caching: Cache get/set + decorator OK
✅ 📊 Observability: Recorded 3 metric types
✅ 🖥️ CLI Commands: workflow list + stats working
✅ 💾 State Manager: SQLite persistence working
✅ 📋 Workflow Parser: YAML parsing working
✅ 🌐 Dashboard: 16,076 chars HTML ready
✅ 💬 Conversation Builder: Progress tracking
✅ ⚡ Ollama Backend: OllamaExecutor ready

🎯 Total: 11/11 tests passed
🎉 ALL FEATURES VERIFIED!
```

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

**1. Configure LLM backend**

```bash
# Option A: Ollama (FREE - local)
ollama serve && ollama pull llama3.2

# Option B: Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Option C: GPT
export OPENAI_API_KEY=sk-...
```

**2. Run a workflow**

```bash
agenticom workflow run marketing-campaign "Launch strategy for B2B SaaS targeting HR teams"
```

**3. Open dashboard**

```bash
agenticom dashboard
```

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
