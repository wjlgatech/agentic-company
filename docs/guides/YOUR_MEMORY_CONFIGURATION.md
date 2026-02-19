# Your Memory System Configuration

Based on your answers to the 5 key questions:

## Configuration Summary

| Question | Your Answer | Configuration Value |
|----------|-------------|-------------------|
| **Q1**: Tolerance for worse performance | 5% | `max_acceptable_degradation_pct = 0.05` |
| **Q2**: Parameter tuning frequency | Weekly | `tuning_interval_days = 7` |
| **Q3**: Success criteria | 5% improvement | `target_improvement_pct = 0.05` |
| **Q4**: Alert recipients | Both eng + product | `alert_recipients["critical"] = ["eng", "product"]` |
| **Q5**: Relevance vs coverage | High threshold (0.80) | `similarity_threshold = 0.80` |

---

## Your Profile: "Conservative Quality-First"

You've chosen a configuration that prioritizes:
- ✅ **Quality over quantity** - Only show highly relevant lessons (80%+ match)
- ✅ **User trust** - Better to show nothing than show bad advice
- ✅ **Steady improvement** - Weekly tuning with realistic 5% goal
- ✅ **Shared ownership** - Eng + product teams both alerted to critical issues
- ✅ **Room to experiment** - 5% tolerance allows testing without being too risky

---

## What This Means in Practice

### Week 1: Launch

**Expected Metrics**:
```
✓ Retrieval relevance: 0.75-0.80 (high quality)
⚠ Coverage: 35-45% (lower due to high threshold)
? Success improvement: 0-5% (early days)
```

**What you'll see**:
- Workflows get 2-3 lessons (not 5-7)
- But those 2-3 are spot-on
- About half of workflows get no lessons (threshold too high for them)

**Action**: Monitor if the lessons retrieved are actually helping workflows succeed.

### Week 2: First Tuning Cycle

**The Key Question**: Did we hit 5% improvement?

**Scenario A**: Yes, we're at 6% improvement ✓
- **Action**: Lock in threshold at 0.80
- **Focus**: Expand coverage by adding more diverse lessons
- **Celebrate**: Memory is working!

**Scenario B**: No, we're at 2% improvement ✗
- **Action**: Run A/B test: 0.75 vs 0.80 vs 0.78
- **Focus**: Find the threshold sweet spot
- **Timeline**: 2 weeks to conclude test

### Weeks 3-4: Optimization

**If coverage is too low** (< 35%):
```python
# Option 1: Lower threshold for "content" cluster
cluster_threshold_adjustments = {
    "code": 0.0,        # Keep 0.80 (precision matters)
    "content": -0.05,   # Drop to 0.75 (more diversity)
    "analysis": 0.0,    # Keep 0.80 (precision matters)
}

# Option 2: Extract more lessons from recent successful workflows

# Option 3: Manually seed high-quality lessons for common patterns
```

**If relevance drops** (< 0.70):
```python
# Option 1: Audit recently approved lessons - reject bad ones
# Option 2: Raise threshold to 0.82
# Option 3: Improve embeddings (use better model)
```

### Steady State (Week 5+)

**Target Metrics**:
```
✓ Success improvement: 5-8%
✓ Retrieval relevance: 0.72-0.78
✓ Coverage: 40-50%
✓ P95 latency: < 300ms
✓ User satisfaction: > 4.0/5.0
```

**Weekly Rhythm**:
- **Monday 9am**: Automated tuning runs
  - Adjusts threshold ±5% based on past week's data
  - Sends summary email to eng team

- **Monday 10am**: Eng reviews tuning
  - Override if adjustment seems wrong
  - Approve new lessons proposed by LLM

- **Friday 3pm**: Weekly metrics report
  - Sent to eng + product teams
  - Includes: improvement %, top lessons, coverage, alerts

---

## Alert Examples

### 🎉 INFO: Excellent Performance

```
Title: Excellent Memory Performance! 🎉
Message: Workflow improvement with lessons is 12.0%, well above target!

Recipients: eng

Recommended Action:
  Continue monitoring. Document what's working well.
  Consider expanding lesson coverage to other domains.
```

### ⚠️ WARNING: Below Target

```
Title: Improvement Below 5% Target
Message: Workflow improvement with lessons is 3.0%, below target of 5%.
         Memory is helping, but not meeting goals.

Recipients: eng

Recommended Action:
  Review lesson quality. Extract better lessons from top-performing workflows.
  Consider lowering similarity threshold slightly to increase coverage.
```

### 🚨 CRITICAL: Memory Making Things Worse

```
Title: Memory Degrading Workflow Success
Message: Workflows with lessons are 8.0% WORSE than without.
         This exceeds the 5% tolerance threshold.

Recipients: eng, product  👈 BOTH TEAMS ALERTED

Recommended Action:
  DISABLE MEMORY IMMEDIATELY and investigate.

  Potential causes:
  (1) Bad lessons recently approved
  (2) Retrieval algorithm broken
  (3) Lessons being applied incorrectly

  DO NOT RE-ENABLE until root cause found and fixed.
```

---

## Runbook: When Things Go Wrong

### Scenario 1: Improvement Goes Negative

**Trigger**: `improvement < -5%` (workflows with lessons are 5%+ worse)

**Immediate Actions** (within 1 hour):
1. **Disable memory retrieval**
   ```python
   ENABLE_MEMORY_RETRIEVAL = False
   ```
2. **Alert eng + product teams** (automatic)
3. **Preserve data** - don't delete anything, need it for investigation

**Investigation** (within 24 hours):
1. Check recently approved lessons (last 7 days)
   - Are any obviously bad?
   - Reject suspicious lessons
2. Check retrieval relevance
   - Has it dropped suddenly?
   - If yes, retrieval algorithm is broken
3. Check workflow errors
   - Are specific error types spiking?
   - Are workflows misinterpreting lessons?

**Resolution**:
- If bad lessons: Reject them, re-enable memory
- If retrieval broken: Fix algorithm, test on historical data, re-enable
- If workflow interpretation issue: Fix how lessons are presented/applied

**Timeline**: Aim to re-enable within 2-3 days maximum.

### Scenario 2: Coverage Drops Below 35%

**Trigger**: `coverage < 0.35` (only 35% of workflows find lessons)

**This is expected** with threshold = 0.80, but still monitor.

**Actions**:
1. Check if recent workflows are in new domains
   - Extract lessons from these domains
2. Consider cluster-specific threshold
   - Lower threshold for underserved clusters
3. Manually seed lessons for common patterns

**Decision Point**:
- If coverage stays < 35% for 2 weeks: Lower threshold to 0.78
- If improvement is still > 5%: Accept lower coverage (quality > quantity)

### Scenario 3: Users Report "No Helpful Lessons"

**Trigger**: `satisfaction < 3.0/5.0` for 1 week

**Investigation**:
1. **Qualitative feedback** - what are users saying?
   - "No lessons at all" → Coverage problem
   - "Lessons not relevant" → Relevance problem (threshold too low?)
   - "Lessons too obvious" → Need deeper insights
   - "Lessons too complex" → Need simpler recommendations

2. **Check metrics correlation**:
   ```python
   if satisfaction < 3.0 and relevance > 0.75:
       # High relevance but low satisfaction
       # Problem: Lessons are technically relevant but not *helpful*
       # Action: Improve lesson content quality, not retrieval

   if satisfaction < 3.0 and coverage < 0.40:
       # Low coverage
       # Problem: Not finding lessons for user's tasks
       # Action: Extract more lessons or lower threshold
   ```

**Resolution**:
- Gather specific examples from unhappy users
- Review those specific lessons - what's wrong?
- Update lesson extraction prompt to address issues

---

## A/B Testing Protocol

### When to A/B Test

**DO test when**:
- Making significant parameter changes (threshold ±0.05 or more)
- Trying new retrieval algorithms
- Changing lesson content structure
- Unsure if a change will help or hurt

**DON'T test when**:
- Making tiny adjustments (threshold ±0.01)
- Fixing obvious bugs
- Emergency situations

### Example: Testing Threshold Values

**Hypothesis**: Lowering threshold from 0.80 to 0.75 will improve coverage without hurting success rate.

**Setup**:
```python
variants = {
    "control":   {"similarity_threshold": 0.80},  # Current
    "variant_a": {"similarity_threshold": 0.75},  # Lower
    "variant_b": {"similarity_threshold": 0.78},  # Middle
}

traffic_split = {
    "control":   0.40,  # 40% of workflows
    "variant_a": 0.30,  # 30%
    "variant_b": 0.30,  # 30%
}

duration = 14  # days
```

**Measure**:
- **Primary**: Workflow success rate (with vs without lessons)
- **Secondary**: Retrieval relevance, coverage, latency

**Decision Criteria**:
| Metric | Control | Variant A | Variant B | Winner |
|--------|---------|-----------|-----------|--------|
| Success improvement | +5% | +6% | +5.5% | A |
| Relevance | 0.76 | 0.71 | 0.74 | Control |
| Coverage | 0.42 | 0.55 | 0.48 | A |

**Recommendation**: Ship Variant A (0.75)
- **Why**: Better improvement (+6% vs +5%), much better coverage (0.55 vs 0.42)
- **Trade-off**: Slightly lower relevance (0.71 vs 0.76) is acceptable
- **Net benefit**: Worth the small relevance drop for significant coverage gain

---

## Configuration Files

Your configuration is stored in:
- **`orchestration/memory_config.py`** - Main configuration
- **`~/.agenticom/lessons.json`** - Stored lessons
- **`~/.agenticom/memory_metrics.json`** - Historical metrics

### Key Configuration Values

```python
from orchestration.memory_config import get_memory_config

config = get_memory_config()

# Retrieval
config.similarity_threshold                    # 0.80
config.get_threshold_for_cluster("content")    # 0.75 (adjusted)
config.max_lessons_per_query                   # 5

# Targets
config.target_improvement_pct                  # 0.05 (5%)
config.max_acceptable_degradation_pct          # 0.05 (5%)
config.target_retrieval_relevance              # 0.70
config.target_coverage                         # 0.45 (lower due to high threshold)

# Tuning
config.tuning_interval_days                    # 7 (weekly)
config.auto_tune_enabled                       # True
config.tuning_learning_rate                    # 0.05 (5% adjustment)

# Alerts
config.alert_recipients["critical"]            # ["eng", "product"]
config.alert_check_interval_hours              # 6 (4x per day)
```

---

## Next Steps

### Immediate (Before Launch)
1. ✅ Configuration created - `orchestration/memory_config.py`
2. ⬜ Test configuration with sample data
3. ⬜ Set up alert endpoints (Slack webhook)
4. ⬜ Create weekly report template

### Week 1 (Launch)
1. ⬜ Deploy with threshold = 0.80
2. ⬜ Monitor metrics dashboard daily
3. ⬜ Collect user feedback on lesson quality
4. ⬜ Document any immediate issues

### Week 2 (First Tuning)
1. ⬜ Run first automated tuning cycle
2. ⬜ Review tuning recommendations
3. ⬜ Decide: lock in 0.80 or A/B test lower thresholds
4. ⬜ Send weekly report to eng + product

### Week 3-4 (Optimization)
1. ⬜ Execute A/B test if needed
2. ⬜ Extract more lessons for underserved domains
3. ⬜ Fine-tune cluster-specific thresholds
4. ⬜ Establish baseline metrics

### Week 5+ (Steady State)
1. ⬜ Monitor weekly
2. ⬜ Approve new lessons as proposed
3. ⬜ Archive inactive lessons monthly
4. ⬜ Adjust parameters as data suggests

---

## Success Criteria

After 4 weeks, you should see:

| Metric | Target | Status |
|--------|--------|--------|
| Success improvement | ≥ 5% | ⬜ |
| Retrieval relevance | 0.70-0.78 | ⬜ |
| Coverage | 40-50% | ⬜ |
| P95 latency | < 300ms | ⬜ |
| User satisfaction | ≥ 4.0/5.0 | ⬜ |
| Alert rate | < 2 warnings/week | ⬜ |

If all checks pass → **Memory system is successful!**

If any fail → Use runbook to diagnose and fix.

---

## Questions?

Your configuration is designed for:
- **Conservative start** (high threshold, realistic targets)
- **Data-driven tuning** (weekly adjustments based on metrics)
- **Safety** (5% tolerance, automated alerts)
- **Cross-functional visibility** (eng + product both involved)

This is a solid foundation. Adjust as you learn from real data.

**Remember**: The ONE metric that matters is `improvement` (success with lessons vs without). Everything else is in service of that.
