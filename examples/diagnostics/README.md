# Diagnostics Examples

This directory contains example action files for browser automation testing with Agenticom diagnostics.

## Quick Start

```bash
# Simple screenshot test
agenticom test-diagnostics https://example.com -a examples/diagnostics/simple_screenshot.json --headed

# Login flow test (requires local server)
agenticom test-diagnostics http://localhost:3000 -a examples/diagnostics/login_test.json --headed

# API data loading test (requires local server)
agenticom test-diagnostics http://localhost:3000 -a examples/diagnostics/api_test.json --headless
```

## Example Files

### `simple_screenshot.json`
Basic example that navigates to a page and takes a screenshot.

**Use case:** Verify a page loads correctly

```bash
agenticom test-diagnostics https://example.com -a examples/diagnostics/simple_screenshot.json
```

### `login_test.json`
Tests a complete login flow with form input and navigation.

**Use case:** Verify login functionality works end-to-end

**Requirements:** Local server running on port 3000 with login form

```bash
agenticom test-diagnostics http://localhost:3000/login -a examples/diagnostics/login_test.json
```

**Actions:**
1. Navigate to /login
2. Wait for login form
3. Type email address
4. Type password
5. Click submit button
6. Wait for dashboard to load
7. Take screenshot

### `api_test.json`
Tests API data fetching and display.

**Use case:** Verify API integration and data rendering

**Requirements:** Local server running on port 3000 with data table

```bash
agenticom test-diagnostics http://localhost:3000/dashboard -a examples/diagnostics/api_test.json
```

**Actions:**
1. Navigate to /dashboard
2. Wait for data table to load
3. Take screenshot (initial state)
4. Click refresh button
5. Wait for refresh
6. Take screenshot (after refresh)

## Action File Format

Action files are JSON with the following structure:

```json
{
  "description": "Human-readable description of what this tests",
  "url": "Base URL for the test",
  "actions": [
    {
      "type": "navigate",
      "value": "https://example.com"
    },
    {
      "type": "wait_for_selector",
      "selector": "#element-id",
      "timeout": 5000
    },
    {
      "type": "click",
      "selector": "#button-id"
    },
    {
      "type": "type",
      "selector": "#input-id",
      "value": "text to type"
    },
    {
      "type": "screenshot",
      "value": "screenshot_name.png"
    },
    {
      "type": "wait",
      "value": "2000"
    }
  ],
  "expected": {
    "no_console_errors": true,
    "final_url": "https://example.com/success",
    "network_requests_include": ["/api/endpoint"]
  }
}
```

## Supported Action Types

### `navigate`
Navigate to a URL.
```json
{"type": "navigate", "value": "https://example.com"}
```

### `click`
Click an element.
```json
{"type": "click", "selector": "#button-id"}
```

### `type`
Type text into an input field.
```json
{"type": "type", "selector": "#email", "value": "user@example.com"}
```

### `wait_for_selector`
Wait for an element to appear.
```json
{"type": "wait_for_selector", "selector": "#dashboard", "timeout": 5000}
```

### `wait`
Wait for a fixed duration (milliseconds).
```json
{"type": "wait", "value": "2000"}
```

### `screenshot`
Take a screenshot.
```json
{"type": "screenshot", "value": "page.png"}
```

## Creating Your Own Tests

1. **Identify the user flow** - What steps does a user take?
2. **Map to actions** - Convert each step to an action
3. **Add waits** - Ensure elements are loaded before interacting
4. **Add screenshots** - Capture key states for verification
5. **Test manually first** - Run with `--headed` to see what happens

## Tips

- **Use `--headed` during development** to see what's happening
- **Add explicit waits** for dynamic content
- **Use specific selectors** (IDs are better than classes)
- **Take screenshots** at key points for debugging
- **Check console errors** - they're captured automatically

## Integration with Workflows

You can use these tests in workflow YAML files:

```yaml
steps:
  - id: implement_login
    agent: developer
    input: "Implement login page"
    metadata:
      diagnostics_enabled: true
      test_url: "http://localhost:3000/login"
      test_actions:
        - type: navigate
          value: "http://localhost:3000/login"
        - type: wait_for_selector
          selector: "#login-form"
        - type: screenshot
          value: "login_page.png"
```

The workflow will automatically run these tests after each implementation attempt, retrying until tests pass.

## Troubleshooting

**Browser won't launch:**
```bash
playwright install chromium
```

**Element not found:**
- Use `--headed` to see the page
- Add `wait_for_selector` before interacting
- Check selector is correct (use browser DevTools)

**Timeout errors:**
- Increase timeout: `"timeout": 10000` (10 seconds)
- Add explicit wait before the action
- Check if page is actually loading

**Screenshots not saved:**
```bash
mkdir -p outputs/diagnostics
chmod 755 outputs/diagnostics
```

## Next Steps

- See `docs/diagnostics.md` for full documentation
- Run `agenticom diagnostics` to check system status
- Use `agenticom build-criteria` to generate success criteria
- Integrate with workflows for automated testing
