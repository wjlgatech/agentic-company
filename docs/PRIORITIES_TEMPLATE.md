# Priority Framework Template

**Purpose**: Document decision rules and context to automate 60% of priority decisions
**Last Updated**: [DATE]
**Project**: [Your Project Name]

---

## How to Use This Template

1. **Copy this file** to your project root as `PRIORITIES.md`
2. **Fill in the bracketed sections** with your project's values
3. **Update "Current Context"** weekly or when priorities shift
4. **Add new decision rules** as you discover repeated priority conflicts
5. **Keep it current** - outdated context is worse than no context

**Goal**: Enable Claude (or any AI assistant) to make 60% of priority decisions automatically by checking this document.

---

## Decision Rules (Sorted by Priority)

### 1. [Rule Name - e.g., "Safety/Security Always Wins"]
**Rule**: [Clear, actionable rule]
**When it applies**: [Specific conditions]
**Example**:
- ✅ Good: [Example of following rule]
- ❌ Bad: [Example of violating rule]

### 2. [Rule Name - e.g., "Blocking Bugs > New Features"]
**Rule**: [Clear rule]
**When it applies**: [Conditions]
**Example**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

### 3. [Rule Name - e.g., "Customer Pain > Internal Tools"]
**Rule**: [Clear rule]
**When it applies**: [Conditions - e.g., "When 5+ support tickets about same issue"]
**Example**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

### 4. [Rule Name - e.g., "Deadline Pressure → Ship Good Enough"]
**Rule**: [Clear rule - e.g., "When deadline < 3 days, prefer working over perfect"]
**When it applies**: [Conditions]
**Example**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

### 5. [Rule Name - e.g., "Unblock Others First"]
**Rule**: [Clear rule]
**When it applies**: [Conditions]
**Example**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

---

## Current Context

**Last Updated**: [DATE - Update this weekly!]

### Active Sprint/Cycle
**Sprint Goal**: [e.g., "Launch MVP to 10 beta users"]
**End Date**: [DATE]
**Success Criteria**:
1. [Criterion 1]
2. [Criterion 2]
3. [Criterion 3]

### Immediate Priorities (Next 7 Days)
1. **[Priority 1 - e.g., "Fix login bug"]**
   - **Why**: [Reason - e.g., "Blocking 3 beta testers"]
   - **Owner**: [Name]
   - **Deadline**: [DATE]

2. **[Priority 2]**
   - **Why**: [Reason]
   - **Owner**: [Name]
   - **Deadline**: [DATE]

3. **[Priority 3]**
   - **Why**: [Reason]
   - **Owner**: [Name]
   - **Deadline**: [DATE]

### Medium-Term Goals (Next 30 Days)
1. **[Goal 1]**
   - **Milestone**: [Description]
   - **Status**: [Not Started / In Progress / Blocked]

2. **[Goal 2]**
   - **Milestone**: [Description]
   - **Status**: [Status]

### Stakeholder Priorities
**[Stakeholder 1 - e.g., "CEO"]**:
- Top concern: [e.g., "User growth"]
- Willing to trade: [e.g., "Internal tooling improvements"]

**[Stakeholder 2 - e.g., "Engineering Lead"]**:
- Top concern: [e.g., "Technical debt"]
- Willing to trade: [e.g., "Feature velocity in short term"]

**[Stakeholder 3 - e.g., "Customer Success"]**:
- Top concern: [e.g., "Support ticket volume"]
- Willing to trade: [e.g., "Advanced features"]

### Current Constraints
- **Budget**: [e.g., "$50K remaining, 60% burned"]
- **Team Capacity**: [e.g., "2 engineers, 1 designer"]
- **Tech Debt**: [e.g., "15% of sprints allocated to refactoring"]
- **External Dependencies**: [e.g., "Waiting on API access from Partner X"]

### Active Incidents/Blockers
1. **[Incident/Blocker 1]**
   - **Impact**: [e.g., "3 customers affected"]
   - **Status**: [e.g., "Investigating - ETA 2 hours"]

2. **[Incident/Blocker 2]**
   - **Impact**: [Description]
   - **Status**: [Status]

---

## Automatic Decision Examples

Use this section to document HOW the decision rules apply in practice.

### Example 1: "Should I work on Feature X or Bug Y?"

**Context**:
- Feature X: New analytics dashboard (requested by 1 customer)
- Bug Y: Search results showing duplicates (reported by 8 customers)

**Decision Process**:
1. Check Rule #3: Customer Pain > Internal Tools
   - Bug Y affects 8 customers → High customer pain
   - Feature X requested by 1 customer → Lower priority
2. **Decision**: Work on Bug Y first

**Automatic?** ✅ YES - Claude can decide this from rules + context

---

### Example 2: "Should I refactor Module A or build Feature B?"

**Context**:
- Module A: Tech debt, working but hard to maintain
- Feature B: New feature, in sprint goal
- Sprint ends in 2 days

**Decision Process**:
1. Check Rule #4: Deadline Pressure → Ship Good Enough
   - Deadline < 3 days → Defer non-critical work
2. Check "Active Sprint/Cycle": Feature B in sprint goal
3. **Decision**: Build Feature B, defer refactoring

**Automatic?** ✅ YES - Rules + context provide clear answer

---

### Example 3: "Should I optimize Algorithm X or add Feature Y?"

**Context**:
- Algorithm X: Currently 500ms, could optimize to 100ms
- Feature Y: New onboarding flow
- No performance complaints from users

**Decision Process**:
1. Check Rule #3: Customer Pain > Internal Tools
   - No user complaints → Low customer pain
2. Check "Medium-Term Goals": Improve onboarding (contains Feature Y)
3. **Decision**: Build Feature Y

**Automatic?** ✅ YES - Clear priority from goals

---

### Example 4: "Should I use Framework A or B for new feature?"

**Context**:
- Framework A: Team familiar, slower
- Framework B: Team unfamiliar, faster

**Decision Process**:
1. Check decision rules: No rule covers architectural decisions
2. Check constraints: Team capacity is limited
3. **Decision**: [ESCALATE TO HUMAN]
   - Reason: Trade-off between team familiarity and performance
   - Requires judgment on team learning capacity

**Automatic?** ❌ NO - Requires human judgment

---

## When to Escalate to Human

Claude (or any AI assistant) should escalate when:

1. **No applicable rule**: Decision doesn't match any existing rule
2. **Conflicting rules**: Multiple rules point to different priorities
3. **Missing context**: Required information not in this document
4. **Strategic decision**: Long-term architectural or business decision
5. **Novel situation**: First time encountering this type of decision
6. **Stakeholder conflict**: Different stakeholders want different things
7. **High-risk decision**: Potential for significant negative impact

### Escalation Template

When escalating, Claude should provide:

```
PRIORITY DECISION ESCALATION

Decision: [What needs deciding]

Options:
- Option A: [Description]
- Option B: [Description]

Context:
- [Relevant context from this document]

Rules Applied:
- Rule #X: [Result]
- Rule #Y: [Result]

Why Escalating:
- [Reason for escalation - e.g., "Conflicting rules", "Missing context"]

Recommendation:
- [Claude's suggestion, if any]
- [Reasoning]
```

---

## Priority Calculation Matrix (Optional)

For more complex prioritization, use this scoring system:

| Factor | Weight | Score (1-5) | Weighted Score |
|--------|--------|-------------|----------------|
| Customer Impact | 40% | [1-5] | [Weight × Score] |
| Business Value | 30% | [1-5] | [Weight × Score] |
| Effort (inverse) | 20% | [1-5] | [Weight × Score] |
| Technical Debt Reduction | 10% | [1-5] | [Weight × Score] |
| **TOTAL** | 100% | - | **[Sum]** |

**How to use**:
1. Score each factor 1-5 (5 = highest priority)
2. Multiply by weight
3. Sum weighted scores
4. Higher total = higher priority

**Example**:
```
Task A: New user dashboard
- Customer Impact: 5 × 40% = 2.0
- Business Value: 4 × 30% = 1.2
- Effort (inverse): 3 × 20% = 0.6
- Tech Debt: 2 × 10% = 0.2
- TOTAL: 4.0

Task B: Refactor auth module
- Customer Impact: 2 × 40% = 0.8
- Business Value: 2 × 30% = 0.6
- Effort (inverse): 4 × 20% = 0.8
- Tech Debt: 5 × 10% = 0.5
- TOTAL: 2.7

Decision: Task A (4.0) > Task B (2.7) → Work on dashboard first
```

---

## Change Log

| Date | Change | Reason | Updated By |
|------|--------|--------|------------|
| [DATE] | Initial creation | Establish priority framework | [Name] |

---

## Quick Reference

**Most Common Priority Questions**:

Q: Should I fix this bug or add this feature?
→ Check Rule #2 (Blocking Bugs > Features) + "Active Incidents/Blockers"

Q: Should I work on X or Y?
→ Check "Immediate Priorities (Next 7 Days)" for explicit ordering

Q: Is this worth doing now?
→ Check "Active Sprint/Cycle" - is it in sprint goal?

Q: Should I perfect this or ship it?
→ Check Rule #4 (Deadline Pressure) + "Active Sprint/Cycle" end date

Q: Should I refactor or build new?
→ Check "Current Constraints" tech debt allocation + "Immediate Priorities"

---

**Document Version**: 1.0
**Last Updated**: [DATE]
**Next Review Date**: [DATE - Schedule weekly reviews]
