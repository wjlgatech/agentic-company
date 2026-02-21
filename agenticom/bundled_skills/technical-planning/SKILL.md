---
name: technical-planning
description: Structured technical task breakdown and planning. Use when decomposing feature requests into implementable tasks with acceptance criteria, dependency ordering, and risk assessment.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# Technical Planning

## When to Use
Use when breaking down a feature request or user story into implementable tasks.

## Do Not Use When
The request is already broken down into specific implementation tasks.

## Step-by-Step

1. **Restate the goal**: In one sentence, what problem does this feature solve for the user?

2. **Identify the system boundary**: What components does this touch?
   - Data layer (schema changes, new tables/fields)
   - Business logic layer (new services, modified functions)
   - API layer (new endpoints, changed contracts)
   - UI layer (new screens, changed flows)

3. **Break into atomic tasks** using INVEST criteria:
   - Independent: each task can be implemented and tested on its own
   - Negotiable: scope can be adjusted without breaking other tasks
   - Valuable: delivers something observable
   - Estimable: concrete enough to scope
   - Small: completable in one development session
   - Testable: has clear acceptance criteria

4. **For each task, define**:
   - What to implement (concrete, not vague)
   - Acceptance criteria (measurable, binary pass/fail)
   - Dependencies (must be done before this task)

5. **Risk assessment** (for each task, note if it):
   - Touches shared infrastructure (database schema, auth middleware)
   - Requires new external dependencies
   - Has performance implications at scale
   - Changes existing API contracts

6. **Output format**:
   ```
   ## Goal: [one sentence]
   ## Tasks:
   1. [Task name]
      - What: [concrete description]
      - Accepts: [measurable criteria]
      - Depends on: [task numbers or "none"]
      - Risk: [low/medium/high + reason]
   ## Dependencies diagram: [optional]
   ```
