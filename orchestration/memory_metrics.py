"""
Memory Management Observability & Metrics

This module provides comprehensive monitoring for adaptive memory systems to measure:
1. Whether lessons are actually helping workflows
2. If memory retrieval is finding the right lessons
3. When to adjust parameters (thresholds, weights, etc.)
4. Root cause analysis when things go wrong

Philosophy: "You can't improve what you don't measure"
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from pathlib import Path


class MetricType(str, Enum):
    """Types of metrics to track."""
    # Leading indicators (predictive)
    RETRIEVAL_RELEVANCE = "retrieval_relevance"      # Are we finding the right lessons?
    RETRIEVAL_LATENCY = "retrieval_latency"          # How fast?
    LESSON_COVERAGE = "lesson_coverage"              # Do we have lessons for common tasks?

    # Lagging indicators (outcome-based)
    WORKFLOW_SUCCESS_RATE = "workflow_success_rate"  # Did it complete successfully?
    WORKFLOW_DURATION = "workflow_duration"          # How long did it take?
    ERROR_REDUCTION = "error_reduction"              # Fewer errors over time?
    HUMAN_SATISFACTION = "human_satisfaction"        # User feedback

    # System health
    MEMORY_BLOAT = "memory_bloat"                    # Is memory growing too large?
    RETRIEVAL_LOAD = "retrieval_load"                # System performance
    LESSON_STALENESS = "lesson_staleness"            # Are lessons outdated?


@dataclass
class WorkflowOutcome:
    """Record of a workflow execution outcome."""
    run_id: str
    workflow_id: str
    task_description: str
    cluster: str  # code, content, analysis

    success: bool
    duration_seconds: float
    error_count: int
    error_types: List[str]

    lessons_retrieved: List[str]  # Lesson IDs that were provided
    lessons_used_count: int       # How many were actually referenced
    human_satisfaction: Optional[float] = None  # 0-1 rating

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RetrievalEvent:
    """Record of a memory retrieval operation."""
    timestamp: str
    workflow_id: str
    cluster: str
    query_context: str

    retrieved_lesson_ids: List[str]
    retrieval_scores: List[float]  # Similarity/relevance scores
    latency_ms: float

    # Ground truth (if available)
    actually_helpful: Optional[List[str]] = None  # Which lessons were actually useful


@dataclass
class MetricSnapshot:
    """Point-in-time metric value."""
    metric_type: MetricType
    value: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryMetricsCollector:
    """
    Collect and analyze metrics for adaptive memory management.

    This is the "observability layer" that tells you:
    - What's working
    - What's not working
    - What to change and by how much
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize metrics collector.

        Args:
            storage_path: Where to store metrics data
        """
        if storage_path is None:
            storage_path = str(Path.home() / ".agenticom" / "memory_metrics.json")

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.workflow_outcomes: List[WorkflowOutcome] = []
        self.retrieval_events: List[RetrievalEvent] = []
        self.metric_snapshots: List[MetricSnapshot] = []

        self._load()

    def _load(self):
        """Load metrics from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                    # Load workflow outcomes
                    for item in data.get("workflow_outcomes", []):
                        self.workflow_outcomes.append(WorkflowOutcome(**item))

                    # Load retrieval events
                    for item in data.get("retrieval_events", []):
                        self.retrieval_events.append(RetrievalEvent(**item))

                    # Load metric snapshots
                    for item in data.get("metric_snapshots", []):
                        item["metric_type"] = MetricType(item["metric_type"])
                        self.metric_snapshots.append(MetricSnapshot(**item))

            except Exception as e:
                print(f"Failed to load metrics: {e}")

    def _save(self):
        """Save metrics to storage."""
        try:
            data = {
                "workflow_outcomes": [
                    {**o.__dict__, "timestamp": o.timestamp}
                    for o in self.workflow_outcomes
                ],
                "retrieval_events": [
                    {**e.__dict__, "timestamp": e.timestamp}
                    for e in self.retrieval_events
                ],
                "metric_snapshots": [
                    {
                        "metric_type": s.metric_type.value,
                        "value": s.value,
                        "timestamp": s.timestamp,
                        "metadata": s.metadata,
                    }
                    for s in self.metric_snapshots
                ],
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Failed to save metrics: {e}")

    # =========================================================================
    # DATA COLLECTION
    # =========================================================================

    def record_workflow_outcome(self, outcome: WorkflowOutcome):
        """Record the outcome of a workflow execution."""
        self.workflow_outcomes.append(outcome)
        self._save()

    def record_retrieval(self, event: RetrievalEvent):
        """Record a memory retrieval operation."""
        self.retrieval_events.append(event)
        self._save()

    def record_metric(self, metric_type: MetricType, value: float, metadata: Optional[Dict] = None):
        """Record a point-in-time metric value."""
        snapshot = MetricSnapshot(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.metric_snapshots.append(snapshot)
        self._save()

    # =========================================================================
    # LEADING INDICATORS - Predict future performance
    # =========================================================================

    def measure_retrieval_relevance(
        self,
        lookback_hours: int = 24
    ) -> Dict[str, float]:
        """
        Measure how relevant retrieved lessons are.

        High relevance = memory is finding the right lessons
        Low relevance = need to adjust retrieval algorithm

        Returns:
            {
                "avg_relevance": 0.0-1.0,
                "precision_at_3": 0.0-1.0,  # How many of top 3 were helpful
                "coverage": 0.0-1.0,         # % of queries that found lessons
            }
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent_events = [
            e for e in self.retrieval_events
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]

        if not recent_events:
            return {"avg_relevance": 0.0, "precision_at_3": 0.0, "coverage": 0.0}

        # Average relevance score
        all_scores = []
        for event in recent_events:
            all_scores.extend(event.retrieval_scores)

        avg_relevance = sum(all_scores) / len(all_scores) if all_scores else 0.0

        # Precision@3 (if ground truth available)
        precision_values = []
        for event in recent_events:
            if event.actually_helpful is not None:
                top3 = event.retrieved_lesson_ids[:3]
                helpful_in_top3 = len([lid for lid in top3 if lid in event.actually_helpful])
                precision_values.append(helpful_in_top3 / min(3, len(top3)))

        precision_at_3 = sum(precision_values) / len(precision_values) if precision_values else 0.0

        # Coverage (% of queries that found at least one lesson)
        found_lessons = len([e for e in recent_events if len(e.retrieved_lesson_ids) > 0])
        coverage = found_lessons / len(recent_events) if recent_events else 0.0

        return {
            "avg_relevance": avg_relevance,
            "precision_at_3": precision_at_3,
            "coverage": coverage,
        }

    def measure_retrieval_latency(
        self,
        lookback_hours: int = 24
    ) -> Dict[str, float]:
        """
        Measure how fast memory retrieval is.

        Fast retrieval = good user experience
        Slow retrieval = need to optimize (indexes, caching, etc.)

        Returns:
            {
                "p50_ms": median latency,
                "p95_ms": 95th percentile,
                "p99_ms": 99th percentile,
            }
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent_events = [
            e for e in self.retrieval_events
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]

        if not recent_events:
            return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}

        latencies = sorted([e.latency_ms for e in recent_events])
        n = len(latencies)

        return {
            "p50_ms": latencies[n // 2] if n > 0 else 0.0,
            "p95_ms": latencies[int(n * 0.95)] if n > 0 else 0.0,
            "p99_ms": latencies[int(n * 0.99)] if n > 0 else 0.0,
        }

    # =========================================================================
    # LAGGING INDICATORS - Measure actual outcomes
    # =========================================================================

    def measure_workflow_success_rate(
        self,
        lookback_hours: int = 168  # 1 week
    ) -> Dict[str, Any]:
        """
        Measure workflow success rates over time.

        Increasing success rate = memory is helping
        Decreasing success rate = something is wrong

        Returns:
            {
                "overall_success_rate": 0.0-1.0,
                "with_lessons": 0.0-1.0,      # Success rate when lessons used
                "without_lessons": 0.0-1.0,   # Success rate when no lessons
                "improvement": float,          # Difference (positive = lessons help)
            }
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent_outcomes = [
            o for o in self.workflow_outcomes
            if datetime.fromisoformat(o.timestamp) > cutoff
        ]

        if not recent_outcomes:
            return {
                "overall_success_rate": 0.0,
                "with_lessons": 0.0,
                "without_lessons": 0.0,
                "improvement": 0.0,
            }

        total_success = len([o for o in recent_outcomes if o.success])
        overall_rate = total_success / len(recent_outcomes)

        # Split by whether lessons were used
        with_lessons = [o for o in recent_outcomes if len(o.lessons_retrieved) > 0]
        without_lessons = [o for o in recent_outcomes if len(o.lessons_retrieved) == 0]

        with_rate = (
            len([o for o in with_lessons if o.success]) / len(with_lessons)
            if with_lessons else 0.0
        )
        without_rate = (
            len([o for o in without_lessons if o.success]) / len(without_lessons)
            if without_lessons else 0.0
        )

        return {
            "overall_success_rate": overall_rate,
            "with_lessons": with_rate,
            "without_lessons": without_rate,
            "improvement": with_rate - without_rate,
        }

    def measure_error_reduction(
        self,
        lookback_hours: int = 168
    ) -> Dict[str, Any]:
        """
        Measure if errors are decreasing over time.

        Decreasing errors = lessons are working
        Increasing errors = need to investigate

        Returns:
            {
                "current_error_rate": float,
                "previous_error_rate": float,
                "reduction_pct": float,           # % improvement
                "common_error_types": List[str],
            }
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent_outcomes = [
            o for o in self.workflow_outcomes
            if datetime.fromisoformat(o.timestamp) > cutoff
        ]

        if len(recent_outcomes) < 10:  # Need enough data
            return {
                "current_error_rate": 0.0,
                "previous_error_rate": 0.0,
                "reduction_pct": 0.0,
                "common_error_types": [],
            }

        # Split into two periods
        mid_point = len(recent_outcomes) // 2
        older = recent_outcomes[:mid_point]
        newer = recent_outcomes[mid_point:]

        old_error_rate = sum(o.error_count for o in older) / len(older)
        new_error_rate = sum(o.error_count for o in newer) / len(newer)

        reduction_pct = 0.0
        if old_error_rate > 0:
            reduction_pct = ((old_error_rate - new_error_rate) / old_error_rate) * 100

        # Find common error types
        error_type_counts = {}
        for outcome in recent_outcomes:
            for error_type in outcome.error_types:
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1

        common_errors = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "current_error_rate": new_error_rate,
            "previous_error_rate": old_error_rate,
            "reduction_pct": reduction_pct,
            "common_error_types": [e[0] for e in common_errors],
        }

    def measure_human_satisfaction(
        self,
        lookback_hours: int = 168
    ) -> Dict[str, float]:
        """
        Measure user satisfaction with workflow outcomes.

        High satisfaction = memory is delivering value
        Low satisfaction = need to adjust approach

        Returns:
            {
                "avg_satisfaction": 0.0-1.0,
                "response_rate": 0.0-1.0,  # How many users provide feedback
            }
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent_outcomes = [
            o for o in self.workflow_outcomes
            if datetime.fromisoformat(o.timestamp) > cutoff
        ]

        if not recent_outcomes:
            return {"avg_satisfaction": 0.0, "response_rate": 0.0}

        with_ratings = [o for o in recent_outcomes if o.human_satisfaction is not None]

        avg = (
            sum(o.human_satisfaction for o in with_ratings) / len(with_ratings)
            if with_ratings else 0.0
        )

        response_rate = len(with_ratings) / len(recent_outcomes)

        return {
            "avg_satisfaction": avg,
            "response_rate": response_rate,
        }

    # =========================================================================
    # SYSTEM HEALTH
    # =========================================================================

    def measure_memory_bloat(self, total_lessons: int, active_lessons: int) -> float:
        """
        Measure if memory is growing too large.

        High bloat = too many inactive lessons taking up space
        Low bloat = well-curated memory

        Returns:
            Bloat ratio (active / total). Higher is better. Target: > 0.7
        """
        if total_lessons == 0:
            return 1.0

        return active_lessons / total_lessons

    # =========================================================================
    # ROOT CAUSE ANALYSIS
    # =========================================================================

    def diagnose_retrieval_issues(self) -> Dict[str, Any]:
        """
        Analyze why retrieval might not be working well.

        Returns diagnosis with potential root causes and recommendations.
        """
        relevance = self.measure_retrieval_relevance()
        latency = self.measure_retrieval_latency()

        issues = []
        recommendations = []

        # Check relevance
        if relevance["avg_relevance"] < 0.6:
            issues.append("Low retrieval relevance (< 0.6)")
            recommendations.append("Adjust similarity threshold or improve embeddings")

        if relevance["coverage"] < 0.5:
            issues.append("Low coverage - many queries find no lessons")
            recommendations.append("Add more diverse lessons or lower retrieval threshold")

        # Check latency
        if latency["p95_ms"] > 500:
            issues.append("Slow retrieval (p95 > 500ms)")
            recommendations.append("Add caching or optimize vector search indexes")

        # Check lesson usage
        recent_outcomes = self.workflow_outcomes[-50:] if len(self.workflow_outcomes) > 50 else self.workflow_outcomes
        if recent_outcomes:
            avg_usage = sum(o.lessons_used_count for o in recent_outcomes) / len(recent_outcomes)
            if avg_usage < 0.5:
                issues.append("Retrieved lessons are not being used")
                recommendations.append("Improve lesson quality or presentation")

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "relevance": relevance,
                "latency": latency,
            }
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive dashboard summary for monitoring.

        This is what you'd show to a system operator.
        """
        return {
            "leading_indicators": {
                "retrieval_relevance": self.measure_retrieval_relevance(),
                "retrieval_latency": self.measure_retrieval_latency(),
            },
            "lagging_indicators": {
                "success_rates": self.measure_workflow_success_rate(),
                "error_reduction": self.measure_error_reduction(),
                "human_satisfaction": self.measure_human_satisfaction(),
            },
            "diagnostics": self.diagnose_retrieval_issues(),
            "data_volume": {
                "workflow_outcomes": len(self.workflow_outcomes),
                "retrieval_events": len(self.retrieval_events),
                "metric_snapshots": len(self.metric_snapshots),
            }
        }


# =============================================================================
# A/B TESTING FRAMEWORK
# =============================================================================

class ABTestConfig:
    """Configuration for A/B testing memory parameters."""

    def __init__(self, name: str, variants: Dict[str, Dict[str, Any]]):
        """
        Initialize A/B test.

        Args:
            name: Test name (e.g., "similarity_threshold_test")
            variants: Dict of variant_name -> parameter_values
                Example:
                {
                    "control": {"similarity_threshold": 0.70},
                    "variant_a": {"similarity_threshold": 0.75},
                    "variant_b": {"similarity_threshold": 0.80},
                }
        """
        self.name = name
        self.variants = variants
        self.assignment: Dict[str, str] = {}  # user_id -> variant_name

    def assign_variant(self, user_id: str) -> str:
        """Assign user to a variant (sticky assignment)."""
        if user_id in self.assignment:
            return self.assignment[user_id]

        # Simple hash-based assignment for consistency
        import hashlib
        hash_val = int(hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest(), 16)
        variant_names = list(self.variants.keys())
        assigned = variant_names[hash_val % len(variant_names)]

        self.assignment[user_id] = assigned
        return assigned

    def get_parameters(self, user_id: str) -> Dict[str, Any]:
        """Get parameters for this user's assigned variant."""
        variant = self.assign_variant(user_id)
        return self.variants[variant]
