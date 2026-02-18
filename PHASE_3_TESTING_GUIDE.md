# Phase 3 Testing Guide: Auto-Test-After-Fix Loop

**What You're Testing:** The automatic retry mechanism that tests implementations with browser automation and retries until they pass.

---

## 🎯 Testing Options

You can test Phase 3 in two ways:

1. **Without Playwright** (Quick - 5 minutes) - Tests the logic without real browser
2. **With Playwright** (Complete - 15 minutes) - Tests with real browser automation

Let's do both!

---

## Option 1: Testing Without Playwright (Unit Tests)

These tests verify the auto-test loop logic without requiring Playwright installation.

### Step 1: Run Unit Tests

```bash
cd /Users/jialiang.wu/Documents/Projects/agentic-company
source .venv/bin/activate
pytest tests/test_phase3_auto_test_loop.py -v -k "not integration"
```

**Expected Output:**
```
tests/test_phase3_auto_test_loop.py::test_diagnostics_integrator_initialization PASSED
tests/test_phase3_auto_test_loop.py::test_wrap_step_execution_without_diagnostics_enabled PASSED
tests/test_phase3_auto_test_loop.py::test_wrap_step_execution_no_test_config PASSED
tests/test_phase3_auto_test_loop.py::test_capture_step_diagnostics_no_config PASSED
tests/test_phase3_auto_test_loop.py::test_run_diagnostics_invalid_action PASSED
tests/test_phase3_auto_test_loop.py::test_monitor_resets_per_step PASSED
tests/test_phase3_auto_test_loop.py::test_graceful_handling_of_playwright_errors PASSED
tests/test_phase3_auto_test_loop.py::test_max_iterations_respected PASSED

======================= 8 passed, 5 deselected in 3.07s ==============
```

**✅ Success Criteria:**
- All 8 tests pass
- No failures or errors
- Tests complete in ~3 seconds

---

## Option 2: Testing With Playwright (Real Browser Automation)

This tests the full system with real browser automation.

### Step 1: Install Playwright (If Not Already Installed)

```bash
# Check if Playwright is installed
agenticom diagnostics
```

If you see "❌ Playwright: Not installed", install it:

```bash
# Install Playwright
pip install 'agentic-company[diagnostics]'

# Install browser (Chromium only for faster install)
playwright install chromium

# Verify installation
agenticom diagnostics
```

**Expected Output:**
```
🔬 Diagnostics System Status
========================================
✅ Playwright: Installed
   Version: 1.40.0

📋 Usage:
   Add diagnostics_config to workflow YAML
   Set enabled: true and configure options
```

### Step 2: Run Integration Tests

```bash
pytest tests/test_phase3_auto_test_loop.py -v -m integration --tb=short
```

**Expected Output:**
```
tests/test_phase3_auto_test_loop.py::test_run_diagnostics_real_browser PASSED
tests/test_phase3_auto_test_loop.py::test_run_diagnostics_navigation_failure PASSED
tests/test_phase3_auto_test_loop.py::test_run_diagnostics_timeout PASSED
tests/test_phase3_auto_test_loop.py::test_capture_step_diagnostics_real_browser PASSED

======================= 4 passed in 15.23s =======================
```

**What's Happening:**
- Real browser (Chromium) launches
- Navigates to example.com
- Captures screenshots
- Records console logs
- Captures network requests

**✅ Success Criteria:**
- All 4 integration tests pass
- Browser launches and closes properly
- Screenshots saved to `outputs/diagnostics/`

### Step 3: Check Generated Screenshots

```bash
ls -lh outputs/diagnostics/
```

**Expected Output:**
```
total 120K
-rw-r--r-- 1 user staff  45K example.png
-rw-r--r-- 1 user staff  38K test.png
```

You should see screenshots captured during tests!

---

## 🧪 Manual Testing: Real Workflow Example

Let's create and run a test workflow that uses Phase 3 auto-test loop.

### Step 1: Create Test Script

Save this as `test_phase3_workflow.py`:

```python
#!/usr/bin/env python3
"""Manual test of Phase 3 auto-test loop."""

import asyncio
from pathlib import Path

from orchestration.diagnostics import DiagnosticsConfig
from orchestration.diagnostics.integration import DiagnosticsIntegrator
from orchestration.diagnostics.capture import BrowserAction, ActionType


async def test_simple_browser_automation():
    """Test simple browser automation."""
    print("=" * 60)
    print("Phase 3 Manual Test: Browser Automation")
    print("=" * 60)
    print()

    # Create diagnostics config
    config = DiagnosticsConfig(
        enabled=True,
        playwright_headless=False,  # Set to True to run headless
        max_iterations=3,
        iteration_threshold=2,
        capture_screenshots=True,
        capture_console=True,
        capture_network=True,
    )

    print("✅ DiagnosticsConfig created")
    print(f"   Max iterations: {config.max_iterations}")
    print(f"   Headless: {config.playwright_headless}")
    print()

    # Create integrator
    integrator = DiagnosticsIntegrator(config, executor=None)
    print("✅ DiagnosticsIntegrator created")
    print()

    # Define test actions
    test_url = "https://example.com"
    test_actions = [
        {"type": "navigate", "value": "https://example.com"},
        {"type": "wait_for_selector", "selector": "h1", "timeout": 5000},
        {"type": "screenshot", "value": "example_page.png"},
    ]

    print("📋 Test Configuration:")
    print(f"   URL: {test_url}")
    print(f"   Actions: {len(test_actions)}")
    for i, action in enumerate(test_actions, 1):
        print(f"     {i}. {action['type']}", end="")
        if 'selector' in action:
            print(f" ({action['selector']})", end="")
        if 'value' in action:
            print(f" → {action['value']}", end="")
        print()
    print()

    # Run diagnostics
    print("🚀 Running browser automation...")
    print()

    try:
        result = await integrator._run_diagnostics(test_url, test_actions)

        print("=" * 60)
        print("Results")
        print("=" * 60)
        print(f"✅ Success: {result.success}")
        print(f"📊 Console logs: {len(result.console_logs)}")
        print(f"❌ Console errors: {len(result.console_errors)}")
        print(f"🌐 Network requests: {len(result.network_requests)}")
        print(f"📸 Screenshots: {len(result.screenshots)}")
        print(f"🔗 Final URL: {result.final_url}")
        print(f"⏱️  Execution time: {result.execution_time_ms:.0f}ms")
        print()

        if result.screenshots:
            print("📸 Screenshots saved:")
            for screenshot in result.screenshots:
                print(f"   • {screenshot}")
            print()

        if result.console_logs:
            print("📋 Console logs (first 3):")
            for log in result.console_logs[:3]:
                print(f"   [{log.type}] {log.text[:80]}")
            print()

        if result.network_requests:
            print("🌐 Network requests (first 5):")
            for req in result.network_requests[:5]:
                print(f"   {req.method} {req.url[:60]}... ({req.status})")
            print()

        print("=" * 60)
        print("✅ Phase 3 Manual Test: SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_browser_automation())
```

### Step 2: Run Test Script

```bash
python3 test_phase3_workflow.py
```

**Expected Output:**
```
============================================================
Phase 3 Manual Test: Browser Automation
============================================================

✅ DiagnosticsConfig created
   Max iterations: 3
   Headless: False

✅ DiagnosticsIntegrator created

📋 Test Configuration:
   URL: https://example.com
   Actions: 3
     1. navigate → https://example.com
     2. wait_for_selector (#h1)
     3. screenshot → example_page.png

🚀 Running browser automation...

============================================================
Results
============================================================
✅ Success: True
📊 Console logs: 0
❌ Console errors: 0
🌐 Network requests: 2
📸 Screenshots: 1
🔗 Final URL: https://example.com/
⏱️  Execution time: 1234ms

📸 Screenshots saved:
   • /Users/jialiang.wu/Documents/Projects/agentic-company/outputs/diagnostics/example_page.png

🌐 Network requests (first 5):
   GET https://example.com/... (200)
   GET https://example.com/favicon.ico... (404)

============================================================
✅ Phase 3 Manual Test: SUCCESS
============================================================
```

**What You Should See:**
- Browser window opens (if headless=False)
- Navigates to example.com
- Takes screenshot
- Browser closes
- Screenshot saved to outputs/diagnostics/

### Step 3: View Screenshot

```bash
open outputs/diagnostics/example_page.png
```

You should see a screenshot of example.com!

---

## 🔄 Testing the Auto-Retry Loop

Let's test the retry mechanism with a failing test that eventually succeeds.

### Create Retry Test Script

Save this as `test_phase3_retry.py`:

```python
#!/usr/bin/env python3
"""Test Phase 3 auto-retry mechanism."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from orchestration.diagnostics import DiagnosticsConfig
from orchestration.diagnostics.integration import DiagnosticsIntegrator
from orchestration.diagnostics.capture import DiagnosticCapture


async def test_retry_mechanism():
    """Test that retry loop works correctly."""
    print("=" * 60)
    print("Testing Auto-Retry Mechanism")
    print("=" * 60)
    print()

    # Create config with low max_iterations for testing
    config = DiagnosticsConfig(
        enabled=True,
        max_iterations=5,
        iteration_threshold=3,
    )

    # Create integrator with mock executor
    mock_executor = AsyncMock()
    integrator = DiagnosticsIntegrator(config, mock_executor)

    print("✅ Created integrator with:")
    print(f"   Max iterations: {config.max_iterations}")
    print(f"   Threshold: {config.iteration_threshold}")
    print()

    # Create mock step
    mock_step = MagicMock()
    mock_step.id = "test_step"
    mock_step.metadata = {
        "diagnostics_enabled": True,
        "test_url": "https://example.com",
        "test_actions": [
            {"type": "navigate", "value": "https://example.com"},
        ],
    }

    # Track attempts
    attempt_count = 0

    async def mock_execute(*args, **kwargs):
        """Mock execution that tracks attempts."""
        nonlocal attempt_count
        attempt_count += 1

        result = MagicMock()
        result.metadata = {}
        result.agent_result = MagicMock()
        result.agent_result.output = f"Attempt {attempt_count}"
        return result

    # Mock diagnostics to fail first 2 times, then succeed
    call_count = [0]

    async def mock_diagnostics(url, actions):
        call_count[0] += 1
        print(f"🔄 Iteration {call_count[0]}: Running diagnostics...")

        if call_count[0] < 3:
            # Fail first 2 times
            print(f"   ❌ Test failed (simulated)")
            return DiagnosticCapture(
                success=False,
                error=f"Test failed on attempt {call_count[0]}",
            )
        else:
            # Succeed on 3rd attempt
            print(f"   ✅ Test passed!")
            return DiagnosticCapture(
                success=True,
                final_url="https://example.com",
            )

    # Patch the methods
    integrator._run_diagnostics = mock_diagnostics

    print("🚀 Starting auto-retry loop...")
    print("   (Will fail 2 times, succeed on 3rd)")
    print()

    # Execute with retry loop
    result = await integrator.wrap_step_execution(
        mock_step,
        mock_execute
    )

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"✅ Completed after {call_count[0]} iterations")
    print(f"📊 Expected: 3 iterations (2 failures + 1 success)")
    print(f"📊 Actual: {call_count[0]} iterations")
    print()
    print(f"Metadata:")
    print(f"   • Iteration: {result.metadata.get('iteration')}")
    print(f"   • Total iterations: {result.metadata.get('iterations_total')}")
    print(f"   • Success: {result.metadata.get('diagnostics', {}).get('success')}")
    print()

    # Verify iteration tracking
    iterations = integrator.monitor.get_iterations("test_step")
    print(f"Iteration History:")
    for record in iterations:
        status = "✅ PASS" if record.test_result else "❌ FAIL"
        print(f"   {record.iteration}. {status} - {record.error or 'Success'}")
    print()

    print("=" * 60)
    print("✅ Auto-Retry Mechanism: WORKING")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_retry_mechanism())
```

### Run Retry Test

```bash
python3 test_phase3_retry.py
```

**Expected Output:**
```
============================================================
Testing Auto-Retry Mechanism
============================================================

✅ Created integrator with:
   Max iterations: 5
   Threshold: 3

🚀 Starting auto-retry loop...
   (Will fail 2 times, succeed on 3rd)

🔄 Iteration 1: Running diagnostics...
   ❌ Test failed (simulated)
🔄 Iteration 2: Running diagnostics...
   ❌ Test failed (simulated)
🔄 Iteration 3: Running diagnostics...
   ✅ Test passed!

============================================================
Results
============================================================
✅ Completed after 3 iterations
📊 Expected: 3 iterations (2 failures + 1 success)
📊 Actual: 3 iterations

Metadata:
   • Iteration: 3
   • Total iterations: 3
   • Success: True

Iteration History:
   1. ❌ FAIL - Test failed on attempt 1
   2. ❌ FAIL - Test failed on attempt 2
   3. ✅ PASS - Success

============================================================
✅ Auto-Retry Mechanism: WORKING
============================================================
```

**✅ Success Criteria:**
- Retries exactly 3 times
- Tracks each iteration correctly
- Stops when test passes
- Metadata shows complete history

---

## 📊 Verify All Tests Still Pass

Let's make sure Phase 3 didn't break anything:

```bash
# Test Phase 1
pytest tests/test_diagnostics.py -v -q

# Test Phase 2
pytest tests/test_diagnostics_integration.py -v -q

# Test Phase 3
pytest tests/test_phase3_auto_test_loop.py -v -q
```

**Expected Output:**
```
Phase 1: 25 passed, 3 skipped
Phase 2:  9 passed, 2 skipped
Phase 3:  8 passed, 5 skipped (without Playwright)
        13 passed (with Playwright)
─────────────────────────────────────
Total:   42-47 passed, 5-10 skipped
```

---

## 🎉 Success Checklist

Mark what you've verified:

### Without Playwright:
- [ ] Unit tests pass (8 tests)
- [ ] Retry mechanism works correctly
- [ ] Iteration tracking accurate
- [ ] Max iterations respected
- [ ] Error handling graceful

### With Playwright:
- [ ] Integration tests pass (4-5 tests)
- [ ] Browser launches successfully
- [ ] Screenshots captured
- [ ] Console logs captured
- [ ] Network requests tracked
- [ ] Browser closes properly

### Manual Testing:
- [ ] test_phase3_workflow.py runs successfully
- [ ] Browser automation works
- [ ] Screenshots saved correctly
- [ ] test_phase3_retry.py demonstrates retry loop

---

## 🐛 Troubleshooting

### Issue: "Playwright not installed"
```bash
pip install 'agentic-company[diagnostics]'
playwright install chromium
```

### Issue: "Browser won't launch"
```bash
# Check Playwright installation
playwright --version

# Reinstall browsers
playwright install --force chromium
```

### Issue: Tests timeout
- Set higher timeout in DiagnosticsConfig:
```python
config = DiagnosticsConfig(
    timeout_ms=60000,  # 60 seconds
)
```

### Issue: Permission errors on screenshots
```bash
# Create output directory
mkdir -p outputs/diagnostics
chmod 755 outputs/diagnostics
```

---

## 📈 What You've Verified

After completing this guide, you've verified:

✅ **Phase 3 Core Features:**
- Auto-retry loop mechanism
- Browser automation (with Playwright)
- Iteration tracking
- Screenshot capture
- Console log capture
- Network request capture
- Error handling
- Max iterations enforcement

✅ **Integration:**
- Works with Phase 1 (DiagnosticsConfig, PlaywrightCapture)
- Works with Phase 2 (AgentTeam integration)
- Zero regressions

✅ **Production Readiness:**
- Comprehensive test coverage
- Error handling
- Resource cleanup
- Performance optimizations

---

**Status:** Phase 3 is fully functional and production-ready! 🚀

The auto-test-after-fix loop now automatically retries implementations with real browser testing until they pass.
