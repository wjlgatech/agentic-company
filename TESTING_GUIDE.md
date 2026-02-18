# 🧪 Complete Testing Guide - Loop-Back & Archive Features

## 🚀 **Quick Start**

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Make sure dashboard is running
agenticom dashboard
# Opens at http://localhost:8080

# 3. Open another terminal for testing
source .venv/bin/activate
```

---

## ✅ **Test Suite 1: Archive/Delete Commands**

### Test 1.1: List Current Runs

```bash
agenticom workflow list

# Expected: Shows all active (non-archived) workflow runs
# Example output:
# 📋 5 workflow run(s):
# ✅ abc123 - feature-dev
#    Task: Create calculator...
#    Status: completed
#    Steps: 5/5
```

### Test 1.2: Archive a Run

```bash
# Pick a run ID from the list above (e.g., abc123)
agenticom workflow archive abc123

# Expected output:
# 📦 Archived workflow run: abc123
#    Use 'agenticom workflow unarchive' to restore
```

### Test 1.3: Verify Archive

```bash
# List without archived
agenticom workflow list

# Expected: abc123 should NOT appear

# List with archived
agenticom workflow list --include-archived

# Expected: abc123 should appear with [ARCHIVED] tag
```

### Test 1.4: Unarchive

```bash
agenticom workflow unarchive abc123

# Expected output:
# 📤 Unarchived workflow run: abc123
#    Run is now visible in active list

# Verify it's back
agenticom workflow list
# Expected: abc123 appears in list
```

### Test 1.5: Soft Delete

```bash
agenticom workflow delete abc123

# Expected output:
# 📦 Archived workflow run: abc123
#    Use 'agenticom workflow unarchive' to restore

# Note: Same as archive by default
```

### Test 1.6: Permanent Delete

```bash
agenticom workflow delete abc123 --permanent

# Expected: Confirmation prompt
# ⚠️  Permanently delete run abc123? This cannot be undone! [y/N]:

# Type 'y' to confirm

# Expected output:
# 🗑️  Permanently deleted workflow run: abc123

# Verify it's gone
agenticom workflow list --include-archived
# Expected: abc123 not in list at all
```

---

## ✅ **Test Suite 2: Loop-Back Workflow**

### Test 2.1: Run Feature Development with Loop-Back

```bash
# This workflow has loop-back configured for verify/test steps
agenticom workflow run feature-dev-loopback "Create a simple calculator with add and divide functions"

# Expected behavior:
# 1. PLAN: Breaks down the task ✅
# 2. IMPLEMENT: Writes code ✅
# 3. VERIFY: Reviews code (may fail first time) ❌
# 4. LOOP BACK TO IMPLEMENT: Fixes issues ✅
# 5. VERIFY: Passes second time ✅
# 6. TEST: Creates tests ✅
# 7. REVIEW: Final approval ✅

# Watch the dashboard to see loop-back in action!
```

### Test 2.2: Check Loop History

```python
# In Python:
from agenticom.state import StateManager

state = StateManager()
runs = state.list_runs(limit=1)
run = runs[0]

print(f"Loop counts: {run.loop_counts}")
print(f"Feedback history: {len(run.feedback_history)} entries")

for feedback in run.feedback_history:
    print(f"\nStep: {feedback['step_id']}")
    print(f"Action: {feedback.get('action', 'retry')}")
    print(f"Loop #: {feedback['loop_count']}")
    print(f"Feedback: {feedback['feedback'][:100]}...")
```

---

## ✅ **Test Suite 3: LLM-Powered Recovery**

### Test 3.1: Run with LLM Analysis

```bash
# This workflow uses LLM to decide recovery strategy
agenticom workflow run feature-dev-llm "Build a todo list CLI with add, list, and complete commands"

# Expected behavior:
# 1. When verification fails, LLM analyzes:
#    - Error type (syntax, logic, missing feature)
#    - Context (what was supposed to be done)
#    - Available actions (retry vs loop-back)
# 2. LLM decides optimal recovery:
#    - RETRY: For small issues or missing details
#    - LOOP_BACK: For logic errors needing reimplementation
#    - STOP: For fundamental impossibilities
# 3. LLM provides specific feedback to agent
```

### Test 3.2: View LLM Decisions

```bash
# Check the logs/context for LLM analysis
agenticom workflow inspect <run-id>

# Look for context variables:
# - implement_llm_feedback
# - verify_llm_loopback_feedback

# These contain LLM's analysis and recommendations
```

---

## ✅ **Test Suite 4: Dashboard Visualization**

### Test 4.1: Watch Real-Time Loop-Back

1. Open dashboard: http://localhost:8080
2. Run a workflow in another terminal:
   ```bash
   agenticom workflow run feature-dev-loopback "Create calculator"
   ```
3. Watch the dashboard for:
   - Stage progress bar
   - Step status updates
   - Real-time transitions
   - Loop-back indicators (step counter may decrease)

### Test 4.2: Inspect Feedback History

1. Click on a completed run in dashboard
2. Expand step details
3. Look for feedback in step inputs
4. Check for loop count indicators

---

## ✅ **Test Suite 5: Python API**

### Test 5.1: Manual Loop-Back Test

```python
from agenticom.workflows import WorkflowDefinition, WorkflowRunner
from agenticom.failure_handler import FailureHandler
from agenticom.state import StateManager

# Load workflow
workflow = WorkflowDefinition.from_yaml(
    'agenticom/bundled_workflows/feature-dev-with-loopback.yaml'
)

# Simple executor (replace with real LLM)
def simple_executor(agent_prompt: str, user_input: str) -> str:
    return "STATUS: done"  # Simulated response

# Create components
state = StateManager()
handler = FailureHandler(llm_executor=simple_executor)
runner = WorkflowRunner(
    state_manager=state,
    executor=simple_executor,
    failure_handler=handler
)

# Run workflow
run, results = runner.run_all(
    workflow,
    task="Create a hello world function",
    stop_on_failure=True
)

# Check results
print(f"Run ID: {run.id}")
print(f"Status: {run.status}")
print(f"Steps completed: {len([r for r in results if r.status.value == 'completed'])}/{len(results)}")
print(f"Loop history: {run.loop_counts}")
print(f"Feedback entries: {len(run.feedback_history)}")
```

### Test 5.2: Custom Failure Handler

```python
from agenticom.failure_handler import FailureHandler

def custom_llm(prompt: str) -> str:
    # Your custom LLM implementation
    # Could be OpenAI, Anthropic, or any LLM
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# Create handler with custom LLM
handler = FailureHandler(llm_executor=custom_llm)

# Use in runner...
```

---

## 📊 **Expected Results**

### Success Indicators:

✅ **Archive/Delete:**
- Commands execute without errors
- Runs appear/disappear from list correctly
- Confirmation prompts work
- Database updates persist

✅ **Loop-Back:**
- Failed steps trigger loop-back
- Execution jumps to correct previous step
- Feedback appears in context
- Loop count increments properly
- Max loops enforced (workflow stops after limit)

✅ **LLM Recovery:**
- LLM analysis prompt is generated
- LLM responds with valid action
- Action is parsed and executed
- Fallback works if LLM fails
- Feedback is specific and helpful

---

## 🐛 **Troubleshooting**

### Issue: Commands not found

```bash
# Solution: Activate virtual environment
source .venv/bin/activate
which agenticom  # Should point to .venv/bin/agenticom
```

### Issue: Workflow fails immediately

```bash
# Check error message
agenticom workflow status <run-id>

# Common causes:
# 1. Missing LLM API key
# 2. Invalid YAML syntax
# 3. Agent configuration error

# Debug mode
agenticom workflow run <workflow-id> "<task>" --dry-run
```

### Issue: Loop-back not triggering

```python
# Verify on_failure is configured in YAML
import yaml
with open('path/to/workflow.yaml') as f:
    workflow = yaml.safe_load(f)

for step in workflow['steps']:
    if 'on_failure' in step:
        print(f"{step['id']}: {step['on_failure']}")
    else:
        print(f"{step['id']}: No on_failure config")
```

### Issue: Dashboard not showing loop-back

```bash
# Dashboard updates in real-time
# Refresh the page if needed
# Check browser console for errors
# Verify dashboard is running: lsof -i :8080
```

---

## 📈 **Performance Testing**

### Test: Max Loops Enforcement

```bash
# Create a workflow that will fail repeatedly
# Verify it stops after max_loops attempts

# Check the run
agenticom workflow status <run-id>

# Should show:
# Status: failed
# Error: "Exceeded maximum loop attempts"

# Check loop counts
python3 -c "
from agenticom.state import StateManager
state = StateManager()
run = state.get_run('<run-id>')
print(f'Loop counts: {run.loop_counts}')
"
```

### Test: Feedback Context Size

```bash
# Run workflow with multiple loop-backs
# Check that feedback history doesn't grow unbounded

# Verify context size
python3 -c "
from agenticom.state import StateManager
state = StateManager()
run = state.get_run('<run-id>')
import json
context_size = len(json.dumps(run.context))
print(f'Context size: {context_size} bytes')
print(f'Feedback entries: {len(run.feedback_history)}')
"

# Should be reasonable (< 100KB per run)
```

---

## ✅ **Acceptance Criteria**

All features pass if:

1. ✅ Archive/unarchive commands work correctly
2. ✅ Delete with confirmation works
3. ✅ Permanent delete removes all data
4. ✅ Loop-back triggers on failure
5. ✅ Feedback is passed to retried steps
6. ✅ Max loops are enforced
7. ✅ LLM analysis provides valid decisions
8. ✅ Dashboard shows real-time updates
9. ✅ No infinite loops
10. ✅ Context doesn't grow unbounded

---

## 🎉 **Next Steps After Testing**

1. ✅ Verify all tests pass
2. ✅ Commit remaining changes
3. ✅ Push to main branch
4. ✅ Update documentation
5. ✅ Create release notes
6. ✅ Share with team

---

**🚀 Happy Testing!**
