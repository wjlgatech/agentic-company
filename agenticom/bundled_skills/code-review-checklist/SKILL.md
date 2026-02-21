---
name: code-review-checklist
description: Production-readiness code review checklist. Use when reviewing code for quality, security, maintainability, and deployment safety. Covers correctness, error handling, security patterns, and observability.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# Code Review Checklist

## When to Use
Use when performing a final code review before production approval.

## Do Not Use When
Reviewing documentation, plans, or non-code artifacts.

## Step-by-Step

1. **Correctness**
   - Does the code handle the happy path correctly?
   - Are edge cases handled (null inputs, empty lists, zero values)?
   - Are boundary conditions correct (off-by-one, inclusive/exclusive ranges)?

2. **Error handling**
   - Are exceptions caught at the right level?
   - Do error messages give enough context to debug?
   - Are resources properly cleaned up (files, connections, locks)?

3. **Security** (flag any of these as CRITICAL):
   - No hardcoded secrets, tokens, or passwords
   - User inputs are validated and sanitized before use
   - SQL/shell/template injection risks are mitigated
   - Authentication checks are present where required
   - Sensitive data is not logged

4. **Performance**
   - No N+1 query patterns (DB calls inside loops)
   - No unbounded loops or recursion without termination guarantee
   - Large payloads are streamed, not buffered entirely in memory

5. **Observability**
   - Meaningful log messages at key decision points
   - Errors logged with context (not silently swallowed)
   - Metrics emitted for latency-sensitive paths

6. **Deployment safety**
   - Database migrations are backward-compatible
   - No breaking API changes without versioning
   - Feature flags used for risky rollouts

## Output Format
```
CRITICAL issues (block deployment): ...
WARNINGS (should fix): ...
SUGGESTIONS (consider): ...

VERDICT: APPROVED FOR PRODUCTION | MAJOR REWORK REQUIRED
```
