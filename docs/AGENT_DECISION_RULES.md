# Agent Decision Rules

**Purpose**: Define when AI agents should act autonomously vs escalate to humans
**Last Updated**: 2026-02-16
**Project**: Agentic Company

---

## Philosophy

**Core Principle**: Agents should maximize velocity while minimizing risk. This means:
- ✅ **Automate the routine** - Agents handle repetitive, low-risk decisions
- 🤔 **Escalate the novel** - Humans handle strategic, high-risk, or unprecedented decisions
- 🔄 **Learn from escalations** - Each escalation should update these rules to prevent future escalations

**Goal**: Over time, fewer escalations as rules become more comprehensive.

---

## Autonomous Decision Authority

Agents MAY decide autonomously when ALL conditions are met:

### 1. Decision Criteria (Choose YOUR criteria)

Pick ONE authority model that fits your use case:

#### Option A: Pattern-Based Authority
Agent can decide if:
- ✅ Documented rule exists in PRIORITIES.md or DESIGN_SYSTEM.md
- ✅ Decision matches 90%+ similarity to documented example
- ✅ No conflicting rules
- ✅ Risk level: LOW (reversible, local impact only)

#### Option B: Scope-Based Authority
Agent can decide if decision is within scope:
- ✅ Code changes: < 100 lines modified
- ✅ File changes: < 5 files touched
- ✅ Time impact: < 30 minutes of work
- ✅ Cost impact: < $1 in LLM costs
- ✅ Reversibility: Git revertible (no external side effects)

#### Option C: Domain-Based Authority
Agent can decide if domain is whitelisted:
- ✅ Design decisions: Follow DESIGN_SYSTEM.md
- ✅ Priority decisions: Follow PRIORITIES.md
- ✅ Testing: Write/update tests for existing features
- ✅ Documentation: Update docs for code changes
- ✅ Refactoring: Improve code without changing behavior

#### Option D: Hybrid (Recommended)
Agent can decide if:
- ✅ Pattern-based OR scope-based authorization AND
- ✅ Domain is whitelisted AND
- ✅ Resource limits not exceeded

---

## Resource Limits

Agents MUST stay within these limits per task:

### Compute Resources
| Resource | Limit | Reasoning |
|----------|-------|-----------|
| LLM API calls | 20 calls | Prevent runaway loops |
| Total tokens | 100K tokens | Cost control (~$0.30 per task at current pricing) |
| Execution time | 10 minutes | Prevent hanging tasks |
| File reads | 50 files | Prevent excessive file scanning |
| File writes | 10 files | Limit scope of changes |

### Cost Budget
| Period | Budget | Action if Exceeded |
|--------|--------|-------------------|
| Per task | $1.00 | STOP and escalate |
| Per hour | $10.00 | STOP and escalate |
| Per day | $50.00 | STOP and escalate |

### Impact Limits
| Impact Type | Limit | Reasoning |
|-------------|-------|-----------|
| Lines of code changed | 200 lines | Large changes need review |
| Files modified | 10 files | Keep changes scoped |
| External API calls | 5 calls | Prevent rate limits |
| Database operations | 0 | Never touch prod DB autonomously |
| Deployment operations | 0 | Always require human approval |

---

## Mandatory Escalation Scenarios

Agents MUST escalate (ask human) when ANY condition is true:

### 1. Strategic Decisions
- [ ] Architecture changes (new framework, major refactor)
- [ ] API design (public-facing APIs)
- [ ] Security decisions (auth, permissions, data access)
- [ ] Business logic changes (pricing, user workflows)
- [ ] Database schema changes

### 2. High-Risk Operations
- [ ] Production deployments
- [ ] Data migrations
- [ ] Irreversible operations (delete, drop, purge)
- [ ] External system integration (new API connections)
- [ ] Financial transactions

### 3. Novel Situations
- [ ] First time encountering this type of decision
- [ ] No documented pattern in PRIORITIES.md or DESIGN_SYSTEM.md
- [ ] Conflicting rules (Rule A says X, Rule B says Y)
- [ ] User requirements unclear or ambiguous

### 4. Resource Limits Exceeded
- [ ] Approaching resource limits (>80% of any limit)
- [ ] Cost budget exceeded
- [ ] Execution time exceeded
- [ ] Unable to complete task within limits

### 5. Quality Thresholds
- [ ] Tests failing after changes
- [ ] Linting errors introduced
- [ ] Performance regression detected (>10% slower)
- [ ] Accessibility regression detected (WCAG violations)

### 6. Stakeholder Conflicts
- [ ] Requirements from different stakeholders conflict
- [ ] Priority unclear (not in PRIORITIES.md)
- [ ] Design decision not covered in DESIGN_SYSTEM.md

---

## Escalation Protocol

When escalating, agents MUST provide:

```markdown
## DECISION ESCALATION

**Decision Required**: [Clear statement of what needs deciding]

**Context**:
- [Relevant background information]
- [Current project state]
- [Why this decision arose]

**Options Considered**:

### Option A: [Name]
- **Description**: [What this option entails]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]
- **Estimated effort**: [Time/resources]
- **Risk level**: [Low/Medium/High]

### Option B: [Name]
- **Description**: [What this option entails]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]
- **Estimated effort**: [Time/resources]
- **Risk level**: [Low/Medium/High]

**Rules Applied**:
- ✅ Rule #[X] from PRIORITIES.md: [Result]
- ✅ Rule #[Y] from DESIGN_SYSTEM.md: [Result]
- ⚠️ Conflicting rule: [If applicable]

**Why Escalating**:
- [Specific reason from "Mandatory Escalation Scenarios"]
- [Any additional context]

**Recommendation** (if agent has one):
- I recommend: [Option X]
- Reasoning: [Why this option seems best]
- Confidence: [Low/Medium/High]

**What I need from you**:
- [ ] Choose between options
- [ ] Provide additional context on [specific question]
- [ ] Update [PRIORITIES.md / DESIGN_SYSTEM.md] with new rule
```

---

## Learning from Escalations

After each escalation and human decision:

### Agent Should:
1. **Document the pattern**: Add new rule to PRIORITIES.md or DESIGN_SYSTEM.md
2. **Update examples**: Add this case to "Automatic Decision Examples"
3. **Prevent future escalations**: Similar decisions should be autonomous next time

### Human Should:
1. **Provide clear reasoning**: Why did you choose Option X?
2. **Create reusable rule**: Can this apply to similar future decisions?
3. **Update decision authority**: Should agent have autonomy in this domain?

### Example Flow:

**Escalation**: "Should I use TypeScript or JavaScript for new module?"

**Human Decision**: "Use TypeScript (we standardized on it last month)"

**Learning**:
```markdown
# Add to PRIORITIES.md:

### Rule #[N]: "Always Use TypeScript for New Modules"
**Rule**: All new modules must be written in TypeScript
**When it applies**: Any new .ts/.tsx files
**Reasoning**: Team standardized on TypeScript for type safety
**Example**:
- ✅ Good: Create `newModule.ts`
- ❌ Bad: Create `newModule.js`
```

**Result**: Agent won't escalate this decision again.

---

## Agent State Verification Tests

Similar to scene graph tests for AR overlays, agents should verify their own state:

### Test Pattern: State Inspection

```python
# Example: Verify agent stayed within resource limits
def test_agent_resource_limits():
    agent = create_agent()
    task = "Refactor authentication module"

    result = agent.execute(task)

    # Verify resource limits
    assert result.llm_calls <= 20, "Exceeded LLM call limit"
    assert result.total_tokens <= 100_000, "Exceeded token limit"
    assert result.execution_time_seconds <= 600, "Exceeded time limit"
    assert result.files_modified <= 10, "Exceeded file modification limit"

    # Verify quality
    assert result.tests_passing, "Tests failed after agent changes"
    assert result.linting_passed, "Linting failed after agent changes"
```

### Test Pattern: Decision Verification

```python
def test_agent_follows_decision_rules():
    agent = create_agent()

    # Scenario: Bug vs Feature priority
    task_bug = "Fix login crash (affects 10 users)"
    task_feature = "Add dark mode (requested by 1 user)"

    decision = agent.prioritize([task_bug, task_feature])

    # Verify agent follows Rule #3: Customer Pain > Internal Tools
    assert decision[0] == task_bug, "Agent should prioritize bug affecting 10 users"
    assert decision.reasoning == "Rule #3: Higher customer pain (10 users vs 1)", \
        "Agent should cite decision rule"
```

### Test Pattern: Escalation Verification

```python
def test_agent_escalates_when_required():
    agent = create_agent()

    # Scenario: Novel architectural decision (should escalate)
    task = "Choose between GraphQL and REST for new API"

    result = agent.execute(task)

    assert result.escalated, "Agent should escalate architectural decisions"
    assert "Strategic Decision" in result.escalation_reason, \
        "Agent should cite correct escalation category"
    assert len(result.options_presented) >= 2, \
        "Agent should present multiple options"
```

---

## Adjustment Guidelines

**When to tighten rules** (reduce agent autonomy):
- Agent made costly mistakes (deployed broken code, deleted data)
- Frequent escalations that should have been autonomous
- Resource limits being exceeded regularly
- Quality regressions after agent changes

**When to loosen rules** (increase agent autonomy):
- Agent consistently makes good decisions within current scope
- Escalations reveal agent could have decided autonomously
- Team velocity improving with current autonomy level
- Resource usage well below limits

**Calibration cycle**: Review every 2 weeks, adjust limits based on:
- Number of escalations (too many? → loosen rules)
- Number of mistakes (too many? → tighten rules)
- Team feedback (trust level, velocity impact)

---

## Quick Reference

### Agent Can Decide Autonomously

✅ **Yes** - Proceed without asking:
- Design follows DESIGN_SYSTEM.md exactly
- Priority clear from PRIORITIES.md
- Code changes < 100 lines, < 5 files
- Tests pass after changes
- Reversible via git
- Cost < $1, time < 10 min

❌ **No** - Must escalate:
- Architecture decision
- Security decision
- Production deployment
- Database schema change
- Conflicting rules
- Novel situation
- Resource limits exceeded
- Tests failing

---

## Example Scenarios

### Scenario 1: "Should I fix Bug A or Bug B first?"

**Context**:
- Bug A: UI glitch (1 user report)
- Bug B: Data loss (5 user reports)

**Agent Decision Process**:
1. Check PRIORITIES.md Rule #3: Customer Pain > Internal
2. Bug B affects 5 users vs 1 user
3. Decision: Fix Bug B first
4. **Autonomous?** ✅ YES - Clear rule applies

---

### Scenario 2: "Should I refactor to use Framework X?"

**Context**:
- Current: Vanilla JavaScript
- Proposed: React framework

**Agent Decision Process**:
1. Check decision rules: Architecture change
2. Check escalation scenarios: "Strategic Decision" = YES
3. **Autonomous?** ❌ NO - Must escalate to human

**Escalation**:
```markdown
## DECISION ESCALATION

**Decision Required**: Should we refactor to use React framework?

**Options Considered**:
- Option A: Keep vanilla JS (current)
- Option B: Migrate to React

**Why Escalating**: Strategic/architectural decision

**Recommendation**: Need human decision on framework choice
```

---

### Scenario 3: "Should I increase button size from 40px to 44px?"

**Context**:
- Current: 40px × 40px button
- DESIGN_SYSTEM.md says: "Minimum button size: 44px × 44px (iOS HIG)"

**Agent Decision Process**:
1. Check DESIGN_SYSTEM.md: Rule exists
2. Current size violates rule (40px < 44px)
3. Decision: Increase to 44px
4. **Autonomous?** ✅ YES - Following documented rule

---

## Document Maintenance

- **Review frequency**: Every 2 weeks
- **Update triggers**:
  - After each escalation (add new rule)
  - When resource limits reached (adjust limits)
  - After agent mistakes (tighten rules)
  - When agent could have decided (loosen rules)
- **Owner**: [Your team lead or project owner]

---

**Document Version**: 1.0
**Last Updated**: 2026-02-16
**Next Review**: [Set 2-week reminder]
