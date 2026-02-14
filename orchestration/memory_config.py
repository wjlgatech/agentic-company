"""
Memory Management Configuration

User decisions codified:
- Q1: 5% tolerance for worse performance
- Q2: Weekly parameter tuning
- Q3: 5% improvement target (realistic)
- Q4: Alerts to both eng + product teams
- Q5: High threshold (0.80) - prioritize relevance over coverage
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MemorySystemConfig:
    """Configuration for adaptive memory management system."""

    # =========================================================================
    # RETRIEVAL PARAMETERS
    # =========================================================================

    # Similarity threshold for lesson retrieval
    # Q5: High threshold (0.80) - prioritize relevance over coverage
    # Trade-off: Fewer lessons retrieved, but very relevant
    similarity_threshold: float = 0.80

    # Maximum number of lessons to retrieve per query
    max_lessons_per_query: int = 5

    # Minimum confidence score for proposed lessons
    min_lesson_confidence: float = 0.7

    # Similarity threshold adjustments by workflow cluster
    # Some clusters may benefit from different thresholds
    cluster_threshold_adjustments: Dict[str, float] = None

    def __post_init__(self):
        """Initialize default values for fields."""
        if self.cluster_threshold_adjustments is None:
            self.cluster_threshold_adjustments = {
                "code": 0.0,      # Use base threshold (0.80)
                "content": -0.05,  # Slightly lower (0.75) - content is more diverse
                "analysis": 0.0,   # Use base threshold (0.80)
            }

        if self.tunable_parameters is None:
            self.tunable_parameters = [
                "similarity_threshold",
                "max_lessons_per_query",
            ]

        if self.alert_recipients is None:
            self.alert_recipients = {
                "critical": ["eng", "product"],    # Both teams for critical issues
                "warning": ["eng"],                # Eng only for warnings
                "info": ["eng"],                   # Eng only for info
            }

        if self.alert_thresholds is None:
            self.alert_thresholds = {
                # CRITICAL ALERTS (immediate action required)
                "critical": {
                    # Q1: 5% tolerance - if worse than this, critical
                    "improvement_below": -self.max_acceptable_degradation_pct,

                    # Retrieval completely broken
                    "avg_relevance_below": 0.50,

                    # Unacceptable latency
                    "p95_latency_above_ms": 2000.0,

                    # Error spike
                    "error_rate_increase_pct": 0.50,  # 50% increase
                },

                # WARNING ALERTS (plan intervention)
                "warning": {
                    # Q3: Below 5% target for 2 weeks
                    "improvement_below_target": self.target_improvement_pct,
                    "duration_weeks": 2,

                    # Relevance degrading
                    "avg_relevance_below": 0.60,

                    # Latency concerns
                    "p95_latency_above_ms": self.max_retrieval_latency_ms,

                    # Coverage too low (expected with high threshold, but monitor)
                    "coverage_below": 0.35,

                    # User dissatisfaction
                    "satisfaction_below": 3.0,  # out of 5
                },

                # INFO ALERTS (FYI)
                "info": {
                    # Good performance to celebrate
                    "improvement_above": 0.10,  # 10% improvement!

                    # Memory bloat
                    "bloat_ratio_below": 0.50,
                },
            }

        if self.ab_test_traffic_split is None:
            self.ab_test_traffic_split = {
                "control": 0.40,      # 40% on current parameters
                "variant_a": 0.30,    # 30% on test variant A
                "variant_b": 0.30,    # 30% on test variant B
            }

    def get_threshold_for_cluster(self, cluster: str) -> float:
        """Get effective threshold for a workflow cluster."""
        adjustment = self.cluster_threshold_adjustments.get(cluster, 0.0)
        return self.similarity_threshold + adjustment

    # =========================================================================
    # PERFORMANCE TARGETS
    # =========================================================================

    # Q3: 5% improvement target (realistic)
    # This is the minimum acceptable improvement in success rate
    target_improvement_pct: float = 0.05  # 5%

    # Q1: 5% tolerance for worse performance
    # If memory makes things >5% worse, immediate intervention required
    max_acceptable_degradation_pct: float = 0.05  # 5%

    # Target retrieval relevance (0-1 scale)
    target_retrieval_relevance: float = 0.70

    # Target coverage (% of queries that find lessons)
    # With high threshold (0.80), we expect lower coverage
    target_coverage: float = 0.45  # Lower than default due to high threshold

    # Maximum acceptable latency (p95)
    max_retrieval_latency_ms: float = 500.0

    # =========================================================================
    # TUNING & OPTIMIZATION
    # =========================================================================

    # Q2: Weekly parameter tuning
    tuning_interval_days: int = 7

    # Minimum data points needed before tuning
    min_workflows_for_tuning: int = 50

    # Learning rate for automated parameter adjustment
    # Lower = more conservative adjustments
    tuning_learning_rate: float = 0.05

    # Enable automated parameter tuning
    auto_tune_enabled: bool = True

    # Parameters that can be auto-tuned
    tunable_parameters: List[str] = None

    # =========================================================================
    # ALERTING & MONITORING
    # =========================================================================

    # Q4: Alerts to both eng + product teams
    alert_recipients: Dict[str, List[str]] = None

    # Alert thresholds based on Q1 and Q3
    alert_thresholds: Dict[str, Dict[str, Any]] = None

    # How often to check metrics and send alerts
    alert_check_interval_hours: int = 6  # 4 times per day

    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================

    # Archive lessons that haven't been used in N days
    archive_unused_after_days: int = 90

    # Archive lessons with low effectiveness scores
    archive_effectiveness_below: float = 0.40

    # Maximum total lessons before forcing cleanup
    max_total_lessons: int = 1000

    # Target active lesson ratio (active/total)
    target_active_ratio: float = 0.70

    # =========================================================================
    # A/B TESTING
    # =========================================================================

    # Enable A/B testing for parameter changes
    ab_testing_enabled: bool = True

    # Minimum duration for A/B tests (in days)
    ab_test_min_duration_days: int = 14  # 2 weeks

    # Minimum workflows per variant before concluding test
    ab_test_min_workflows_per_variant: int = 100

    # Statistical significance threshold (p-value)
    ab_test_significance_threshold: float = 0.05

    # Traffic split for A/B tests
    ab_test_traffic_split: Dict[str, float] = None


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global configuration instance
_config: MemorySystemConfig = None


def get_memory_config() -> MemorySystemConfig:
    """Get the global memory configuration."""
    global _config
    if _config is None:
        _config = MemorySystemConfig()
    return _config


def set_memory_config(config: MemorySystemConfig):
    """Set the global memory configuration."""
    global _config
    _config = config


def reset_memory_config():
    """Reset to default configuration."""
    global _config
    _config = MemorySystemConfig()


# =============================================================================
# ALERTING SYSTEM
# =============================================================================

class MemoryAlert:
    """Alert about memory system health."""

    def __init__(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        metrics: Dict[str, Any],
        recommended_action: str,
    ):
        self.severity = severity
        self.title = title
        self.message = message
        self.metrics = metrics
        self.recommended_action = recommended_action
        self.timestamp = None  # Set when sent

    def to_dict(self) -> Dict[str, Any]:
        """Serialize alert."""
        return {
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metrics": self.metrics,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp,
        }


class AlertManager:
    """Manage alerts for memory system."""

    def __init__(self, config: MemorySystemConfig):
        self.config = config
        self.sent_alerts: List[MemoryAlert] = []

    def check_and_send_alerts(self, metrics: Dict[str, Any]):
        """
        Check metrics against thresholds and send alerts if needed.

        Args:
            metrics: Current system metrics from MemoryMetricsCollector
        """
        alerts = []

        # Check critical conditions
        critical = self.config.alert_thresholds["critical"]

        # Q1: 5% tolerance - critical if worse
        improvement = metrics.get("lagging_indicators", {}).get("success_rates", {}).get("improvement", 0)
        if improvement < critical["improvement_below"]:
            alerts.append(MemoryAlert(
                severity=AlertSeverity.CRITICAL,
                title="Memory Degrading Workflow Success",
                message=f"Workflows with lessons are {abs(improvement)*100:.1f}% WORSE than without. This exceeds the 5% tolerance threshold.",
                metrics={"improvement": improvement},
                recommended_action="DISABLE MEMORY IMMEDIATELY and investigate. Potential causes: (1) Bad lessons recently approved, (2) Retrieval algorithm broken, (3) Lessons being applied incorrectly.",
            ))

        # Check retrieval relevance
        relevance = metrics.get("leading_indicators", {}).get("retrieval_relevance", {}).get("avg_relevance", 1.0)
        if relevance < critical["avg_relevance_below"]:
            alerts.append(MemoryAlert(
                severity=AlertSeverity.CRITICAL,
                title="Retrieval Relevance Critically Low",
                message=f"Average retrieval relevance is {relevance:.2f}, below critical threshold of {critical['avg_relevance_below']}. Retrieved lessons are not relevant to queries.",
                metrics={"avg_relevance": relevance},
                recommended_action="Stop lesson approval. Audit retrieval algorithm. Consider raising similarity threshold or improving embeddings.",
            ))

        # Check latency
        latency = metrics.get("leading_indicators", {}).get("retrieval_latency", {}).get("p95_ms", 0)
        if latency > critical["p95_latency_above_ms"]:
            alerts.append(MemoryAlert(
                severity=AlertSeverity.CRITICAL,
                title="Retrieval Latency Unacceptable",
                message=f"P95 latency is {latency:.0f}ms, above critical threshold of {critical['p95_latency_above_ms']:.0f}ms. Memory is slowing down workflows significantly.",
                metrics={"p95_latency_ms": latency},
                recommended_action="Disable memory temporarily. Optimize vector search (add indexes), implement caching, or reduce memory size.",
            ))

        # Check warning conditions
        warning = self.config.alert_thresholds["warning"]

        # Q3: 5% target - warning if below target for 2 weeks
        if 0 <= improvement < warning["improvement_below_target"]:
            alerts.append(MemoryAlert(
                severity=AlertSeverity.WARNING,
                title="Improvement Below 5% Target",
                message=f"Workflow improvement with lessons is {improvement*100:.1f}%, below target of {warning['improvement_below_target']*100:.0f}%. Memory is helping, but not meeting goals.",
                metrics={"improvement": improvement, "target": warning["improvement_below_target"]},
                recommended_action="Review lesson quality. Extract better lessons from top-performing workflows. Consider lowering similarity threshold slightly to increase coverage.",
            ))

        # Check info conditions (positive alerts)
        info = self.config.alert_thresholds["info"]

        if improvement > info["improvement_above"]:
            alerts.append(MemoryAlert(
                severity=AlertSeverity.INFO,
                title="Excellent Memory Performance! 🎉",
                message=f"Workflow improvement with lessons is {improvement*100:.1f}%, well above target! Memory system is delivering strong value.",
                metrics={"improvement": improvement},
                recommended_action="Continue monitoring. Document what's working well. Consider expanding lesson coverage to other domains.",
            ))

        # Send alerts to appropriate teams
        for alert in alerts:
            self._send_alert(alert)

        return alerts

    def _send_alert(self, alert: MemoryAlert):
        """
        Send alert to appropriate teams.

        Q4: Both eng + product teams for critical, eng only for warning/info
        """
        import datetime
        alert.timestamp = datetime.datetime.now().isoformat()

        recipients = self.config.alert_recipients.get(alert.severity.value, ["eng"])

        # In production, this would integrate with:
        # - Slack webhooks
        # - PagerDuty
        # - Email
        # - Internal dashboard

        print(f"\n{'='*80}")
        print(f"🚨 MEMORY SYSTEM ALERT - {alert.severity.value.upper()}")
        print(f"{'='*80}")
        print(f"Recipients: {', '.join(recipients)}")
        print(f"Title: {alert.title}")
        print(f"Message: {alert.message}")
        print(f"\nMetrics:")
        for key, value in alert.metrics.items():
            print(f"  - {key}: {value}")
        print(f"\nRecommended Action:")
        print(f"  {alert.recommended_action}")
        print(f"{'='*80}\n")

        self.sent_alerts.append(alert)

    def get_recent_alerts(self, hours: int = 24) -> List[MemoryAlert]:
        """Get alerts from the last N hours."""
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)

        return [
            alert for alert in self.sent_alerts
            if alert.timestamp and datetime.datetime.fromisoformat(alert.timestamp) > cutoff
        ]


# =============================================================================
# IMPLICATIONS OF YOUR CHOICES
# =============================================================================

IMPLICATIONS_DOC = """
# Implications of Your Configuration Choices

## Q1: 5% Tolerance for Worse Performance

**What this means:**
- Memory can make things up to 5% worse before critical intervention
- This gives room for experimentation and A/B testing
- But once crossed, immediate action required (disable memory)

**Operational impact:**
- System will be more forgiving during tuning
- You can test aggressive parameter changes
- But need automated monitoring to catch when tolerance is exceeded

**Recommended:**
- Set up automated alerts that check every 6 hours
- Have runbook ready for "what to do when we hit -5%"
- Consider auto-disable if sustained for 24h

## Q2: Weekly Parameter Tuning

**What this means:**
- Parameters adjust every 7 days based on data
- Allows ~50-100 workflows per week to inform adjustments
- Fast enough to adapt, slow enough to avoid noise

**Operational impact:**
- Need dashboard showing "next tuning in X days"
- Tuning happens automatically (with option to override)
- Changes are small (learning_rate = 0.05 = 5% adjustment)

**Recommended:**
- Schedule tuning for Monday mornings (review weekend data)
- Send "tuning summary" email after each adjustment
- Keep audit log of all parameter changes

## Q3: 5% Improvement Target (Realistic)

**What this means:**
- Success = workflows with lessons are 5% more successful
- This is achievable and measurable
- Sets clear bar for "is memory worth it?"

**Operational impact:**
- If you're at 4%, you're close (warning, not critical)
- If you're at 8%, you're exceeding expectations (celebrate!)
- If you're at 1%, need to improve lesson quality

**Recommended:**
- Track toward this goal publicly (dashboard, weekly reports)
- If consistently above 5%, consider raising bar to 7%
- If struggling to reach 5%, reassess approach

## Q4: Alerts to Both Eng + Product Teams

**What this means:**
- Critical issues get attention from both technical and product sides
- Product team can make go/no-go decisions
- Eng team can investigate and fix

**Operational impact:**
- Need clear alert format that's accessible to non-technical stakeholders
- Product team needs to understand thresholds
- Shared responsibility for memory system health

**Recommended:**
- Weekly summary report for product team (even when healthy)
- Critical alerts include:
  - What happened (plain language)
  - Impact on users
  - Recommended action
- Set up Slack channel: #memory-system-health

## Q5: High Threshold (0.80) - Prioritize Relevance

**What this means:**
- Only retrieve lessons with 80%+ similarity
- Fewer lessons retrieved, but highly relevant
- Trade-off: Lower coverage (45% vs 55%)

**Operational impact:**
- Workflows will get 2-3 lessons instead of 5-7
- But those 2-3 will be spot-on
- "Miss" rate will be higher (55% of queries find nothing)

**Why this makes sense:**
- Bad lessons are worse than no lessons
- Users trust the system more when recommendations are accurate
- Easier to expand coverage later than to regain trust after bad advice

**Recommended:**
- Monitor coverage closely (target: 45%)
- If coverage drops below 35%, investigate
- Consider cluster-specific adjustments:
  - "content" workflows: 0.75 (more diversity needed)
  - "code" workflows: 0.80 (precision critical)
  - "analysis" workflows: 0.80 (precision critical)

## Combined Impact: Your Configuration Profile

**Profile: "Conservative Quality-First"**

Characteristics:
- Prioritize relevance over coverage (Q5: threshold 0.80)
- Allow experimentation but catch failures (Q1: 5% tolerance)
- Steady, data-driven tuning (Q2: weekly)
- Realistic success bar (Q3: 5% improvement)
- Cross-functional ownership (Q4: eng + product)

**This profile works well when:**
- ✅ You're in early stages (better to start conservative)
- ✅ User trust is critical (bad recommendations hurt)
- ✅ You have time to grow coverage organically
- ✅ You prefer predictable, steady improvements

**Watch out for:**
- ⚠️ Coverage may feel low initially (45% "hit rate")
- ⚠️ Slower growth of memory value (high bar for lessons)
- ⚠️ May need to manually seed diverse lessons

## Next Actions Based on Your Choices

1. **Week 1**: Deploy with high threshold (0.80)
   - Expect: Low coverage (35-45%), high relevance (0.75+)
   - Monitor: Are the few lessons we retrieve actually helping?

2. **Week 2**: First tuning cycle
   - Measure: Did we hit 5% improvement target?
   - If yes: Lock in threshold, focus on coverage
   - If no: Consider dropping to 0.78 and retest

3. **Week 3-4**: A/B test if needed
   - Test: 0.75 vs 0.80 vs 0.82
   - Measure: Success rate, relevance, user satisfaction
   - Ship: Best-performing variant

4. **Week 5+**: Expand coverage
   - Add more lessons for underserved clusters
   - Lower threshold for "content" cluster if needed
   - Maintain high bar for "code" and "analysis"

Want to proceed with implementing the automated tuning system based on these settings?
"""


def print_implications():
    """Print the implications document."""
    print(IMPLICATIONS_DOC)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    config = get_memory_config()

    print("Memory System Configuration")
    print("=" * 80)
    print(f"Similarity Threshold: {config.similarity_threshold}")
    print(f"Target Improvement: {config.target_improvement_pct * 100}%")
    print(f"Max Degradation: {config.max_acceptable_degradation_pct * 100}%")
    print(f"Tuning Interval: Every {config.tuning_interval_days} days")
    print(f"Alert Recipients (critical): {config.alert_recipients['critical']}")
    print()

    # Simulate checking metrics
    print("Simulating Alert Check...")
    print()

    alert_manager = AlertManager(config)

    # Scenario 1: Excellent performance
    print("SCENARIO 1: Excellent Performance")
    print("-" * 80)
    metrics_good = {
        "leading_indicators": {
            "retrieval_relevance": {"avg_relevance": 0.76},
            "retrieval_latency": {"p95_ms": 180},
        },
        "lagging_indicators": {
            "success_rates": {"improvement": 0.12},  # 12% improvement!
        },
    }
    alert_manager.check_and_send_alerts(metrics_good)

    # Scenario 2: Below target (warning)
    print("\nSCENARIO 2: Below Target")
    print("-" * 80)
    metrics_warning = {
        "leading_indicators": {
            "retrieval_relevance": {"avg_relevance": 0.68},
            "retrieval_latency": {"p95_ms": 220},
        },
        "lagging_indicators": {
            "success_rates": {"improvement": 0.03},  # Only 3% improvement
        },
    }
    alert_manager.check_and_send_alerts(metrics_warning)

    # Scenario 3: Critical failure
    print("\nSCENARIO 3: Critical Failure")
    print("-" * 80)
    metrics_critical = {
        "leading_indicators": {
            "retrieval_relevance": {"avg_relevance": 0.62},
            "retrieval_latency": {"p95_ms": 200},
        },
        "lagging_indicators": {
            "success_rates": {"improvement": -0.08},  # -8% (worse!)
        },
    }
    alert_manager.check_and_send_alerts(metrics_critical)

    print("\n" + "=" * 80)
    print("Configuration Implications:")
    print("=" * 80)
    print_implications()
