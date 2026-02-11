<p align="center">
  <img src="assets/icons/agenticom-golden.svg" width="180" alt="Agenticom"/>
</p>

<h1 align="center">AGENTICOM</h1>

<p align="center">
  <strong>Production-Grade Multi-Agent Orchestration</strong><br>
  <em>Everything antfarm does, plus guardrails, memory, approval gates, observability, and 3 LLM backends.</em>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-why-agenticom">Why Agenticom</a> •
  <a href="#-verified-features">Features</a> •
  <a href="#-multi-backend">Backends</a>
</p>

---

## Quick Start

```bash
pip install agentic-company
agenticom install
agenticom workflow run feature-dev "Add user authentication with JWT"
```

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
```

**30 seconds. 5 agents. Cross-verification built in.**

---

## Why Agenticom?

We love [antfarm](https://github.com/jlowin/antfarm). We copied its pattern. Then we added everything else.

| Feature | Antfarm | Agenticom |
|---------|---------|-----------|
| YAML workflows | ✅ | ✅ |
| SQLite state | ✅ | ✅ |
| CLI commands | ✅ | ✅ |
| Fresh context/step | ✅ | ✅ |
| **Guardrails** | ❌ | ✅ Content filter, rate limiter |
| **Memory** | ❌ | ✅ Persistent remember/recall |
| **Approval Gates** | ❌ | ✅ Auto/Human/Hybrid |
| **Observability** | ❌ | ✅ Metrics, Prometheus, tracing |
| **Multi-Backend** | ❌ | ✅ Ollama (FREE), Claude, GPT |
| **REST API** | ❌ | ✅ 27 endpoints |
| **Caching** | ❌ | ✅ LLM response cache |
| **Security** | ❌ | ✅ JWT, audit log, sanitization |
| **Language** | TypeScript | Python |

**Antfarm is a CLI. Agenticom is a platform.**

---

## Verified Features

Every feature below has been **tested and verified working**:

### 1. Guardrails
```python
from orchestration.guardrails import ContentFilter, RateLimiter, GuardrailPipeline

pipeline = GuardrailPipeline([
    ContentFilter(blocked_patterns=["password", "api_key"]),
    RateLimiter(max_requests=100, window_seconds=60)
])

result = pipeline.check("Send me your password")
# result.passed = False, result.reason = "Blocked pattern: password"
```

### 2. Persistent Memory
```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("User prefers Python over JavaScript", tags=["preferences"])
memory.remember("Project deadline is March 15", tags=["schedule"])

# Later...
results = memory.recall("what language does user prefer", limit=3)
# Returns relevant memories with similarity scores
```

### 3. Approval Gates
```python
from orchestration.approval import AutoApprovalGate, HumanApprovalGate, HybridApprovalGate

# Auto-approve low-risk actions
auto_gate = AutoApprovalGate()

# Require human approval for high-risk
human_gate = HumanApprovalGate(timeout_seconds=300)

# Hybrid: auto for low-risk, human for high-risk
hybrid_gate = HybridApprovalGate(risk_threshold=0.7)
```

### 4. Observability
```python
from orchestration.observability import MetricsCollector, Tracer

metrics = MetricsCollector()
metrics.increment("workflow_runs")
metrics.histogram("step_duration_seconds", 1.5)

# Prometheus endpoint: GET /metrics
# Returns: workflow_runs_total 42
```

### 5. Multi-Backend (FREE option!)
```python
from orchestration.integrations import (
    OllamaExecutor,      # FREE - runs locally
    OpenClawExecutor,    # Claude API
    NanobotExecutor,     # OpenAI API
    auto_setup_executor  # Auto-detects best available
)

# Use FREE local LLM (no API key needed!)
executor = OllamaExecutor(model="llama3.2")
result = executor.execute_sync("Write a Python function")

# Or auto-detect: tries Ollama → Claude → GPT
executor = auto_setup_executor()
```

### 6. REST API (27 endpoints)
```python
from orchestration.api import app
import uvicorn

# Endpoints include:
# POST /api/workflows/run
# GET  /api/workflows/{id}/status
# POST /api/chat
# GET  /api/memory/recall
# GET  /api/approvals/pending
# GET  /metrics (Prometheus)

uvicorn.run(app, port=8000)
```

### 7. Agent Pipelines
```python
from orchestration.pipeline import Pipeline, PipelineBuilder, LLMStep, ParallelStep

# Sequential pipeline
pipeline = (PipelineBuilder()
    .add_step(LLMStep("plan", "Create a plan for: {task}"))
    .add_step(LLMStep("implement", "Implement: {plan}"))
    .add_step(LLMStep("review", "Review: {implementation}"))
    .build())

# Parallel execution
parallel = ParallelStep([
    LLMStep("research", "Research: {topic}"),
    LLMStep("outline", "Outline: {topic}")
])
```

### 8. Response Caching
```python
from orchestration.cache import LocalCache, cached

cache = LocalCache()

@cached(cache, ttl=3600)
def expensive_llm_call(prompt):
    return executor.execute_sync(prompt)

# First call: hits LLM
result1 = expensive_llm_call("Explain recursion")

# Second call: returns cached (FREE!)
result2 = expensive_llm_call("Explain recursion")
```

### 9. Security
```python
from orchestration.security import (
    create_jwt_token,
    verify_jwt_token,
    AuditLogger,
    sanitize_input
)

# JWT authentication
token = create_jwt_token({"user_id": "123", "role": "admin"})
payload = verify_jwt_token(token)

# Audit logging
audit = AuditLogger()
audit.log("workflow_executed", user="alice", workflow="feature-dev")

# Input sanitization
clean = sanitize_input(user_input)  # Removes injection attempts
```

### 10. Agent System
```python
from orchestration.agents import (
    Agent, AgentRole, AgentTeam,
    PlannerAgent, DeveloperAgent, VerifierAgent, TesterAgent, ReviewerAgent
)

# Pre-built specialized agents
team = AgentTeam(
    agents=[
        PlannerAgent(),
        DeveloperAgent(),
        VerifierAgent(),
        TesterAgent(),
        ReviewerAgent()
    ]
)
```

### 11. No-Code Conversation Builder
```python
from orchestration.conversation import ConversationBuilder

builder = ConversationBuilder()
# Guides users through workflow creation via conversation
# No code required - just answer questions
```

### 12. CLI
```bash
agenticom install                    # Install bundled workflows
agenticom workflow list              # List all workflows
agenticom workflow run <id> <task>   # Run a workflow
agenticom workflow status <run-id>   # Check status
agenticom workflow resume <run-id>   # Resume failed run
agenticom stats                      # Show statistics
agenticom uninstall --force          # Remove all data
```

---

## Bundled Workflows

| Workflow | Agents | Steps | Use Case |
|----------|--------|-------|----------|
| `feature-dev` | 5 | 5 | Planner → Developer → Verifier → Tester → Reviewer |
| `marketing-campaign` | 5 | 5 | SocialIntel → Competitor → Content → Community → Lead |

```bash
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

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         AGENTICOM                               │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  GUARDRAILS  │  │    MEMORY    │  │   APPROVAL   │         │
│  │ ContentFilter│  │ LocalMemory  │  │ Auto/Human/  │         │
│  │ RateLimiter  │  │ remember()   │  │   Hybrid     │         │
│  └──────────────┘  │ recall()     │  └──────────────┘         │
│                    └──────────────┘                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ OBSERVABILITY│  │    CACHE     │  │   SECURITY   │         │
│  │ Metrics      │  │ LocalCache   │  │ JWT Auth     │         │
│  │ Prometheus   │  │ @cached      │  │ AuditLog     │         │
│  │ Tracing      │  │ TTL support  │  │ Sanitization │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
├────────────────────────────────────────────────────────────────┤
│                      AGENT PIPELINE                             │
│  ┌─────────┐ → ┌─────────┐ → ┌─────────┐ → ┌─────────┐        │
│  │ Planner │   │Developer│   │Verifier │   │ Tester  │        │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘        │
│                (Cross-agent verification)                       │
├────────────────────────────────────────────────────────────────┤
│                      MULTI-BACKEND                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   OLLAMA     │  │   OPENCLAW   │  │   NANOBOT    │         │
│  │  (FREE!)     │  │   (Claude)   │  │    (GPT)     │         │
│  │  Local LLM   │  │  Cloud API   │  │  Cloud API   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
├────────────────────────────────────────────────────────────────┤
│  REST API (27 endpoints)  │  CLI  │  Python API                │
└────────────────────────────────────────────────────────────────┘
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

# With Ollama (FREE local LLM)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.2
```

---

## Stats

```bash
agenticom stats

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

## Project Structure

```
├── agenticom/                    # CLI package (antfarm-style)
│   ├── cli.py                    # CLI commands
│   ├── core.py                   # Orchestration engine
│   ├── state.py                  # SQLite state
│   ├── workflows.py              # YAML parser
│   └── bundled_workflows/        # Ready-to-use workflows
│
├── orchestration/                # Full platform (7,159 lines)
│   ├── api.py                    # REST API (27 endpoints)
│   ├── guardrails.py             # Content filtering
│   ├── memory.py                 # Persistent memory
│   ├── approval.py               # Approval gates
│   ├── observability.py          # Metrics & tracing
│   ├── cache.py                  # Response caching
│   ├── security.py               # JWT, audit, sanitization
│   ├── pipeline.py               # Agent pipelines
│   ├── conversation.py           # No-code builder
│   └── integrations/
│       ├── ollama.py             # FREE local LLM
│       ├── openclaw.py           # Claude
│       └── nanobot.py            # GPT
```

---

## License

MIT — Use it, fork it, ship it.

---

<p align="center">
  <strong>Antfarm, but production-ready.</strong><br>
  <br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star on GitHub</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Report Bug</a>
</p>
