---
name: tdd-patterns
description: Test-driven development patterns for comprehensive test suites. Use when creating unit tests, integration tests, or test plans. Covers test structure, edge cases, mocking, and coverage strategies.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# TDD Patterns

## When to Use
Use when writing any test suite — unit, integration, or end-to-end.

## Do Not Use When
Writing exploratory scripts or one-off debugging code.

## Step-by-Step

1. **Arrange-Act-Assert structure**: Every test must have three clear sections:
   - Arrange: set up inputs, mocks, and preconditions
   - Act: call the function/method under test (one action per test)
   - Assert: verify the output and side effects

2. **Name tests descriptively**:
   - Pattern: `test_<function>_<scenario>_<expected_outcome>`
   - Example: `test_create_user_with_duplicate_email_raises_value_error`

3. **Cover these scenario categories for every function**:
   - Happy path (valid inputs, expected output)
   - Empty/null/zero inputs
   - Boundary values (min, max, one over/under)
   - Invalid types or formats
   - Error conditions (what should raise?)

4. **Mock external dependencies**: Never hit real databases, APIs, or file systems in unit tests. Use `unittest.mock.patch` or `pytest-mock`.

5. **Assert specifics, not truthiness**:
   - Bad:  `assert result`
   - Good: `assert result.status_code == 200`
   - Good: `assert "error" not in result.json()`

6. **One logical assertion per test**: Multiple assertions hide which one failed.

7. **Test the contract, not the implementation**: Tests should not know about internal variable names or private methods.

## Coverage Targets
- New functions: 100% line coverage
- Integration paths: at least one test per code path through the API layer
- Error handlers: test that errors are raised, not just that the code runs
