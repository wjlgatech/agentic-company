# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agenticom is a Python framework for orchestrating multi-agent AI teams. Agents (planner, developer, verifier, tester, reviewer) collaborate through YAML-defined workflows with production safety features: guardrails, memory, approval gates, and observability. Inspired by Antfarm but adds MCP integration for real tool execution.

**9 Bundled Workflows**: 2 core (feature-dev, marketing-campaign) + 7 enterprise (due-diligence, compliance-audit, patent-landscape, security-assessment, churn-analysis, grant-proposal, incident-postmortem).

## Common Commands

```bash
# Setup
make install              # pip install -e .
make dev                  # Install with dev + LLM provider deps

# Testing
make test                 # pytest tests/ -v
pytest tests/test_agents.py -v              # Run single test file
pytest tests/test_agents.py::TestName -v    # Run single test class/function

# Code Quality
make lint                 # ruff check + mypy
make format               # black + ruff --fix

# Dev Server
make serve                # uvicorn on port 8000 with reload

# CLI
agenticom workflow list
agenticom workflow run <id> "<task description>"
agenticom workflow inspect <id>            # Show step inputs/outputs
agenticom workflow status <run-id>
agenticom workflow resume <run-id>
agenticom dashboard                        # Open web UI
```

## Architecture

### Core packages

- **`orchestration/`** — Framework core. All major subsystems are modules here.
- **`agenticom/`** — CLI entry point and bundled workflow YAML files (`agenticom/bundled_workflows/`).
- **`frontend/`** — React + Vite + TypeScript web dashboard (Zustand, TanStack Query, Tailwind).

### Execution flow

1. **YAML workflow** defines agents (with roles/prompts) and steps (with template inputs)
2. **`WorkflowParser`** (`orchestration/workflows/parser.py`) converts YAML → `AgentTeam` with `WorkflowStep` list
3. **`AgentTeam`** (`orchestration/agents/team.py`) executes steps sequentially; each step gets fresh context ("Ralph Loop" pattern to prevent hallucination)
4. **Template substitution**: `{{task}}` injects user input, `{{step_outputs.step_id}}` passes previous step results
5. **LLM execution**: `UnifiedExecutor` (`orchestration/integrations/unified.py`) routes to OpenClaw (Anthropic), Nanobot (OpenAI), or Ollama (local)

### Key subsystems (all under `orchestration/`)

| Module | Purpose |
|---|---|
| `agents/` | Base agent, specialized agents (Planner/Developer/Verifier/Tester/Reviewer), AgentTeam orchestration, TeamBuilder fluent API |
| `workflows/` | YAML parser, template substitution engine |
| `integrations/` | LLM backends: OpenClaw, Nanobot, Ollama + `auto_setup_executor()` |
| `tools/` | MCP bridge, tool registry, PromptEngineer, IntentRefiner (PIR), ConversationalRefiner, SmartRefiner (multi-turn interview → coherent prompt synthesis), HybridRefiner |
| `guardrails.py` | Composable pipeline: content filter, PII detection, rate limiting |
| `memory.py` | Local/Redis/PostgreSQL memory backends |
| `approval.py` | Auto/Human/Hybrid approval gates |
| `pipeline.py` | Generic step-by-step execution engine |
| `evaluator.py` | Rule-based + LLM-based quality evaluation |
| `observability.py` | Prometheus metrics, structlog, distributed tracing |
| `api.py` | FastAPI REST API |
| `database.py` | SQLAlchemy ORM (SQLite dev / PostgreSQL prod) |
| `conversation.py` | Natural language workflow builder |

### Workflow YAML structure

```yaml
id: feature-dev
agents:
  - id: planner
    name: Planner
    role: Requirements Analysis & Task Breakdown
    prompt: |
      [Agent instructions]
steps:
  - id: plan
    agent: planner
    input: "{{task}}"
    expects: "STATUS: done"
    retry: 2
  - id: develop
    agent: developer
    input: "{{step_outputs.plan}}"
```

The YAML parser uses the `id` field (not `role`) for agent-to-role mapping. Template variables with hyphenated step IDs are converted (`{{step_outputs.X}}` → `{X}` format internally).

### MCP integration

`MCPToolBridge` (`tools/mcp_bridge.py`) connects workflow tool references to real MCP servers (PubMed, Ahrefs, Similarweb, etc.) via `MCPToolRegistry` (`tools/registry.py`).

## Code Style

- **Formatter**: Black, line length 88
- **Linter**: Ruff (rules: E, F, W, I, N, UP, B, C4; E501 ignored)
- **Type checking**: mypy with `disallow_untyped_defs = true`
- **Python**: 3.10+ required
- **Async**: pytest uses `asyncio_mode = "auto"` — async test functions work without decorators

## Entry Points

Three CLI entry points defined in `pyproject.toml`:
- `agentic` → `orchestration.cli:main`
- `agenticom` → `agenticom.cli:main`
- `agenticom-launch` → `orchestration.launcher:main`

## Demo & Examples

- **`demo/`** — SmartChatbox: Real LLM-powered multi-turn interview demo with Claude API integration (`demo/server.py` + `demo/index.html`)
- **`examples/`** — Code examples for using the framework
- **`experiments/`** — Research/evaluation scripts (not for production use)

## Debugging Web Applications

**IMPORTANT:** When implementing or debugging web features (dashboard, frontend, etc.):

1. **Always check the browser console first**
   - Press `F12` (or `Cmd+Option+I` on Mac)
   - Look for JavaScript errors (red messages)
   - Check Network tab for API failures
   - Example: "Uncaught SyntaxError" indicates a JavaScript syntax error

2. **Common issues:**
   - Nested template literals cause syntax errors → Use string concatenation instead
   - Unescaped quotes in dynamic content → Always escape with `.replace(/"/g, '&quot;')`
   - API returning data but UI empty → JavaScript error preventing execution
   - CORS errors → Check server headers

3. **Debugging workflow:**
   ```javascript
   // Add console.log to trace execution
   console.log('Loading data...', data);

   // Add error handling
   try {
     await someOperation();
   } catch (err) {
     console.error('Operation failed:', err);
   }
   ```

4. **Test API endpoints independently:**
   ```bash
   curl http://localhost:3000/api/workflows
   curl http://localhost:3000/api/runs
   ```

## Verification Testing Protocol

**CRITICAL RULE:** Before claiming any fix or feature is working, you MUST verify it from the user's perspective.

### Testing Requirements:

1. **For API/Backend Changes:**
   ```bash
   # Test the actual HTTP endpoint
   curl -s http://localhost:PORT/api/endpoint | jq .

   # Verify data structure
   curl -s http://localhost:PORT/api/runs | jq '.[0] | keys'

   # Test with actual user parameters
   curl -X POST http://localhost:PORT/api/action -d '{"param": "value"}'
   ```

2. **For UI/Frontend Changes:**
   ```bash
   # Verify served HTML contains your changes
   curl -s http://localhost:PORT/ | grep -A5 "your-new-function"

   # Check that JavaScript is syntactically valid
   curl -s http://localhost:PORT/ > /tmp/page.html
   # Then inspect /tmp/page.html for your changes
   ```

3. **For CLI Commands:**
   ```bash
   # Run the actual command the user would run
   agenticom workflow list
   agenticom workflow status <run-id>

   # Verify output format and content
   agenticom workflow status <run-id> | grep "Status:"
   ```

4. **For Dashboard/Web UI:**
   - After making code changes and restarting server
   - Verify served HTML actually contains your changes (curl test)
   - Clear Python cache if needed: `find . -name "*.pyc" -delete`
   - Force kill and restart: `pkill -9 -f "process-name"`
   - Check browser console (F12) for JavaScript errors
   - Test the actual user interaction flow

### Before Reporting Success:

✅ **DO:**
- Test the endpoint/command exactly as the user would interact with it
- Verify the served content matches your source code changes
- Check for JavaScript/Python syntax errors in logs
- Confirm data is flowing through the entire pipeline
- Test edge cases (empty data, errors, etc.)

❌ **DON'T:**
- Claim something works without testing it
- Assume changes took effect without verification
- Test only the source file (test the runtime behavior)
- Skip testing if "it should work in theory"

### Example Verification Flow:

```bash
# 1. Make changes to code
vim agenticom/dashboard.py

# 2. Restart service
pkill -9 -f "agenticom dashboard" && sleep 1
agenticom dashboard &

# 3. VERIFY changes are live
curl -s http://localhost:8080/ | grep "my-new-function"  # Should find it

# 4. Test user interaction
curl -s http://localhost:8080/api/runs | jq '.[0]'  # Should show data

# 5. Check for errors
tail /tmp/dashboard.log  # Should be empty or show startup only
```

**Remember:** The user experiences the running application, not the source code. Always test the running system.

## AI-Human Collaboration Workflow

This section defines the optimal division of labor between AI (Claude Code) and human developers based on observed patterns and meta-analysis.

### What AI Should Automate ✅

**1. Implementation & Testing Loop**
- Write code based on requirements
- Run automated verification tests BEFORE claiming success
- Iterate on fixes using test feedback
- Only report success when tests pass
- Generate test cases for edge cases

**Example workflow:**
```bash
# AI's internal loop (don't report until this succeeds)
1. Write fix → 2. curl test endpoint → 3. Verify output → 4. PASS? → Report success
                                                         ↓ FAIL
                                                         └─→ Debug → Repeat
```

**2. Verification Testing**
- Test APIs with curl before saying "API is working"
- Test CLI commands before saying "command works"
- Check served HTML matches source code changes
- Verify JavaScript syntax in browser console
- Test the complete user interaction flow

**3. Documentation Generation**
- Auto-generate docs from code changes
- Update README with new features
- Create test result reports
- Document configuration changes

**4. Iterative Debugging**
- Read error messages from logs/console
- Identify root cause
- Apply fix
- Verify fix with tests
- Repeat until resolved

### What Requires Human Input ❌

**1. Requirement Clarification & Design Decisions**
- "Should we use approach A or B?"
- "What's the priority: performance or maintainability?"
- "Is this feature really needed?"
- UI/UX design choices

**Why:** Strategic decisions need domain expertise and context only humans have.

**2. Acceptance Testing**
- Testing in real browser with real user interactions
- Visual inspection of UI changes
- Workflow testing with production-like data
- Security review of sensitive changes

**Why:** Humans catch usability issues and real-world edge cases AI can't simulate.

**3. Production Approvals**
- Approving git commits
- Deploying to production
- Merging pull requests
- Releasing new versions

**Why:** Humans bear responsibility for production changes and should review before deployment.

**4. Error Diagnosis from Real Usage**
- Browser console errors with screenshots
- Network tab inspection
- Real-world bug reports from users
- Performance profiling

**Why:** AI can't access browser dev tools or see visual UI issues.

**5. Strategic Direction**
- Roadmap planning
- Feature prioritization
- Architecture evolution
- Tech stack decisions

**Why:** Business context and long-term vision require human judgment.

### Anti-Patterns to Avoid 🚫

Based on 2-day debugging session meta-analysis:

**❌ Don't: Claim "Fixed!" without testing**
```
BAD: "I've fixed the View Full Logs button. It should work now."
GOOD: "I've fixed the button. Let me verify: [runs curl test] ✅ Confirmed working."
```

**❌ Don't: Assume changes took effect**
```
BAD: "I updated dashboard.py, so the changes are live."
GOOD: "Updated dashboard.py. Testing served HTML... ✅ Changes confirmed in output."
```

**❌ Don't: Test only source files**
```
BAD: cat dashboard.py | grep "my-function"  # Only checks source
GOOD: curl http://localhost:8080/ | grep "my-function"  # Tests runtime
```

**❌ Don't: Skip edge case testing**
```
BAD: "The function works for normal input."
GOOD: "Tested: normal input ✅, empty input ✅, malformed input ✅"
```

**❌ Don't: Report success on first attempt**
```
BAD: After 1 try: "All fixed!" → User reports still broken → 8 more iterations
GOOD: After 1 try: Test → Still broken → Fix → Test → ✅ Now report success
```

### Improved Workflow Pattern

**Traditional Pattern (High Iteration Count):**
```
User: "Button doesn't work"
  ↓
AI: "Fixed!" [no testing]
  ↓
User: "Still broken" [tests in browser]
  ↓
AI: "Fixed again!" [still no testing]
  ↓
Repeat 5-8 times...
```

**Optimized Pattern (Low Iteration Count):**
```
User: "Button doesn't work"
  ↓
AI: [Fix → Test → Fail → Debug → Fix → Test → Pass]
  ↓
AI: "Fixed and verified ✅ [shows test output]"
  ↓
User: [Acceptance test in browser]
  ↓
User: "Approved ✅" or "Issue with UX: [specific feedback]"
```

### Key Metrics from Meta-Analysis

**Before Verification Protocol:**
- Average iterations per fix: 5-8
- False "Fixed!" claims: 80%
- User time spent on diagnosis: High

**After Verification Protocol:**
- Average iterations per fix: 1-2
- False "Fixed!" claims: <10%
- User time spent on diagnosis: Low (only acceptance testing)

### Practical Examples

**Example 1: Dashboard Button Fix**
```bash
# ❌ OLD APPROACH: Claim success without testing
echo "Fixed the button!" # No verification

# ✅ NEW APPROACH: Test before claiming success
curl -s http://localhost:8081/ | grep "btn-view-logs" # Verify button exists
curl -s http://localhost:8081/api/runs | jq '.[0].id' # Verify data
echo "✅ Button rendering confirmed, API working"
```

**Example 2: API Endpoint Change**
```bash
# ❌ OLD APPROACH:
# "I've updated the /api/status endpoint to return more data"

# ✅ NEW APPROACH:
# Test before reporting:
curl -s http://localhost:8081/api/status | jq .
# Output shows new fields → ✅ Confirmed
# "Updated /api/status endpoint. Verification: [paste output]"
```

**Example 3: CLI Command Fix**
```bash
# ❌ OLD APPROACH:
# "Fixed the workflow status command"

# ✅ NEW APPROACH:
agenticom workflow status test-run-123
# Output shows correct status → ✅ Confirmed
# "Fixed workflow status command. Test output: [paste result]"
```

### Collaboration Model Summary

| Task | AI Role | Human Role |
|------|---------|------------|
| **Requirements** | Ask clarifying questions | Define what/why |
| **Design** | Propose options with tradeoffs | Choose approach |
| **Implementation** | Write code | Review code |
| **Testing** | Automated verification ✅ | Acceptance testing |
| **Debugging** | Fix → Test loop | Diagnose real-world issues |
| **Documentation** | Generate docs | Review accuracy |
| **Deployment** | Prepare changes | Approve & deploy |

**Golden Rule:** AI automates the "verify it works" loop. Human provides the "verify it's right" judgment.
