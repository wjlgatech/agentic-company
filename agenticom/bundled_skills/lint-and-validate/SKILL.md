---
name: lint-and-validate
description: Systematic output validation checklist. Use when verifying or reviewing any agent output against acceptance criteria. Ensures specificity, measurability, and completeness of verification reports.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# Lint and Validate

## When to Use
Use this skill when cross-checking any implementation, plan, or document against stated acceptance criteria.

## Do Not Use When
Output is purely creative (no measurable criteria exist).

## Step-by-Step

1. **Map criteria to evidence**: For each acceptance criterion, identify the specific line of output that satisfies it. Quote it explicitly — do not paraphrase.

2. **Score each criterion**:
   - PASS: Criterion is fully met with concrete evidence
   - PARTIAL: Criterion is addressed but incompletely (explain gap)
   - FAIL: Criterion is missing or contradicted (explain why)

3. **Check specificity**: Reject vague conclusions like "looks good" or "seems correct". Every verdict must cite specific output lines.

4. **Check measurability**: Quantitative criteria (response time < 200ms, test coverage > 80%) must have numbers in the output, not just assertions.

5. **Check completeness**: Are ALL criteria covered? Unaddressed criteria are implicit FAILs.

6. **Produce a structured verdict**:
   ```
   CRITERION 1 — [name]: PASS | PARTIAL | FAIL
   Evidence: "[exact quote from output]"
   Gap (if any): ...

   OVERALL: VERIFIED | ISSUES FOUND
   ```

## Best Practices
- Be the critic, not the cheerleader. Your job is to find gaps, not to approve work.
- If the output contains "TODO", "placeholder", or "stub" — flag as PARTIAL at best.
- A single FAIL criterion means the overall verdict is ISSUES FOUND, not VERIFIED.
