<div align="center">
  <img src="assets/mascot.png" alt="Agenticom" width="180">

  <h1>Agenticom</h1>

  <h3>Build an AI company that delivers expert work in hours — not weeks.</h3>

  <p>Spin up specialist AI teams. Get boardroom-ready deliverables.<br>Pay pennies instead of thousands.</p>

  <br>

  <p>
    <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/tests-849+%20passed-brightgreen" alt="Tests">
    <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status">
  </p>
</div>

---

## What would you do with an expert team available 24/7, for $5?

| Without Agenticom | With Agenticom |
|---|---|
| M&A due diligence: **4–8 weeks, $50K–200K** | M&A due diligence: **hours, ~$5 in API costs** |
| Patent landscape: **$500–1000/hr lawyer** | Patent landscape: **hours, ~$3 in API costs** |
| Security audit: **2–4 weeks, $20K–50K** | Security audit: **hours, ~$4 in API costs** |
| Grant proposal: **40–100 hrs of work** | Grant proposal: **afternoon, ~$2 in API costs** |
| Marketing strategy: **agency retainer $10K/mo** | Marketing strategy: **hours, ~$3 in API costs** |

---

## 🔥 What people actually use it for

**"Validate my startup idea."**
A researcher scouts the market, an analyst sizes the opportunity, a strategist designs the go-to-market, a writer produces the business plan. Done in an hour.

**"Write this grant proposal."**
Analyzes the RFP, synthesizes supporting literature, drafts the narrative, builds the budget justification. Submission-ready in an afternoon.

**"Audit our platform security."**
Produces a threat model, vulnerability map, remediation plan prioritized by risk, and a board-ready executive report. Same day.

**"Analyze acquisition target X."**
Five agents cover financial analysis, legal review, market assessment, technical audit, and investment recommendation with valuation range. In hours.

**"Build this feature."**
Plans the work, writes the code, verifies the logic, writes tests, reviews for bugs. Ready to ship.

---

## 🗣️ Just describe what you want — in plain English

No coding. No configuration. Just tell it what you need.

### Use with Claude (claude.ai)

**Step 1:** Install Agenticom once on your machine:
```bash
git clone https://github.com/wjlgatech/agentic-company.git
cd agentic-company && bash setup.sh
```

**Step 2:** Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Step 3:** Open [Claude.ai](https://claude.ai) and describe your task:

> *"Use agenticom due-diligence to analyze TechStartup Inc — $10M ARR, 40% growth, B2B SaaS in HR tech. Give me financial analysis, legal review, market assessment, and a GO/NO-GO recommendation with valuation range."*

> *"Use agenticom grant-proposal to write an NIH R01 for our lab's CRISPR sickle-cell research. Analyze the RFP requirements, synthesize the supporting literature, draft Specific Aims and Research Strategy, and build the budget justification."*

> *"Use agenticom marketing-campaign for my luxury Miami real estate agency targeting international buyers. Buyer personas, competitor audit, 30-day content calendar, influencer list, 90-day launch plan with KPIs."*

> *"Use agenticom security-assessment to audit our e-commerce platform — 100K daily transactions, 2M users' PII. Threat model, vulnerability scan, prioritized remediation plan, board-ready report."*

Claude runs a team of specialist AI agents and returns the full deliverable.

### Use with OpenClaw (WhatsApp · Telegram · Slack · Discord)

[OpenClaw](https://github.com/openclaw/openclaw) is a personal AI assistant on your favourite messaging app. After a one-time install, message it just like you'd message a colleague:

> *"Use agenticom churn-analysis — our SaaS churn is 6.5% monthly. Identify top-5 churn segments, build retention playbooks with ROI projections, draft a 90-day action plan."*

### Web dashboard

Prefer clicking to typing? Open the visual interface:

```bash
agenticom dashboard   # → http://localhost:8080
```

Pick a workflow, describe your task, and watch the agents work.

---

## 🖥️ CLI (for technical users)

### 1. Install

```bash
git clone https://github.com/wjlgatech/agentic-company.git
cd agentic-company && bash setup.sh
```

### 2. Pick an LLM backend

```bash
# Free (local, no API key)
ollama serve && ollama pull llama3.2

# Claude — best quality
export ANTHROPIC_API_KEY=sk-ant-...

# GPT
export OPENAI_API_KEY=sk-...
```

### 3. Run

```bash
# Preview without making any LLM calls
agenticom workflow run feature-dev "Add login button" --dry-run

# Run for real
agenticom workflow run due-diligence "Analyze acquisition target Acme Corp"
agenticom workflow run security-assessment "Audit our payment API"
agenticom workflow run grant-proposal "NIH R01 for CRISPR sickle-cell research"
```

| Command | Description |
|---------|-------------|
| `agenticom workflow list` | List all workflows |
| `agenticom workflow run <id> "<task>"` | Run a workflow |
| `agenticom workflow run <id> "<task>" --dry-run` | Preview without LLM calls |
| `agenticom workflow status <run-id>` | Check status |
| `agenticom workflow resume <run-id>` | Resume a failed run |
| `agenticom dashboard` | Open web UI |
| `agenticom stats` | Run statistics |

---

## 📋 Available expert teams

### Business & Enterprise

| Team (workflow) | What it delivers | Time saved |
|-----------------|-----------------|------------|
| `due-diligence` | M&A investment recommendation with full analysis | 4–6 weeks |
| `compliance-audit` | Audit-ready compliance report with remediation roadmap | 2–4 weeks |
| `patent-landscape` | Freedom-to-operate assessment + IP strategy | 3–6 weeks |
| `security-assessment` | Executive security report + prioritized fixes | 2–4 weeks |
| `churn-analysis` | Retention playbooks with ROI projections | 1–2 weeks |
| `grant-proposal` | Submission-ready proposal draft | 40–60 hours |
| `incident-postmortem` | Blameless post-mortem + action items | 4–8 hours |
| `marketing-campaign` | Full go-to-market strategy | 1–2 weeks |

### Software Development

| Team (workflow) | What it delivers |
|-----------------|-----------------|
| `feature-dev` | Plan → code → tests → review, end-to-end |
| `feature-dev-with-diagnostics` | + automated root cause analysis on failure |
| `autonomous-dev-loop` | Continuous improvement loop for long-running tasks |

---

## 🐍 Python API

```python
import asyncio
from orchestration import load_ready_workflow

team = load_ready_workflow('due-diligence.yaml')
result = asyncio.run(team.run("Analyze acquisition target Acme Corp, $15M ARR"))
print(result.final_output)
```

<details>
<summary>More Python examples</summary>

**Manual setup (more control):**
```python
from orchestration import load_workflow, auto_setup_executor

team = load_workflow('feature-dev.yaml')
executor = auto_setup_executor()
for agent in team.agents.values():
    agent.set_executor(lambda p, c: executor.execute(p, c))

result = asyncio.run(team.run("Add user authentication"))
```

**Build a custom team in code:**
```python
from orchestration.agents import TeamBuilder, AgentRole

team = (
    TeamBuilder("market-research")
    .add_agent(AgentRole.RESEARCHER, "You are a senior market analyst.")
    .add_agent(AgentRole.ANALYST, "You extract actionable insights from data.")
    .add_agent(AgentRole.DEVELOPER, "You synthesize findings into clear reports.")
    .build()
)
```

</details>

---

## 🔐 Production-grade by default

Every team comes with safety features you'd normally pay extra for:

- **Guardrails** — block sensitive content (PII, API keys) before it reaches the LLM
- **Memory** — agents remember context across runs and learn from past work
- **Approval gates** — require human sign-off on high-stakes actions
- **Caching** — skip redundant LLM calls, cut costs
- **Observability** — track every step, metric, and cost
- **MCP integration** — connect to live data: PubMed, Ahrefs, Similarweb, and more

<details>
<summary>Code examples for each feature</summary>

**Guardrails:**
```python
from orchestration.guardrails import ContentFilter, GuardrailPipeline

pipeline = GuardrailPipeline([ContentFilter(blocked_patterns=["password"])])
result = pipeline.check("My password is secret")  # result[0].passed = False
```

**Memory:**
```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("Client prefers executive summaries under 2 pages", tags=["preference"])
results = memory.search("summary format")
```

**Caching:**
```python
from orchestration.cache import cached

@cached(ttl=300)
def research(topic: str) -> str:
    return llm.generate(f"Research {topic}")
```

**Approval gates:**
```python
from orchestration.approval import HybridApprovalGate

gate = HybridApprovalGate(risk_threshold=0.7)
decision = gate.request_approval("Deploy to production", risk_score=0.85)
# Low risk → auto-approved. High risk → waits for human.
```

**MCP tool integration:**
```python
from orchestration.tools import MCPToolBridge

bridge = MCPToolBridge(graceful_mode=True)
result = await bridge.execute("web_search", query="AI regulation 2025")
```

</details>

---

## 📢 News

> **Format:** What it means for you → How it works → What was built

---

### 2026-02-19 — Your AI team gets smarter every time it runs

Every run is now a lesson. The first time a planner produces vague output, the system notices. By run five it proposes a sharper prompt. By run twenty the whole team is measurably better — without you touching a config file.

> **Tech:** Self-improvement loop — SMARC quality scoring on every step output → per-agent performance tracking → capability gap detection → targeted prompt patch proposals → human-in-the-loop approval or auto-apply.

<details>
<summary>Implementation details</summary>

- **`orchestration/self_improvement/`** — new module vendoring four classes from `wjlgatech/self-optimization`: `ResultsVerificationFramework` (SMARC), `MultiAgentPerformanceOptimizer`, `RecursiveSelfImprovementProtocol`, `AntiIdlingSystem`
- **Zero hot-path impact** — recording happens via `asyncio.create_task()` after `team.run()` returns
- **`PromptVersionStore`** — SQLite-backed versioned personas with full rollback chain
- **`PromptEvolver`** — heuristic suffix rules (always works) + optional LLM full-persona rewrite
- **`agenticom feedback`** CLI — `list-patches`, `approve-patch`, `reject-patch`, `rollback`, `rate-run`, `status`
- **`feature-dev.yaml`** — opt-in via `metadata.self_improve: true`
- 51 new tests · 900 total passing

</details>

---

### 2026-02-14 — Ship with confidence: 900 tests guard every change

Refactor boldly. The test suite catches regressions before you do — covering guardrails, memory backends, the YAML parser, all 13 bundled workflows, the REST API, and the CLI end-to-end.

> **Tech:** Comprehensive pytest suite with async support, integration-test isolation, and Playwright-conditional browser tests — enforced in CI across Python 3.10 / 3.11 / 3.12.

<details>
<summary>Implementation details</summary>

- **849 → 900 tests** across three rounds of coverage expansion
- `asyncio_mode = "auto"` — async test functions work without decorators
- `@pytest.mark.integration` guards tests requiring live API keys; CI runs with `-m "not integration"`
- `tests/conftest.py` — `collect_ignore` for 6 script-style files that aren't pytest suites
- CodeQL + coverage jobs added to the CI matrix

</details>

---

### 2026-02-13 — Production-grade CI: every PR is gated before it merges

No more "it worked on my machine." Lint, types, tests on three Python versions, coverage, and security scanning all run automatically. Main branch is fully protected — no direct pushes, no bypassing checks.

> **Tech:** GitHub Actions matrix CI (lint-and-type-check, test ×3 Pythons, coverage, CodeQL) + branch protection (1 reviewer, 5 required checks, `enforce_admins: true`).

<details>
<summary>Implementation details</summary>

- `.github/workflows/ci.yml` — ruff + mypy + pytest in parallel across py3.10/3.11/3.12
- `black>=24.0` pinned; must run after `ruff --fix` to avoid conflicts
- `mypy` config: `disallow_untyped_defs=false`, `warn_return_any=false` (40 pre-existing modules carry `ignore_errors=true`)
- Pre-commit hook (`scripts/check_root_clutter.py`) enforces file-organisation rules at commit time

</details>

---

### 2026-02-11 — Catch bugs before users do: automated browser diagnostics

The verifier agent used to report "it looks wrong." Now it shows you a screenshot, the console error, and an AI-generated root-cause hypothesis — all captured automatically during the workflow run.

> **Tech:** Playwright browser automation captures screenshots + console logs + network requests after each step; a meta-analysis LLM layer identifies root causes and proposes targeted fixes; a criteria builder interviews you to sharpen acceptance criteria.

<details>
<summary>Implementation details</summary>

- **`orchestration/diagnostics/`** — `PlaywrightCapture`, `MetaAnalyzer`, `CriteriaBuilder`, `IterationMonitor`, `DiagnosticsIntegrator`
- `agenticom test-diagnostics <url>` — run browser automation from the CLI
- `agenticom build-criteria "<task>"` — interactive Q&A → structured success criteria JSON
- `@pytest.mark.skipif(not check_playwright_installation(), ...)` guards browser tests

</details>

---

### 2026-02-11 — Connect to live data: MCP tool integrations

Your agents can now query PubMed, Ahrefs, Similarweb, and any MCP server — not just reason about what the data might say, but actually retrieve it mid-workflow.

> **Tech:** `MCPToolBridge` routes workflow tool references to registered MCP servers via `MCPToolRegistry`; `PromptEngineer` + `SmartRefiner` refine task descriptions into coherent multi-turn prompts before execution begins.

<details>
<summary>Implementation details</summary>

- **`orchestration/tools/`** — `mcp_bridge.py`, `registry.py`, `prompt_engineer.py`, `intent_refiner.py`, `smart_refiner.py`, `hybrid_refiner.py`
- `SmartRefiner` — multi-turn interview loop that synthesises a coherent final prompt from user answers
- `ConversationalRefiner` — single-pass intent clarification for simpler cases
- Graceful-mode flag: tools degrade silently when MCP server is unavailable

</details>

---

### 2026-02-11 — From idea to deliverable in hours, not weeks

Five specialist agents — planner, developer, verifier, tester, reviewer — collaborate on a shared task with cross-verification at every handoff. Each agent sees only what it needs; hallucinations from previous steps can't contaminate the next.

> **Tech:** "Ralph Loop" pattern — fresh `AgentContext` per step with template substitution (`{{step_outputs.X}}`); loopback on failure; guardrails, memory, and approval gates composable per workflow; 13 bundled YAML workflows ready to run.

<details>
<summary>Implementation details</summary>

- **`orchestration/agents/`** — `AgentTeam`, `TeamBuilder`, `AgentRole` enum, specialized agents (Planner/Developer/Verifier/Tester/Reviewer/Researcher/Writer/Analyst)
- **`orchestration/workflows/`** — `WorkflowParser` (YAML → `AgentTeam`), template engine
- **`agenticom/state.py`** — SQLite persistence (`~/.agenticom/state.db`) for all run state
- **`orchestration/integrations/unified.py`** — `UnifiedExecutor` routes to OpenClaw (Anthropic), Nanobot (OpenAI), or Ollama; `auto_setup_executor()` picks the best available backend
- 13 bundled workflows: `feature-dev`, `feature-dev-with-diagnostics`, `feature-dev-with-loopback`, `feature-dev-llm-recovery`, `autonomous-dev-loop`, `marketing-campaign`, `due-diligence`, `compliance-audit`, `patent-landscape`, `security-assessment`, `churn-analysis`, `grant-proposal`, `incident-postmortem`

</details>

---

## License

MIT — use it, fork it, build on it.

---

<p align="center">
  <strong>🐕 Your AI company is open for business.</strong><br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star on GitHub</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Report an issue</a>
</p>
