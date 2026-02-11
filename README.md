<p align="center">
  <img src="assets/icons/agenticom-golden.svg" width="180" alt="Agenticom"/>
</p>

<h1 align="center">AGENTICOM</h1>

<p align="center">
  <strong>One agent makes mistakes. Five agents ship features.</strong><br>
  <em>Multi-agent orchestration for OpenClaw and Nanobot.</em>
</p>

<p align="center">
  <a href="#-use-with-openclaw">OpenClaw</a> •
  <a href="#-use-standalone">Standalone</a> •
  <a href="#-natural-language-builder">Natural Language</a> •
  <a href="#-vs-antfarm">vs Antfarm</a>
</p>

---

## What is Agenticom?

Agenticom adds **multi-agent teams** to your AI workflow. Instead of one agent doing everything, you get 5 specialized agents that check each other's work.

```
Single Agent:  User → Agent → Output (hope it's right)

Agenticom:     User → Planner → Developer → Verifier → Tester → Reviewer → Output
                              ↑______________|
                              (cross-verification)
```

*Inspired by [antfarm](https://github.com/snarktank/antfarm)'s elegant YAML + SQLite pattern.*

---

## 🦞 Use with OpenClaw

[OpenClaw](https://github.com/openclaw/openclaw) is a personal AI assistant for WhatsApp, Telegram, Slack, Discord, and more. Agenticom adds multi-agent workflows to OpenClaw.

### Install Agenticom as OpenClaw Skill

```bash
# Clone to OpenClaw workspace
git clone https://github.com/wjlgatech/agentic-company.git ~/.openclaw/workspace/agenticom
cd ~/.openclaw/workspace/agenticom

# Install Python package
pip install -e .

# Install bundled workflows
agenticom install

# Copy skill to OpenClaw skills directory
cp -r skills/agenticom-workflows ~/.openclaw/skills/
```

### Use in OpenClaw

Once installed, tell your OpenClaw agent:

```
"Use agenticom to build user authentication with JWT"
```

Or run directly:

```bash
agenticom workflow run feature-dev "Add JWT authentication to the REST API"
```

<details>
<summary><strong>Example: Full workflow in OpenClaw</strong></summary>

```
You: Use agenticom to add dark mode to my app

OpenClaw: I'll run the feature-dev workflow with Agenticom.

$ agenticom workflow run feature-dev "Add dark mode toggle with system preference detection"

🚀 Running workflow: feature-dev
📝 Task: Add dark mode toggle with system preference detection

✅ Run ID: a7b3c9d2
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ plan (Planner): completed
      - Created 4 stories: theme context, toggle component, CSS variables, persistence
   ✅ implement (Developer): completed
      - Implemented ThemeProvider, DarkModeToggle, CSS custom properties
   ✅ verify (Verifier): completed
      - Verified all acceptance criteria met
   ✅ test (Tester): completed
      - Added unit tests for theme switching
   ✅ review (Reviewer): completed
      - Code review passed, ready to merge

The dark mode feature has been implemented with:
- System preference detection
- Manual toggle override
- Persistent preference storage
- Smooth transition animations
```
</details>

### Available Workflows

| Workflow | Agents | Steps | Use Case |
|----------|--------|-------|----------|
| `feature-dev` | 5 | 5 | Planner → Developer → Verifier → Tester → Reviewer |
| `marketing-campaign` | 5 | 5 | SocialIntel → Competitor → Content → Community → Lead |

---

## 🟢 Use Standalone

No OpenClaw? Run Agenticom directly with any LLM backend.

### Install

```bash
pip install agentic-company
agenticom install
```

### With Ollama (FREE)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.2

# Run workflow
agenticom workflow run feature-dev "Build REST API for user management"
```

### With Claude (Anthropic)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
agenticom workflow run feature-dev "Add caching layer to API"
```

### With GPT (OpenAI / Nanobot)

```bash
export OPENAI_API_KEY=sk-...
agenticom workflow run marketing-campaign "Launch campaign for AI coding tool"
```

### CLI Commands

```bash
agenticom install                    # Install bundled workflows
agenticom workflow list              # List all workflows
agenticom workflow run <id> <task>   # Execute workflow
agenticom workflow status <run-id>   # Check status
agenticom workflow resume <run-id>   # Resume failed run
agenticom stats                      # Show statistics
agenticom uninstall --force          # Remove all data
```

<details>
<summary><strong>Example: CLI output</strong></summary>

```bash
$ agenticom workflow run feature-dev "Add error handling to API endpoints"

🚀 Running workflow: feature-dev
📝 Task: Add error handling to API endpoints

✅ Run ID: 12f3e885
📊 Status: completed
📈 Progress: 5/5 steps

📋 Step Results:
   ✅ plan (Planner): completed
   ✅ implement (Developer): completed
   ✅ verify (Verifier): completed
   ✅ test (Tester): completed
   ✅ review (Reviewer): completed

💡 Check status: agenticom workflow status 12f3e885

$ agenticom stats

📊 Agenticom Statistics
========================================
📁 Workflows installed: 2
🔹 Workflow names: Feature Development Team, Viral Marketing Campaign
📈 Total runs: 3
📂 Database: ~/.agenticom/state.db

📊 Runs by status:
   • completed: 3
   • failed: 0
```
</details>

---

## 💬 Natural Language Builder

Build workflows by answering questions. No code required.

### Python API

```python
from orchestration.conversation import ConversationBuilder

builder = ConversationBuilder()

# Answer questions to build workflow
builder.answer("a")  # Build a feature
builder.answer("auth-flow")  # Name it
builder.answer("a")  # Full team (5 agents)
builder.answer("Add OAuth2 login with Google")

# Generate outputs
yaml_config = builder.generate_yaml()
python_code = builder.generate_python()
```

<details>
<summary><strong>Generated YAML</strong></summary>

```yaml
id: auth-flow
name: Auth Flow
description: Add OAuth2 login with Google

agents:
  - role: planner
    guardrails: [content-filter]
  - role: developer
  - role: verifier
  - role: tester
  - role: reviewer

steps:
  - id: plan
    agent: planner
    input: "Create a detailed plan for: {task}"
    expects: "Clear step-by-step plan"

  - id: implement
    agent: developer
    input: "Implement: {plan}"
    verified_by: verifier
    max_retries: 3

  - id: test
    agent: tester
    input: "Test: {implement}"
    expects: "All tests passing"

  - id: review
    agent: reviewer
    input: "Review: {test}"
```
</details>

---

## ⚔️ vs Antfarm

Both [Antfarm](https://github.com/snarktank/antfarm) and Agenticom provide multi-agent workflows for OpenClaw. Here's how they differ:

| Feature | Antfarm | Agenticom |
|---------|---------|-----------|
| Language | TypeScript | Python |
| Execution | Cron polling (15 min) | Direct execution |
| **Guardrails** | ❌ | ✅ Content filter, rate limiter |
| **Memory** | ❌ | ✅ Persistent remember/recall |
| **Approval Gates** | ❌ | ✅ Auto/Human/Hybrid |
| **Multi-Backend** | ❌ | ✅ Ollama (FREE), Claude, GPT |
| **REST API** | ❌ | ✅ 27 endpoints |
| **Caching** | ❌ | ✅ LLM response cache |
| Dashboard | ✅ Web UI | CLI-based |
| OpenClaw Skill | ✅ | ✅ |

**Use Antfarm if:** You want a web dashboard and cron-based execution.

**Use Agenticom if:** You need guardrails, memory, approval gates, or want to use Python.

---

## 🛡️ Built-in Features

<details>
<summary><strong>Guardrails</strong> — Block sensitive data</summary>

```python
from orchestration.guardrails import ContentFilter, GuardrailPipeline

pipeline = GuardrailPipeline([
    ContentFilter(blocked_patterns=["password", r"sk-[a-zA-Z0-9]{20,}"])
])
# Blocks: "My password: secret123" ❌
```
</details>

<details>
<summary><strong>Memory</strong> — Remember context</summary>

```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("User prefers Python", tags=["preference"])
results = memory.recall("what language", limit=3)
```
</details>

<details>
<summary><strong>Approval Gates</strong> — Human-in-the-loop</summary>

```python
from orchestration.approval import AutoApprovalGate, HumanApprovalGate

auto = AutoApprovalGate()  # For safe operations
human = HumanApprovalGate(timeout_seconds=300)  # For risky ones
```
</details>

<details>
<summary><strong>Caching</strong> — Reduce LLM costs</summary>

```python
from orchestration.cache import LocalCache, cached

cache = LocalCache()

@cached(cache, ttl=3600)
def llm_call(prompt):
    return executor.execute_sync(prompt)
```
</details>

---

## 📦 Project Structure

```
├── agenticom/              # CLI (antfarm-style)
│   ├── cli.py              # Commands
│   ├── core.py             # Orchestration
│   ├── state.py            # SQLite persistence
│   └── bundled_workflows/  # Ready-to-use workflows
│
├── orchestration/          # Full platform
│   ├── guardrails.py       # Content filtering
│   ├── memory.py           # Persistent memory
│   ├── approval.py         # Approval gates
│   ├── cache.py            # Response caching
│   └── integrations/       # Ollama, Claude, GPT
│
├── skills/                 # OpenClaw skill
│   └── agenticom-workflows/
│       └── SKILL.md
```

---

## License

MIT

---

<p align="center">
  <strong>Your AI got coworkers.</strong><br>
  <a href="https://github.com/wjlgatech/agentic-company">⭐ Star</a> •
  <a href="https://github.com/wjlgatech/agentic-company/issues">🐛 Bug</a>
</p>
