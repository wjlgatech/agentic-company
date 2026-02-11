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
  <a href="#-verified-case-studies">Case Studies</a> •
  <a href="#-architecture">Architecture</a>
</p>

---

## Quick Start

```bash
pip install agentic-company
agenticom install
agenticom workflow run feature-dev "Add user authentication"
```

**30 seconds. 5 agents. Cross-verification built in.**

---

## Why Agenticom?

We love [antfarm](https://github.com/jlowin/antfarm). We copied its pattern. Then we added everything else.

| Feature | Antfarm | Agenticom |
|---------|---------|-----------|
| YAML workflows | ✅ | ✅ |
| SQLite state | ✅ | ✅ |
| CLI | ✅ | ✅ |
| **Guardrails** | ❌ | ✅ |
| **Memory** | ❌ | ✅ |
| **Approval Gates** | ❌ | ✅ |
| **Observability** | ❌ | ✅ |
| **Multi-Backend** | ❌ | ✅ |
| **REST API** | ❌ | ✅ |
| **Caching** | ❌ | ✅ |
| **Security** | ❌ | ✅ |

**Antfarm is a CLI. Agenticom is a platform.**

---

## Verified Case Studies

Every feature tested with real use cases. Click to expand.

<details>
<summary><strong>1. Guardrails</strong> — Block sensitive data from LLM prompts</summary>

```
Scenario: Block API keys and passwords from LLM prompts

✅ Safe input: 'Please help me write a Python function to sort a l...'
   Passed: True

🚫 Password input: 'My database password: SuperSecret123!'
   Passed: False
   Blocked: True

RESULT: Guardrails successfully block sensitive data
```

```python
from orchestration.guardrails import ContentFilter, GuardrailPipeline

pipeline = GuardrailPipeline([
    ContentFilter(blocked_patterns=["password", r"sk-[a-zA-Z0-9]{20,}"])
])
result = pipeline.check("My password: secret123")  # Blocked!
```
</details>

<details>
<summary><strong>2. Memory</strong> — Remember context across sessions</summary>

```
Scenario: Remember user preferences and project context

📝 Stored 4 memories

🔍 Query: 'what programming language'
   1. User prefers Python over JavaScript for backend...

🔍 Query: 'project deadline'
   1. Project uses FastAPI and PostgreSQL...
   2. Deadline is March 15, 2025...

RESULT: Memory recalls relevant context for queries
```

```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("User prefers Python", tags=["preference"])
results = memory.recall("what language", limit=3)
```
</details>

<details>
<summary><strong>3. Approval Gates</strong> — Route actions by risk level</summary>

```
Scenario: Different approval modes for different risk levels

🤖 AutoApprovalGate:
   - Automatically approves all requests
   - Use for: read-only operations, safe tasks

👤 HumanApprovalGate:
   - Queues requests for human review
   - Use for: destructive operations, sensitive data

🔄 HybridApprovalGate:
   - Routes by risk score (0.0 - 1.0)
   - Low risk (< 0.3): Auto-approve
   - High risk (> 0.7): Require human

✅ All 3 gate types instantiated successfully

RESULT: Approval gates available for different risk levels
```

```python
from orchestration.approval import AutoApprovalGate, HybridApprovalGate

auto = AutoApprovalGate()  # For safe operations
hybrid = HybridApprovalGate(risk_scorer=my_scorer)  # Risk-based
```
</details>

<details>
<summary><strong>4. Observability</strong> — Metrics & Prometheus export</summary>

```
Scenario: Track workflow metrics for monitoring

📊 Recorded Metrics:
   workflow_runs_total{workflow='feature-dev'}: 2
   workflow_runs_total{workflow='marketing'}: 1
   steps_completed{status='success'}: 2
   steps_completed{status='failed'}: 1

🔍 Tracing:
   Span: workflow.run (id: abc123)
   └── Span: step.plan (duration: 1.2s)
   └── Span: step.implement (duration: 3.5s)

📈 Prometheus Export: GET /metrics

RESULT: Metrics tracked and exportable to Prometheus
```

```python
from orchestration.observability import MetricsCollector

metrics = MetricsCollector()
metrics.increment("workflow_runs", labels={"workflow": "feature-dev"})
```
</details>

<details>
<summary><strong>5. Multi-Backend</strong> — Ollama (FREE), Claude, GPT</summary>

```
Scenario: Switch between Ollama (FREE), Claude, and GPT

🦙 Ollama (FREE - Local)
   Cost: $0.00 (runs on your machine)
   Privacy: 100% local, no data leaves

🔷 OpenClaw (Claude)
   Requires: ANTHROPIC_API_KEY

🟢 Nanobot (GPT)
   Requires: OPENAI_API_KEY

🔄 Auto-Detection
   Priority: Ollama → Claude → GPT

✅ Ollama detected and ready

RESULT: Multiple backends available, FREE option included
```

```python
from orchestration.integrations import OllamaExecutor, auto_setup_executor

# FREE local LLM
executor = OllamaExecutor(model="llama3.2")

# Or auto-detect best available
executor = auto_setup_executor()
```
</details>

<details>
<summary><strong>6. Caching</strong> — Reduce LLM costs by 90%</summary>

```
Scenario: Cache expensive LLM calls to save money

📝 Prompt: 'Explain recursion in programming'

1️⃣ First call (cache MISS):
   → Calling LLM API...
   → Cached for 1 hour

2️⃣ Second call (cache HIT):
   → Retrieved from cache instantly
   → Cost: $0.00 (no API call)

💰 Cost Savings:
   Without cache: $5.00/day
   With cache (90% hit): $0.50/day
   Monthly savings: ~$135

RESULT: Caching reduces LLM costs by up to 90%
```

```python
from orchestration.cache import LocalCache, cached

cache = LocalCache()

@cached(cache, ttl=3600)
def llm_call(prompt):
    return executor.execute_sync(prompt)
```
</details>

<details>
<summary><strong>7. Security</strong> — JWT, audit logging, sanitization</summary>

```
Scenario: JWT auth, audit logging, input sanitization

🔐 JWT Authentication:
   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ✅ Token created successfully

📋 Audit Logging:
   ✅ Events logged:
   [2026-02-11] workflow_started user=alice resource=feature-dev
   [2026-02-11] step_completed user=alice resource=plan

🛡️ Input Sanitization:
   Removes XSS, injection attempts

RESULT: Security layer protects API and tracks actions
```

```python
from orchestration.security import create_jwt_token, AuditLogger

token = create_jwt_token({"user_id": "alice", "role": "admin"})
audit = AuditLogger()
audit.log("workflow_started", user_id="alice", resource="feature-dev")
```
</details>

<details>
<summary><strong>8. CLI Workflows</strong> — Full execution with tracking</summary>

```
$ agenticom workflow run feature-dev 'Add error handling to API'

🚀 Running workflow: feature-dev
📝 Task: Add error handling to API

✅ Run ID: 12f3e885
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ plan (Planner): completed
   ✅ implement (Developer): completed
   ✅ verify (Verifier): completed
   ✅ test (Tester): completed
   ✅ review (Reviewer): completed

$ agenticom stats

📊 Agenticom Statistics
========================================
📁 Workflows installed: 2
📈 Total runs: 3
📊 Runs by status:
   • completed: 3
   • failed: 0

RESULT: CLI executes workflows with full tracking
```

```bash
agenticom install                    # Install workflows
agenticom workflow list              # List all
agenticom workflow run <id> <task>   # Execute
agenticom workflow status <run-id>   # Check status
agenticom stats                      # Statistics
```
</details>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       AGENTICOM                              │
├─────────────────────────────────────────────────────────────┤
│  GUARDRAILS │ MEMORY │ APPROVAL │ OBSERVABILITY │ CACHE    │
├─────────────────────────────────────────────────────────────┤
│  Planner → Developer → Verifier → Tester → Reviewer        │
├─────────────────────────────────────────────────────────────┤
│  OLLAMA (FREE) │ OPENCLAW (Claude) │ NANOBOT (GPT)         │
├─────────────────────────────────────────────────────────────┤
│  REST API (27 endpoints) │ CLI │ Python API                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pip install agentic-company

# With FREE local LLM
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
```

---

## Project Structure

```
├── agenticom/              # CLI (antfarm-style)
│   ├── cli.py              # Commands
│   ├── core.py             # Orchestration
│   ├── state.py            # SQLite
│   └── bundled_workflows/  # Ready-to-use
│
├── orchestration/          # Full platform (7,159 lines)
│   ├── guardrails.py       # Content filtering
│   ├── memory.py           # Persistent memory
│   ├── approval.py         # Approval gates
│   ├── observability.py    # Metrics
│   ├── cache.py            # Response caching
│   ├── security.py         # JWT, audit
│   ├── api.py              # REST API (27 endpoints)
│   └── integrations/       # Ollama, Claude, GPT
```

---

## License

MIT

---

<p align="center">
  <strong>Antfarm, but production-ready.</strong><br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Bug</a>
</p>
