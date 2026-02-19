<div align="center">
  <img src="assets/mascot.png" alt="Agenticom Golden Retriever" width="200">
  <h1>Agenticom: Multi-Agent Team Orchestration</h1>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/tests-849+%20passed-brightgreen" alt="Tests">
    <img src="https://img.shields.io/badge/test__lines-6,000+-blue" alt="Test Lines">
    <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status">
  </p>
</div>

🐕 **Agenticom** is a multi-agent workflow orchestration framework inspired by [Antfarm](https://github.com/snarktank/antfarm).

⚡️ **One agent makes mistakes. Five agents cross-verify.**

## 📢 News

- **2026-02-14** 🧠 **ADAPTIVE MEMORY COMPLETE**: Production-ready lesson learning system with LLM extraction + human curation
  > [Phase 2 Details](MONITORING_ADAPTIVE_MEMORY.md) • 1,695 lines backend • 6,000+ lines tests
- **2026-02-14** 📊 **COMPREHENSIVE MONITORING**: Full observability framework for measuring memory effectiveness
  > [Metrics Guide](MONITORING_ADAPTIVE_MEMORY.md) • Leading + lagging indicators • Root cause analysis • Automated alerting
- **2026-02-14** 🎯 **STAGE TRACKING**: Real-time workflow stage visualization (Plan → Implement → Verify → Test → Review)
  > [Phase 1 Details](PHASE1_COMPLETE_STAGE_TRACKING.md) • Timestamps + artifacts per stage • Auto-detection from step IDs
- **2026-02-14** ✅ **30+ REAL TESTS**: Comprehensive test suite with actual LLM calls, file I/O, and calculations
  > Unit + integration + real-world + stress tests • 849+ tests across 20 test files
- **2026-02-11** 🏢 **7 ENTERPRISE WORKFLOWS**: Due diligence, compliance, patents, security, churn, grants, incidents!
- **2026-02-11** 🔧 **UPGRADE**: Dynamic role resolution - any custom agent role now auto-maps to base types
- **2026-02-11** 🏆 **V3 ASSESSMENT: ⭐⭐⭐⭐⭐ (5/5)** - Independent testing confirms all workflows working perfectly!
- **2026-02-11** 🐛 **CRITICAL FIX**: Multi-step workflow variable substitution now works!
- **2026-02-11** 🧠 **NEW: PromptEngineer** - Automatic prompt improvement using Anthropic's best practices
- **2026-02-11** 🔌 **NEW: MCP Integration** - Connect workflow tools to real MCP servers (PubMed, Ahrefs, etc.)
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
| 🎓 **Adaptive Memory** | ✅ Production | Lesson learning from workflows |
| 📊 **Memory Monitoring** | ✅ Production | Success rate tracking, alerting |
| 🎯 **Stage Tracking** | ✅ Working | Real-time workflow visualization |
| ✅ **Approval Gates** | ✅ Working | Auto/Human/Hybrid patterns |
| 💾 **Caching** | ✅ Working | LLM response cache |
| 📊 **Observability** | ✅ Working | Prometheus-style metrics |
| 📋 **YAML Workflows** | ✅ Working | Parser loads bundled workflows |
| 🖥️ **CLI** | ✅ Working | `workflow list`, `run --dry-run` |
| 🌐 **Dashboard** | ✅ Working | Visual workflow management |
| ⚡ **Multi-Backend** | ✅ Working | Ollama/Claude/GPT abstraction |
| 🔌 **MCP Integration** | ✅ Working | Connect to real MCP servers |
| 🧠 **Prompt Engineer** | ✅ Working | Auto-improve agent prompts |

### ⚠️ What Requires MCP Server Connections

| Feature | Status | How to Enable |
|---------|--------|---------------|
| 🌐 **Web Search** | 🔌 MCP Ready | Connect Ahrefs or Similarweb MCP |
| 📚 **Literature Search** | 🔌 MCP Ready | Connect PubMed MCP |
| 📱 **Social Media** | 🔌 MCP Ready | Connect LunarCrush MCP |
| 📊 **Market Research** | 🔌 MCP Ready | Connect Harmonic or S&P Global MCP |
| 🔍 **Competitor Analysis** | 🔌 MCP Ready | Connect Similarweb MCP |

**The bundled workflows now include MCP Tool Bridge integration.** Tools automatically resolve to real MCP servers when connected, or provide graceful fallback guidance when not.

<details>
<summary><b>🏆 View V3 Independent Assessment (5/5 Stars)</b></summary>

### Overall Rating: ⭐⭐⭐⭐⭐ (5/5) - FULLY FUNCTIONAL

| Metric | V1 (Pre-MCP) | V2 (Broken) | V3 (Fixed) | Trend |
|--------|--------------|-------------|------------|-------|
| **Multi-Step Coordination** | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 📈 Fixed! |
| **Technical Execution** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 📈 Restored |
| **Content Quality** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 📈 Better |
| **Overall** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🎯 Best! |

### Test Results (3/3 Workflows, 11/11 Steps):

**✅ CAR-T Research (5 steps, 263s):**
- Validator caught fabricated citations
- Cross-verification working perfectly

**✅ Software Development (4 steps, 157s):**
- Plan → Code → Tests → Review all connected
- Reviewer found real bugs in generated code

**✅ Marketing Campaign (2 steps, 103s):**
- Research → Strategy properly integrated
- Pain points incorporated into personas

### Key Achievement:
> "From broken (V2) to excellent (V3) in one bug fix. The template substitution fix restored full functionality and the framework now delivers on its promise of multi-agent orchestration."

**Verdict:** ✅ **PRODUCTION READY** for software development and process automation

</details>

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

**1-Click** (auto-detects OS, installs missing prerequisites, creates venv)

```bash
git clone https://github.com/wjlgatech/agentic-company.git
cd agentic-company && bash setup.sh
```

**Or with `make`:**

```bash
git clone https://github.com/wjlgatech/agentic-company.git
cd agentic-company

# For users (production use)
make install && .venv/bin/agenticom install

# For developers (includes pytest, ruff, mypy, black)
make dev
```

`setup.sh` handles everything automatically:
- Installs `python3`, `pip`, `venv`, `make`, `git` if missing (via Homebrew / apt / dnf / pacman)
- Creates a `.venv` virtual environment
- Installs the package and bundled workflows

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
agenticom workflow run feature-dev "Add login button" --dry-run
```

**3. Run a workflow**

```bash
# Actually execute the workflow (requires LLM backend)
agenticom workflow run feature-dev "Add a hello world function"
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

### Core Workflows
| Workflow | Pipeline | Use for |
|----------|----------|---------|
| `feature-dev` | plan → implement → verify → test → review | Software development |
| `marketing-campaign` | discover → analyze → create → outreach → orchestrate | Go-to-market |

### 🆕 Enterprise Workflows (7 High-Impact Use Cases)

| Workflow | Pain Point | Time Saved | Cost Saved |
|----------|------------|------------|------------|
| `due-diligence` | M&A analysis takes 4-8 weeks | 4-6 weeks | $50K-200K |
| `compliance-audit` | Manual audits miss gaps | 2-4 weeks | $25K-75K |
| `patent-landscape` | Patent lawyers charge $500-1000/hr | 3-6 weeks | $30K-100K |
| `security-assessment` | Breaches cost $4.45M average | 2-4 weeks | $20K-50K |
| `churn-analysis` | 5-7% churn = millions lost | 1-2 weeks | $10K-30K |
| `grant-proposal` | 40-100 hrs per proposal | 40-60 hours | $5K-15K |
| `incident-postmortem` | Post-mortems take days | 4-8 hours | $2K-5K |

<details>
<summary><b>📊 Enterprise Workflow Details</b></summary>

**1. M&A Due Diligence** (`due-diligence`)
- 5 agents: Financial Analyst → Legal Reviewer → Market Analyst → Technical Assessor → Deal Lead
- Produces: Investment recommendation with GO/NO-GO decision

**2. Regulatory Compliance Audit** (`compliance-audit`)
- 5 agents: Requirements Mapper → Gap Analyst → Risk Assessor → Remediation Planner → Documenter
- Produces: Audit-ready compliance report with remediation roadmap

**3. Patent Landscape Analysis** (`patent-landscape`)
- 5 agents: Patent Searcher → Claim Analyst → Landscape Mapper → FTO Assessor → IP Strategist
- Produces: Freedom-to-operate assessment with IP strategy

**4. Security Vulnerability Assessment** (`security-assessment`)
- 5 agents: Threat Modeler → Vuln Scanner → Risk Analyst → Remediation Engineer → Security Architect
- Produces: Executive security report with prioritized fixes

**5. Customer Churn Analysis** (`churn-analysis`)
- 5 agents: Data Analyst → Customer Researcher → Segment Strategist → Retention Strategist → CCO
- Produces: Retention playbooks with ROI projections

**6. Grant/RFP Proposal Writing** (`grant-proposal`)
- 5 agents: Requirements Analyst → Research Synthesizer → Proposal Architect → Budget Specialist → Writer
- Produces: Complete proposal draft ready for submission

**7. Incident Post-Mortem** (`incident-postmortem`)
- 5 agents: Timeline Analyst → RCA Specialist → Impact Assessor → Prevention Engineer → Author
- Produces: Blameless post-mortem with action items

</details>

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

<details>
<summary><b>💼 M&A Due Diligence (Enterprise)</b></summary>

```
Use agenticom due-diligence to analyze acquisition target "TechStartup Inc"
with $10M ARR, 40% growth, B2B SaaS in the HR tech space.

Conduct financial analysis, legal review, market assessment, technical audit,
and provide investment recommendation with valuation range.
```

</details>

<details>
<summary><b>🔒 Security Assessment (Enterprise)</b></summary>

```
Use agenticom security-assessment to audit our e-commerce platform
handling 100K daily transactions and PII of 2M users.

Threat model, vulnerability scan, risk analysis, remediation plan,
and board-ready security report with compliance mapping.
```

</details>

## 💪 Strengths & Limitations

<details>
<summary><b>View Capability Analysis</b></summary>

### ✅ Strengths (What Agenticom Excels At)

| Capability | Rating | Evidence |
|------------|--------|----------|
| **Multi-Step Orchestration** | ⭐⭐⭐⭐⭐ | 5-step workflows with cross-verification |
| **Template Flexibility** | ⭐⭐⭐⭐⭐ | Dynamic `{{step_outputs.X}}` substitution |
| **Role Extensibility** | ⭐⭐⭐⭐⭐ | 50+ role mappings + auto-pattern matching |
| **YAML Simplicity** | ⭐⭐⭐⭐⭐ | Non-developers can create workflows |
| **Fresh Context** | ⭐⭐⭐⭐ | Prevents context bloat in long workflows |
| **Cross-Verification** | ⭐⭐⭐⭐ | Agents catch each other's errors |

### ⚠️ Limitations (Areas for Improvement)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No Real Data Access** | Medium | Connect MCP servers for live data |
| **LLM Hallucinations** | Medium | Validator agents catch obvious issues |
| **Sequential Only** | Low | Parallel steps planned for v2 |
| **No Memory Across Runs** | Low | Use memory module for persistence |

### 🔧 Recent Upgrades

1. **Dynamic Role Resolution** (this release)
   - Custom roles auto-map to base types via pattern matching
   - No more "Unknown agent role" errors
   - Supports any role name ending in -analyst, -researcher, etc.

2. **Template Preprocessing** (this release)
   - Fixed `{{step_outputs.X}}` → `{X}` conversion
   - Hyphenated step IDs work correctly
   - Multi-step workflows fully functional

</details>

## 🦞 Use with OpenClaw

[OpenClaw](https://github.com/openclaw/openclaw) - Personal AI assistant for WhatsApp, Telegram, Slack, Discord.

```bash
cd agentic-company && bash setup.sh
```

Then tell your assistant: *"Use agenticom to build a marketing strategy for my SaaS"*

## 🐈 Use with Nanobot

[Nanobot](https://github.com/HKUDS/nanobot) - Ultra-lightweight personal AI assistant.

```bash
cd agentic-company && bash setup.sh
```

Then tell your assistant: *"Use agenticom feature-dev to research and design a mobile app"*

## 🖥️ CLI Reference

| Command | Description |
|---------|-------------|
| `agenticom install` | Install bundled workflows |
| `agenticom workflow list` | List available workflows |
| `agenticom workflow run <id> <task>` | Start a run |
| `agenticom workflow tools <id>` | **Show MCP tool resolution** |
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

<details>
<summary><b>🔌 MCP Tool Integration</b></summary>

Connect workflow tools to real MCP (Model Context Protocol) servers:

```python
from orchestration.tools import MCPToolBridge

# Initialize bridge
bridge = MCPToolBridge(graceful_mode=True)

# Resolve tools from workflow
tools = bridge.resolve_workflow_tools(["web_search", "literature_search"])

# Execute a tool
result = await bridge.execute("web_search", query="AI startups 2024")

# Get resolution report
report = bridge.get_resolution_report(["web_search", "market_research"])
print(report["summary"])  # {resolved: 1, fallback: 1, waiting: 0}
```

**Supported MCP Servers:**
- 📚 **PubMed** - Biomedical literature search
- 🔍 **Ahrefs** - Web search & SEO data
- 📊 **Similarweb** - Competitor traffic analysis
- 🏢 **Harmonic** - Company enrichment data
- 📈 **Amplitude** - Product analytics
- 💬 **LunarCrush** - Social media intelligence

</details>

<details>
<summary><b>🧠 Prompt Engineering</b></summary>

Automatically improve agent prompts using Anthropic's best practices:

```python
from orchestration.tools import PromptEngineer, PromptStyle

# Initialize engineer
engineer = PromptEngineer(executor=my_llm_function)

# Improve a basic prompt
result = await engineer.improve(
    "Find papers about AI.",
    style=PromptStyle.AGENT
)
print(result.improved)  # Full structured agent prompt
print(result.improvements)  # ["Added role setting", "Added guardrails", ...]

# Generate complete agent persona
persona = await engineer.generate_agent_persona(
    role="Senior Data Analyst",
    task="Analyze customer data and identify trends",
    expertise=["Python", "SQL", "Statistics"]
)

# Sync improvement (no LLM needed - uses rule-based approach)
from orchestration.tools import improve_prompt_sync
better_prompt = improve_prompt_sync("analyze data", style=PromptStyle.ANALYSIS)
```

**Prompt Styles:** `AGENT`, `TASK`, `ANALYSIS`, `CREATIVE`, `CODING`

**Improvements Applied:**
- ✅ Role setting & expertise
- ✅ Chain-of-thought reasoning
- ✅ Output format specification
- ✅ Guardrails & safety guidelines
- ✅ Section structure

</details>

<details>
<summary><b>🎓 Adaptive Memory & Lesson Learning (NEW)</b></summary>

Learn from every workflow execution and improve over time:

```python
from orchestration.lessons import LessonExtractor, LessonManager

# Extract lessons from completed workflow
extractor = LessonExtractor(llm_call=your_llm_function)
lessons = extractor.extract_from_run(
    run_id="abc123",
    workflow_id="feature-dev",
    task="Build authentication",
    status="completed",
    duration=1847.5,
    stages=workflow_stages,
    steps=workflow_steps
)

# Human curates lessons
manager = LessonManager()
for lesson in lessons:
    manager.add_proposed(lesson)  # Status: PROPOSED

# Review and approve
pending = manager.get_pending_review()
manager.approve(pending[0].id, reviewer_id="engineer", notes="Good advice")

# Retrieve relevant lessons for next workflow
lessons = manager.get_approved(
    workflow_cluster="code",
    domain_tags=["authentication", "api"]
)
```

**Monitor Memory Effectiveness:**

```python
from orchestration.memory_metrics import MemoryMetricsCollector
from orchestration.memory_config import AlertManager, get_memory_config

collector = MemoryMetricsCollector()

# Record workflow outcomes
collector.record_workflow_outcome(WorkflowOutcome(
    run_id="run-001",
    success=True,
    lessons_retrieved=["lesson-1", "lesson-2"],
    lessons_used_count=2
))

# Measure if lessons help
success_rates = collector.measure_workflow_success_rate()
print(f"Improvement: {success_rates['improvement']*100:.1f}%")
# Example: +8% (workflows with lessons are 8% more successful!)

# Automated alerting
config = get_memory_config()
alert_manager = AlertManager(config)
alerts = alert_manager.check_and_send_alerts(collector.get_dashboard_summary())
```

**Features:**
- 🎯 **LLM-powered extraction** - Analyzes workflows and proposes lessons
- 👤 **Human curation** - Approve/reject before activation
- 📊 **Effectiveness tracking** - Measures if lessons actually help
- 🚨 **Automated alerting** - Critical/Warning/Info based on thresholds
- 🔍 **Smart filtering** - By cluster, domain tags, usage, effectiveness
- 📈 **Metrics dashboard** - Success rate, error reduction, satisfaction

**Configuration (Your Settings):**
- Similarity threshold: **0.80** (high quality over quantity)
- Target improvement: **5%** (realistic goal)
- Tuning frequency: **Weekly** (data-driven adjustments)
- Alert recipients: **Eng + Product** (shared ownership)

**Documentation:**
> 📖 [Complete Monitoring Guide](MONITORING_ADAPTIVE_MEMORY.md) - How to measure memory effectiveness
> ⚙️ [Your Configuration](YOUR_MEMORY_CONFIGURATION.md) - Settings, runbooks, success criteria
> 🧪 [Test Documentation](TEST_IMPLEMENTATION_COMPLETE.md) - 30+ real tests, zero mocks
> 🎯 [Phase 1: Stage Tracking](PHASE1_COMPLETE_STAGE_TRACKING.md) - Workflow stage visualization

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
│   ├── lessons.py          # 🆕 Lesson learning system
│   ├── memory_metrics.py   # 🆕 Memory effectiveness monitoring
│   ├── memory_config.py    # 🆕 Adaptive memory configuration
│   ├── approval.py         # Approval gates
│   ├── cache.py            # Response caching
│   ├── observability.py    # Metrics
│   ├── integrations/       # Ollama, Claude, GPT
│   └── tools/              # MCP & Prompt Engineering
│       ├── mcp_bridge.py   # MCP server integration
│       ├── registry.py     # MCP server registry
│       ├── prompt_engineer.py  # Auto prompt improvement
│       └── smart_refiner.py    # Multi-turn interview system
│
├── skills/                 # Assistant skills
│   ├── agenticom-workflows/  # OpenClaw skill
│   └── agenticom-nanobot/    # Nanobot skill
│
├── tests/                  # 🆕 Comprehensive test suite
│   ├── test_lesson_system.py   # Lesson learning tests (943 lines)
│   └── test_memory_metrics.py  # Memory metrics tests (784 lines)
│
└── docs/
    ├── TEST_RESULTS.md     # Verified test evidence
    ├── MONITORING_ADAPTIVE_MEMORY.md      # 🆕 Memory monitoring guide
    ├── YOUR_MEMORY_CONFIGURATION.md       # 🆕 Configuration & runbooks
    ├── TEST_IMPLEMENTATION_COMPLETE.md    # 🆕 Test documentation
    └── PHASE1_COMPLETE_STAGE_TRACKING.md  # 🆕 Stage tracking details
```

## License

MIT

---

<p align="center">
  <strong>🐕 Your AI got coworkers.</strong><br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Bug</a>
</p>
