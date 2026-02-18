# Phase 1 & 2 Testing Guide

**Dashboard URL:** http://localhost:8081
**Status:** ✅ Running

---

## 🎯 What You're Testing

**Phase 1:** Core diagnostics infrastructure (config, capture, monitoring)
**Phase 2:** Integration with AgentTeam (metadata fields, initialization, hooks)

**Important:** Phase 3 (Auto-Test Loop) is NOT yet implemented, so browser automation won't actually execute. This testing verifies the **infrastructure is in place**.

---

## ✅ Testing Checklist

### 1. CLI Commands (Phase 1)

#### Test: Check Diagnostics Installation Status
```bash
agenticom diagnostics
```

**Expected Output:**
```
🔬 Diagnostics System Status
========================================
❌ Playwright: Not installed

📦 Install with:
   pip install 'agentic-company[diagnostics]'

🌐 Then install browsers:
   playwright install
```

**What This Tests:**
- ✅ CLI command exists
- ✅ Installation check works
- ✅ Graceful handling of missing Playwright

---

### 2. Python Import Tests (Phase 1)

#### Test: Import Core Classes
```bash
python3 << 'EOF'
from orchestration.diagnostics import (
    DiagnosticsConfig,
    IterationMonitor,
    check_playwright_installation,
)

print("✅ All imports successful")
print(f"Playwright installed: {check_playwright_installation()}")

# Create config
config = DiagnosticsConfig(
    enabled=True,
    browser_type="chromium",
    iteration_threshold=3,
)
print(f"✅ Config created: enabled={config.enabled}, threshold={config.iteration_threshold}")

# Create monitor
monitor = IterationMonitor(config)
monitor.start_step("test_step")
print(f"✅ Monitor created and started")

# Record iteration
record = monitor.record_iteration(
    error="Test error",
    fix_attempted="Test fix",
    test_result=False
)
print(f"✅ Iteration recorded: #{record.iteration}")
print(f"Iterations: {monitor.get_iteration_count()}")
EOF
```

**Expected Output:**
```
✅ All imports successful
Playwright installed: False
✅ Config created: enabled=True, threshold=3
✅ Monitor created and started
✅ Iteration recorded: #1
Iterations: 1
```

**What This Tests:**
- ✅ Core classes import successfully
- ✅ DiagnosticsConfig validation works
- ✅ IterationMonitor tracks iterations
- ✅ Works WITHOUT Playwright installed

---

### 3. Phase 1 Example Script

#### Test: Run Example Script
```bash
python3 examples/diagnostics_example.py
```

**Expected Output:**
```
============================================================
Diagnostics System Example (Phase 1)
============================================================

1. Checking Playwright installation...
   Playwright installed: False
   ⚠️  Install with: pip install 'agentic-company[diagnostics]'

2. Creating DiagnosticsConfig...
   Enabled: True
   Browser: chromium
   Viewport: 1920x1080
   Iteration threshold: 3
   Max iterations: 10

3. Demonstrating IterationMonitor...
   Started monitoring: example_step

   Simulating fix-test iterations:
     Iteration 1: FAIL
     Iteration 2: FAIL
     Iteration 3: FAIL
     ⚠️  Meta-analysis threshold reached!
     (Would trigger meta-analysis in Phase 4)

4. Iteration history:
   Iteration 1:
     Error: Test failed: Error 1
     Fix: Attempted fix 1
     Result: FAIL
   [...]

============================================================
Summary
============================================================
✅ Core infrastructure working
✅ IterationMonitor tracking 3 iterations
✅ Meta-analysis trigger detection working
```

**What This Tests:**
- ✅ Full Phase 1 infrastructure works
- ✅ IterationMonitor detects threshold
- ✅ Meta-analysis trigger works

---

### 4. Integration Tests (Phase 2)

#### Test: Run Integration Test Suite
```bash
pytest tests/test_diagnostics_integration.py -v
```

**Expected Output:**
```
tests/test_diagnostics_integration.py::test_step_result_has_metadata_field PASSED
tests/test_diagnostics_integration.py::test_team_config_has_diagnostics_config_field PASSED
tests/test_diagnostics_integration.py::test_team_config_accepts_diagnostics_config PASSED
tests/test_diagnostics_integration.py::test_agent_team_initializes_without_diagnostics PASSED
tests/test_diagnostics_integration.py::test_agent_team_gracefully_handles_missing_playwright PASSED
tests/test_diagnostics_integration.py::test_agent_team_executes_step_without_diagnostics PASSED
tests/test_diagnostics_integration.py::test_step_metadata_preserved_without_diagnostics PASSED
tests/test_diagnostics_integration.py::test_diagnostics_integrator_initializes SKIPPED
tests/test_diagnostics_integration.py::test_step_with_diagnostics_enabled SKIPPED
tests/test_diagnostics_integration.py::test_existing_code_still_works PASSED
tests/test_diagnostics_integration.py::test_workflow_run_without_diagnostics PASSED

=================== 9 passed, 2 skipped, 2 warnings in 0.14s ===================
```

**What This Tests:**
- ✅ StepResult has metadata field
- ✅ TeamConfig has diagnostics_config field
- ✅ AgentTeam initializes diagnostics
- ✅ Graceful degradation without Playwright
- ✅ Backward compatibility (existing code still works)

---

### 5. Python Integration Test (Phase 2)

#### Test: Create Team with Diagnostics Config
```bash
python3 << 'EOF'
from orchestration.diagnostics import DiagnosticsConfig
from orchestration.agents.team import AgentTeam, TeamConfig

# Create diagnostics config
diag_config = DiagnosticsConfig(
    enabled=True,
    playwright_headless=True,
    iteration_threshold=3,
)
print("✅ DiagnosticsConfig created")

# Create team config with diagnostics
team_config = TeamConfig(
    name="Test Team",
    description="Testing Phase 2 integration",
    diagnostics_config=diag_config,
)
print("✅ TeamConfig created with diagnostics_config")

# Create team
team = AgentTeam(team_config)
print(f"✅ AgentTeam created with ID: {team.id}")

# Check diagnostics attribute
if hasattr(team, 'diagnostics'):
    print(f"✅ Team has 'diagnostics' attribute")
    if team.diagnostics is None:
        print("   ℹ️  Diagnostics is None (expected - Playwright not installed or no LLM backend)")
    else:
        print("   ✅ DiagnosticsIntegrator initialized!")
else:
    print("❌ Team missing 'diagnostics' attribute")

print("\n✅ Phase 2 integration working!")
EOF
```

**Expected Output:**
```
✅ DiagnosticsConfig created
✅ TeamConfig created with diagnostics_config
✅ AgentTeam created with ID: <uuid>
✅ Team has 'diagnostics' attribute
   ℹ️  Diagnostics is None (expected - Playwright not installed or no LLM backend)

✅ Phase 2 integration working!
```

**What This Tests:**
- ✅ TeamConfig accepts DiagnosticsConfig
- ✅ AgentTeam initializes with diagnostics config
- ✅ Graceful fallback when Playwright not installed

---

### 6. Dashboard Verification

#### Test: Check Dashboard is Running
```bash
curl -s http://localhost:8081/ | grep -o "<title>.*</title>"
```

**Expected Output:**
```
<title>Agenticom Dashboard</title>
```

#### Test: Check API Endpoints
```bash
# Check runs API
curl -s http://localhost:8081/api/runs | jq 'length'

# Check workflows API
curl -s http://localhost:8081/api/workflows | jq 'length'
```

**Expected Output:**
```
<number>  # Number of workflow runs
<number>  # Number of available workflows
```

**What This Tests:**
- ✅ Dashboard server is running
- ✅ API endpoints respond
- ✅ Existing workflows/runs accessible

---

### 7. Backward Compatibility Tests

#### Test: Verify Existing Tests Still Pass
```bash
pytest tests/test_agents.py -v -q
```

**Expected Output:**
```
========================= 39 passed, 1 warning in 0.24s =========================
```

**What This Tests:**
- ✅ No regressions introduced
- ✅ Existing agent functionality unchanged
- ✅ Phase 1 & 2 are backward compatible

---

## 🔍 What You WON'T See Yet (Phase 3+)

### Not Yet Implemented:
- ❌ **Actual browser automation** - PlaywrightCapture exists but isn't called yet
- ❌ **Auto-retry loop** - DiagnosticsIntegrator.wrap_step_execution() is a stub
- ❌ **Real diagnostic capture** - capture_step_diagnostics() returns placeholder data
- ❌ **Meta-analysis** - MetaAnalyzer exists but isn't triggered yet
- ❌ **Criteria builder** - CriteriaBuilder is a stub

### Why?
These features require:
1. **Playwright installed** (`pip install 'agentic-company[diagnostics]' && playwright install`)
2. **Phase 3 implementation** (auto-test loop)
3. **Phase 4 implementation** (meta-analysis)
4. **Phase 5 implementation** (criteria builder)

---

## 📊 Expected Test Results Summary

| Test Category | Expected Result |
|---------------|-----------------|
| Phase 1 Unit Tests | 25 passed, 3 skipped |
| Phase 2 Integration Tests | 9 passed, 2 skipped |
| Backward Compatibility | 39 passed, 0 failed |
| CLI Commands | All working |
| Python Imports | All successful |
| Dashboard | Running on port 8081 |

**Total:** 73 tests passing, 5 skipped, 0 failures

---

## 🐛 Troubleshooting

### Issue: "No module named 'orchestration.diagnostics'"
**Solution:**
```bash
pip install -e .
```

### Issue: "Dashboard won't start"
**Solution:**
```bash
pkill -9 -f "agenticom dashboard"
agenticom dashboard --port 8081
```

### Issue: "Tests failing"
**Solution:**
```bash
# Check if you're in the right directory
pwd  # Should be /Users/jialiang.wu/Documents/Projects/agentic-company

# Activate venv
source .venv/bin/activate

# Run tests
pytest tests/test_diagnostics.py -v
```

### Issue: "ImportError: Playwright is required"
**Expected:** This is normal if you haven't installed Playwright. The system should gracefully handle this and continue working for non-browser features.

**To install Playwright (optional for Phase 1 & 2):**
```bash
pip install 'agentic-company[diagnostics]'
playwright install chromium
```

---

## ✅ Success Criteria

You should be able to verify:

1. ✅ **CLI command works** - `agenticom diagnostics` runs
2. ✅ **Imports work** - Can import DiagnosticsConfig, IterationMonitor
3. ✅ **Config works** - Can create and validate DiagnosticsConfig
4. ✅ **Monitor works** - IterationMonitor tracks iterations and triggers threshold
5. ✅ **Integration works** - TeamConfig accepts diagnostics_config
6. ✅ **Team initialization works** - AgentTeam has diagnostics attribute
7. ✅ **Graceful degradation** - Everything works without Playwright
8. ✅ **Tests pass** - 73 tests passing, 5 skipped
9. ✅ **No regressions** - All existing tests still pass
10. ✅ **Dashboard runs** - Web UI accessible at http://localhost:8081

---

## 🎉 What This Proves

**Phase 1 & 2 are complete and production-ready:**
- ✅ Core infrastructure is solid
- ✅ Integration with AgentTeam is clean
- ✅ Zero overhead when disabled
- ✅ Graceful degradation without dependencies
- ✅ Comprehensive test coverage
- ✅ 100% backward compatible
- ✅ Ready for Phase 3 implementation

---

**Dashboard:** http://localhost:8081
**Documentation:** PHASE_1_IMPLEMENTATION_SUMMARY.md, PHASE_2_IMPLEMENTATION_SUMMARY.md
**Next Steps:** Phase 3 (Auto-Test Loop with browser automation)
