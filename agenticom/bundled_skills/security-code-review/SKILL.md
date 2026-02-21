---
name: security-code-review
description: Security-focused code review using OWASP Top 10 patterns. Use when verifying or reviewing code for injection, authentication, authorization, data exposure, and other security vulnerabilities.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# Security Code Review

## When to Use
Use when reviewing code that handles user input, authentication, authorization, or sensitive data.

## Do Not Use When
Reviewing pure data transformation logic with no external inputs or user-controlled values.

## Step-by-Step

Check each OWASP Top 10 category relevant to the code:

1. **Injection (SQL, shell, template)**
   - Is user input used directly in SQL queries? → require parameterized queries
   - Is user input passed to shell commands? → require allowlist validation
   - Is user input rendered in templates? → require escaping

2. **Broken Authentication**
   - Are passwords hashed with bcrypt/argon2 (not md5/sha1)?
   - Are JWTs validated for signature, expiry, and algorithm (`alg != 'none'`)?
   - Is token rotation enforced on privilege escalation?

3. **Sensitive Data Exposure**
   - Is PII or credentials logged?
   - Are secrets hardcoded (scan for `password =`, `api_key =`, `secret =`)?
   - Is sensitive data returned in API responses unnecessarily?

4. **Broken Access Control**
   - Does every API endpoint verify the caller has permission for the resource?
   - Are there IDOR risks (can user A access user B's data by changing an ID)?

5. **Security Misconfiguration**
   - Are CORS origins restricted (not `*` in production)?
   - Are error responses generic (not stack traces) for unauthenticated callers?

6. **Rate Limiting**
   - Are login, registration, and password-reset endpoints rate-limited?

## Output Format
For each finding:
```
[CRITICAL|HIGH|MEDIUM|LOW] — Category — Location
Issue: [describe the vulnerability]
Fix: [concrete remediation]
```
