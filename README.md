<p align="center">
  <img src="assets/icons/agenticom-golden.svg" width="180" alt="Agenticom"/>
</p>

<h1 align="center">AGENTICOM</h1>

<p align="center">
  <strong>One agent makes mistakes. Five agents ship features.</strong><br>
  <em>Multi-agent orchestration for OpenClaw, Nanobot, and Ollama.</em>
</p>

<p align="center">
  <a href="#-use-with-openclaw">OpenClaw</a> •
  <a href="#-use-with-nanobot">Nanobot</a> •
  <a href="#-use-standalone">Standalone</a> •
  <a href="#-natural-language-builder">Natural Language</a>
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

Works with **OpenClaw** (Claude), **Nanobot** (GPT), or **Ollama** (FREE local).

*Inspired by [antfarm](https://github.com/jlowin/antfarm)'s elegant YAML + SQLite pattern.*

---

## 🔷 Use with OpenClaw

OpenClaw (Claude Code) users can add Agenticom as an MCP tool.

### Setup (30 seconds)

```bash
pip install agentic-company
```

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agenticom": {
      "command": "python",
      "args": ["-m", "orchestration.mcp_server"]
    }
  }
}
```

### Use in Claude Code

Once configured, you can ask Claude:

```
"Use agenticom to build user authentication with JWT"
```

Claude will have access to these tools:

| Tool | Description |
|------|-------------|
| `agenticom_list_teams` | List available agent teams |
| `agenticom_run_team` | Run a team on a task |
| `agenticom_execute_step` | Execute a single step |
| `agenticom_create_team` | Create custom team |

<details>
<summary><strong>Example: Run marketing campaign in Claude Code</strong></summary>

```
You: Use agenticom to create a viral launch campaign for my new CLI tool

Claude: I'll use the marketing team from Agenticom.

[Calls agenticom_run_team with team="marketing", task="Create viral launch..."]

The team executed 5 steps:
1. SocialIntelAgent: Found 23 pain points on Reddit/HN about CLI tools
2. CompetitorAnalyst: Analyzed fig, warp, starship - identified gaps
3. ContentCreator: Generated 7-day content calendar with threads
4. CommunityManager: Created outreach plan for 15 communities
5. CampaignLead: Compiled 30-day execution plan

[Full output with actionable items]
```
</details>

### Python API with OpenClaw

```python
from orchestration.integrations import OpenClawExecutor
from orchestration.agents import AgentTeam, PlannerAgent, DeveloperAgent, VerifierAgent

# Uses ANTHROPIC_API_KEY from environment
executor = OpenClawExecutor()

# Create team with Claude as the brain
team = AgentTeam(
    agents=[PlannerAgent(), DeveloperAgent(), VerifierAgent()],
    executor=executor
)

# Run task
result = await team.run("Add rate limiting to the API")
```

---

## 🟢 Use with Nanobot

Nanobot (OpenAI) users can use Agenticom with GPT models.

### Setup

```bash
pip install agentic-company
export OPENAI_API_KEY=sk-...
```

### Python API with Nanobot

```python
from orchestration.integrations import NanobotExecutor
from orchestration.agents import AgentTeam, PlannerAgent, DeveloperAgent, VerifierAgent

# Uses OPENAI_API_KEY from environment
executor = NanobotExecutor(model="gpt-4-turbo")

# Create team with GPT as the brain
team = AgentTeam(
    agents=[PlannerAgent(), DeveloperAgent(), VerifierAgent()],
    executor=executor
)

# Run task
result = await team.run("Refactor the authentication module")
```

### CLI with Nanobot

```bash
export OPENAI_API_KEY=sk-...
agenticom install
agenticom workflow run feature-dev "Add caching layer"
```

Agenticom auto-detects your API key and uses Nanobot.

---

## 🦙 Use Standalone (FREE with Ollama)

No API key? Run 100% local with Ollama.

### Setup

```bash
# Install Ollama (one time)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.2

# Install Agenticom
pip install agentic-company
agenticom install
```

### CLI (Recommended)

```bash
agenticom workflow run feature-dev "Build REST API for user management"
```

```
🚀 Running workflow: feature-dev
📝 Task: Build REST API for user management

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

### Python API with Ollama

```python
from orchestration.integrations import OllamaExecutor
from orchestration.agents import AgentTeam, PlannerAgent, DeveloperAgent, VerifierAgent

# FREE - no API key needed
executor = OllamaExecutor(model="llama3.2")

team = AgentTeam(
    agents=[PlannerAgent(), DeveloperAgent(), VerifierAgent()],
    executor=executor
)

result = await team.run("Write unit tests for the payment module")
```

### Auto-Detection

Don't know which backend? Let Agenticom figure it out:

```python
from orchestration.integrations import auto_setup_executor

# Tries: Ollama → OpenClaw → Nanobot
executor = auto_setup_executor()
```

---

## 💬 Natural Language Builder

Build workflows by answering questions. No code required.

### Interactive CLI

```bash
agentic create
```

```
👋 Hi! What would you like your AI team to help you with?

   a) Build a new feature ⭐ Most Popular
   b) Fix a bug
   c) Write content
   d) Review & improve code
   e) Something else

> a

🏷️ What should we call this workflow?
> jwt-auth

🤖 Which AI agents should be on your team?
   a) Full team (5 agents) ⭐ Recommended
   b) Quick team (3 agents)
   c) Custom

> a

📝 Describe the task:
> Add JWT authentication with refresh tokens to the FastAPI backend

✅ Generated workflow!

Saved to: ~/.agenticom/workflows/jwt-auth.yaml
Run with: agenticom workflow run jwt-auth
```

### Python API

```python
from orchestration.conversation import ConversationBuilder

builder = ConversationBuilder()

# Answer questions programmatically
builder.answer("a")  # Build a feature
builder.answer("auth-flow")  # Workflow name
builder.answer("a")  # Full team
builder.answer("Add OAuth2 login with Google and GitHub")

# Generate outputs
yaml_config = builder.generate_yaml()
python_code = builder.generate_python()
```

<details>
<summary><strong>Generated YAML Example</strong></summary>

```yaml
id: auth-flow
name: Auth Flow
description: Add OAuth2 login with Google and GitHub

agents:
  - role: planner
    guardrails:
      - content-filter
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

<details>
<summary><strong>Generated Python Example</strong></summary>

```python
from orchestration import TeamBuilder, AgentRole

team = (TeamBuilder("auth-flow")
    .with_planner()
    .with_developer()
    .with_verifier()
    .with_tester()
    .with_reviewer()
    .step("plan", AgentRole.PLANNER, "Create plan: {task}")
    .step("impl", AgentRole.DEVELOPER, "Implement: {plan}",
          verified_by=AgentRole.VERIFIER)
    .step("test", AgentRole.TESTER, "Test: {impl}")
    .step("review", AgentRole.REVIEWER, "Review: {test}")
    .build())

result = await team.run("Add OAuth2 login with Google and GitHub")
```
</details>

---

## 🛡️ Built-in Features

Agenticom includes production features out of the box:

<details>
<summary><strong>Guardrails</strong> — Block sensitive data</summary>

```python
from orchestration.guardrails import ContentFilter, GuardrailPipeline

pipeline = GuardrailPipeline([
    ContentFilter(blocked_patterns=["password", r"sk-[a-zA-Z0-9]{20,}"])
])

# Blocks: "My password: secret123" ❌
# Allows: "Write a login function" ✅
```
</details>

<details>
<summary><strong>Memory</strong> — Remember context across sessions</summary>

```python
from orchestration.memory import LocalMemoryStore

memory = LocalMemoryStore()
memory.remember("User prefers Python", tags=["preference"])
memory.remember("Project uses FastAPI", tags=["tech"])

results = memory.recall("what framework", limit=3)
# Returns: "Project uses FastAPI"
```
</details>

<details>
<summary><strong>Approval Gates</strong> — Human-in-the-loop</summary>

```python
from orchestration.approval import AutoApprovalGate, HumanApprovalGate

# Auto-approve safe operations
auto = AutoApprovalGate()

# Require human approval for destructive actions
human = HumanApprovalGate(timeout_seconds=300)
```
</details>

<details>
<summary><strong>Observability</strong> — Metrics & tracing</summary>

```python
from orchestration.observability import MetricsCollector

metrics = MetricsCollector()
metrics.increment("workflow_runs", labels={"team": "feature-dev"})

# Export to Prometheus: GET /metrics
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

# Second call is FREE (cache hit)
```
</details>

<details>
<summary><strong>Security</strong> — JWT, audit, sanitization</summary>

```python
from orchestration.security import create_jwt_token, AuditLogger

token = create_jwt_token({"user_id": "alice"})
audit = AuditLogger()
audit.log("workflow_started", user_id="alice", resource="feature-dev")
```
</details>

---

## 📦 Installation

```bash
# Basic
pip install agentic-company
agenticom install

# With FREE local LLM
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
```

---

## 🗂️ Project Structure

```
├── agenticom/              # CLI (run workflows)
│   └── bundled_workflows/  # Ready-to-use teams
│
├── orchestration/          # Full platform
│   ├── integrations/       # OpenClaw, Nanobot, Ollama
│   ├── agents/             # Agent definitions
│   ├── guardrails.py       # Content filtering
│   ├── memory.py           # Persistent memory
│   ├── approval.py         # Human-in-the-loop
│   ├── mcp_server.py       # Claude Code integration
│   └── conversation.py     # Natural language builder
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
