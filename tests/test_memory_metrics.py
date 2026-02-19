"""
Comprehensive tests for memory metrics and monitoring system.

NO MOCKS - Uses real data structures, real calculations, real file I/O.
Tests every metric calculation with real scenarios.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from orchestration.memory_config import (
    AlertManager,
    AlertSeverity,
    MemorySystemConfig,
)
from orchestration.memory_metrics import (
    MemoryMetricsCollector,
    RetrievalEvent,
    WorkflowOutcome,
)

# =============================================================================
# FIXTURES - Real data
# =============================================================================


@pytest.fixture
def temp_metrics_storage():
    """Create temporary storage for metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "metrics.json"


@pytest.fixture
def sample_workflow_outcomes():
    """Real workflow execution outcomes."""
    now = datetime.now()

    return [
        # Successful workflows with lessons
        WorkflowOutcome(
            run_id="run-001",
            workflow_id="feature-dev",
            task_description="Build authentication",
            cluster="code",
            success=True,
            duration_seconds=1847.5,
            error_count=0,
            error_types=[],
            lessons_retrieved=["lesson-1", "lesson-2"],
            lessons_used_count=2,
            human_satisfaction=0.9,
            timestamp=(now - timedelta(hours=1)).isoformat(),
        ),
        WorkflowOutcome(
            run_id="run-002",
            workflow_id="feature-dev",
            task_description="Add password reset",
            cluster="code",
            success=True,
            duration_seconds=1234.0,
            error_count=0,
            error_types=[],
            lessons_retrieved=["lesson-1", "lesson-3"],
            lessons_used_count=2,
            human_satisfaction=0.85,
            timestamp=(now - timedelta(hours=2)).isoformat(),
        ),
        # Successful workflow WITHOUT lessons (control group)
        WorkflowOutcome(
            run_id="run-003",
            workflow_id="feature-dev",
            task_description="Update UI",
            cluster="code",
            success=True,
            duration_seconds=2100.0,
            error_count=1,  # Had a minor error
            error_types=["import_error"],
            lessons_retrieved=[],
            lessons_used_count=0,
            human_satisfaction=None,
            timestamp=(now - timedelta(hours=3)).isoformat(),
        ),
        # Failed workflow WITHOUT lessons
        WorkflowOutcome(
            run_id="run-004",
            workflow_id="feature-dev",
            task_description="Integrate payment",
            cluster="code",
            success=False,
            duration_seconds=456.0,
            error_count=3,
            error_types=["api_timeout", "validation_error", "api_timeout"],
            lessons_retrieved=[],
            lessons_used_count=0,
            human_satisfaction=None,
            timestamp=(now - timedelta(hours=4)).isoformat(),
        ),
    ]


@pytest.fixture
def sample_retrieval_events():
    """Real retrieval operation events."""
    now = datetime.now()

    return [
        RetrievalEvent(
            timestamp=(now - timedelta(minutes=30)).isoformat(),
            workflow_id="feature-dev",
            cluster="code",
            query_context="Build authentication with OAuth",
            retrieved_lesson_ids=["lesson-1", "lesson-2", "lesson-3"],
            retrieval_scores=[0.89, 0.82, 0.76],
            latency_ms=145.5,
            actually_helpful=["lesson-1", "lesson-2"],  # Ground truth
        ),
        RetrievalEvent(
            timestamp=(now - timedelta(minutes=45)).isoformat(),
            workflow_id="feature-dev",
            cluster="code",
            query_context="Add password reset functionality",
            retrieved_lesson_ids=["lesson-1", "lesson-4"],
            retrieval_scores=[0.91, 0.73],
            latency_ms=89.2,
            actually_helpful=["lesson-1"],
        ),
        RetrievalEvent(
            timestamp=(now - timedelta(hours=2)).isoformat(),
            workflow_id="content-campaign",
            cluster="content",
            query_context="Create social media content",
            retrieved_lesson_ids=[],  # No lessons found
            retrieval_scores=[],
            latency_ms=12.3,
            actually_helpful=None,
        ),
    ]


# =============================================================================
# UNIT TESTS - Metric Calculations
# =============================================================================


class TestWorkflowOutcomeData:
    """Test workflow outcome data structure."""

    def test_outcome_creation(self):
        """Test creating real workflow outcomes."""
        outcome = WorkflowOutcome(
            run_id="test-001",
            workflow_id="feature-dev",
            task_description="Test task",
            cluster="code",
            success=True,
            duration_seconds=1234.5,
            error_count=0,
            error_types=[],
            lessons_retrieved=["lesson-1"],
            lessons_used_count=1,
            human_satisfaction=0.8,
        )

        assert outcome.run_id == "test-001"
        assert outcome.success is True
        assert outcome.duration_seconds == 1234.5
        assert len(outcome.lessons_retrieved) == 1


class TestRetrievalRelevance:
    """Test retrieval relevance metric calculations."""

    def test_measure_retrieval_relevance(
        self, temp_metrics_storage, sample_retrieval_events
    ):
        """Test REAL retrieval relevance calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        # Record real retrieval events
        for event in sample_retrieval_events:
            collector.record_retrieval(event)

        # Measure relevance
        relevance = collector.measure_retrieval_relevance(lookback_hours=24)

        # Check avg_relevance (average of all retrieval scores)
        all_scores = []
        for event in sample_retrieval_events:
            all_scores.extend(event.retrieval_scores)

        expected_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        assert abs(relevance["avg_relevance"] - expected_avg) < 0.01

        # Check precision@3 (how many of top 3 were helpful)
        events_with_truth = [
            e for e in sample_retrieval_events if e.actually_helpful is not None
        ]
        precision_values = []

        for event in events_with_truth:
            top3 = event.retrieved_lesson_ids[:3]
            helpful_in_top3 = len(
                [lid for lid in top3 if lid in event.actually_helpful]
            )
            precision_values.append(helpful_in_top3 / min(3, len(top3)))

        expected_precision = (
            sum(precision_values) / len(precision_values) if precision_values else 0.0
        )
        assert abs(relevance["precision_at_3"] - expected_precision) < 0.01

        # Check coverage (% of queries that found lessons)
        found_lessons = len(
            [e for e in sample_retrieval_events if len(e.retrieved_lesson_ids) > 0]
        )
        expected_coverage = found_lessons / len(sample_retrieval_events)
        assert abs(relevance["coverage"] - expected_coverage) < 0.01

    def test_retrieval_latency(self, temp_metrics_storage, sample_retrieval_events):
        """Test REAL latency metric calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        for event in sample_retrieval_events:
            collector.record_retrieval(event)

        latency = collector.measure_retrieval_latency(lookback_hours=24)

        # Calculate expected percentiles
        latencies = sorted([e.latency_ms for e in sample_retrieval_events])
        n = len(latencies)

        expected_p50 = latencies[n // 2]
        expected_p95 = latencies[int(n * 0.95)]
        expected_p99 = latencies[int(n * 0.99)]

        assert latency["p50_ms"] == expected_p50
        assert latency["p95_ms"] == expected_p95
        assert latency["p99_ms"] == expected_p99


class TestWorkflowSuccessRate:
    """Test workflow success rate calculations."""

    def test_measure_success_rate(self, temp_metrics_storage, sample_workflow_outcomes):
        """Test REAL success rate calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        for outcome in sample_workflow_outcomes:
            collector.record_workflow_outcome(outcome)

        success_rates = collector.measure_workflow_success_rate(lookback_hours=24)

        # Calculate expected values
        all_outcomes = sample_workflow_outcomes
        total_success = len([o for o in all_outcomes if o.success])
        overall_rate = total_success / len(all_outcomes)

        with_lessons = [o for o in all_outcomes if len(o.lessons_retrieved) > 0]
        without_lessons = [o for o in all_outcomes if len(o.lessons_retrieved) == 0]

        with_rate = (
            len([o for o in with_lessons if o.success]) / len(with_lessons)
            if with_lessons
            else 0.0
        )
        without_rate = (
            len([o for o in without_lessons if o.success]) / len(without_lessons)
            if without_lessons
            else 0.0
        )

        improvement = with_rate - without_rate

        # Verify calculations
        assert abs(success_rates["overall_success_rate"] - overall_rate) < 0.01
        assert abs(success_rates["with_lessons"] - with_rate) < 0.01
        assert abs(success_rates["without_lessons"] - without_rate) < 0.01
        assert abs(success_rates["improvement"] - improvement) < 0.01

        # In our sample data:
        # with_lessons: 2/2 success = 100%
        # without_lessons: 1/2 success = 50%
        # improvement = 50%!
        assert success_rates["improvement"] > 0, "Lessons should improve success rate"

    def test_error_reduction(self, temp_metrics_storage):
        """Test REAL error reduction calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        now = datetime.now()

        # Earlier outcomes (higher error rate)
        early_outcomes = [
            WorkflowOutcome(
                run_id=f"early-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True,
                duration_seconds=1000.0,
                error_count=3 if i % 2 == 0 else 2,  # 2.5 avg errors
                error_types=["error1", "error2"],
                lessons_retrieved=[],
                lessons_used_count=0,
                timestamp=(now - timedelta(days=7, hours=i)).isoformat(),
            )
            for i in range(10)
        ]

        # Recent outcomes (lower error rate - lessons are helping!)
        recent_outcomes = [
            WorkflowOutcome(
                run_id=f"recent-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True,
                duration_seconds=1000.0,
                error_count=1 if i % 3 == 0 else 0,  # ~0.33 avg errors
                error_types=["error1"] if i % 3 == 0 else [],
                lessons_retrieved=["lesson-1"],
                lessons_used_count=1,
                timestamp=(now - timedelta(hours=i)).isoformat(),
            )
            for i in range(10)
        ]

        for outcome in early_outcomes + recent_outcomes:
            collector.record_workflow_outcome(outcome)

        error_reduction = collector.measure_error_reduction(
            lookback_hours=168
        )  # 1 week

        # Should show significant error reduction
        assert (
            error_reduction["previous_error_rate"]
            > error_reduction["current_error_rate"]
        )
        assert error_reduction["reduction_pct"] > 0, "Errors should be decreasing"

        # In our test data: 2.5 → 0.33 errors = ~87% reduction!
        assert error_reduction["reduction_pct"] > 50  # At least 50% reduction

    def test_human_satisfaction(self, temp_metrics_storage, sample_workflow_outcomes):
        """Test REAL satisfaction metric calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        for outcome in sample_workflow_outcomes:
            collector.record_workflow_outcome(outcome)

        satisfaction = collector.measure_human_satisfaction(lookback_hours=24)

        # Calculate expected values
        with_ratings = [
            o for o in sample_workflow_outcomes if o.human_satisfaction is not None
        ]
        expected_avg = (
            sum(o.human_satisfaction for o in with_ratings) / len(with_ratings)
            if with_ratings
            else 0.0
        )
        expected_response_rate = len(with_ratings) / len(sample_workflow_outcomes)

        assert abs(satisfaction["avg_satisfaction"] - expected_avg) < 0.01
        assert abs(satisfaction["response_rate"] - expected_response_rate) < 0.01


class TestMemoryBloat:
    """Test memory bloat calculation."""

    def test_measure_bloat(self, temp_metrics_storage):
        """Test REAL bloat ratio calculation."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        # Scenario: 100 total lessons, 70 active
        bloat_ratio = collector.measure_memory_bloat(
            total_lessons=100, active_lessons=70
        )

        assert bloat_ratio == 0.70  # 70% active

        # Scenario: 100 total lessons, 40 active (bloated!)
        bloat_ratio_bad = collector.measure_memory_bloat(
            total_lessons=100, active_lessons=40
        )

        assert bloat_ratio_bad == 0.40  # Only 40% active - need cleanup


# =============================================================================
# INTEGRATION TESTS - Root Cause Analysis
# =============================================================================


class TestDiagnostics:
    """Test diagnostic and root cause analysis."""

    def test_diagnose_low_relevance(self, temp_metrics_storage):
        """Test diagnosis when retrieval relevance is low."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        now = datetime.now()

        # Create events with LOW relevance scores
        low_relevance_events = [
            RetrievalEvent(
                timestamp=(now - timedelta(minutes=i)).isoformat(),
                workflow_id="feature-dev",
                cluster="code",
                query_context="Task",
                retrieved_lesson_ids=["lesson-1", "lesson-2"],
                retrieval_scores=[0.55, 0.52],  # Low scores!
                latency_ms=100.0,
            )
            for i in range(10)
        ]

        for event in low_relevance_events:
            collector.record_retrieval(event)

        diagnosis = collector.diagnose_retrieval_issues()

        assert diagnosis["healthy"] is False
        assert "Low retrieval relevance" in " ".join(diagnosis["issues"])
        assert any(
            "threshold" in rec.lower() or "embeddings" in rec.lower()
            for rec in diagnosis["recommendations"]
        )

    def test_diagnose_low_coverage(self, temp_metrics_storage):
        """Test diagnosis when coverage is low."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        now = datetime.now()

        # Create events with many EMPTY retrievals
        mixed_events = [
            RetrievalEvent(
                timestamp=(now - timedelta(minutes=i)).isoformat(),
                workflow_id="feature-dev",
                cluster="code",
                query_context="Task",
                retrieved_lesson_ids=[]
                if i % 3 != 0
                else ["lesson-1"],  # Only 33% coverage
                retrieval_scores=[] if i % 3 != 0 else [0.75],
                latency_ms=50.0,
            )
            for i in range(15)
        ]

        for event in mixed_events:
            collector.record_retrieval(event)

        diagnosis = collector.diagnose_retrieval_issues()

        assert diagnosis["healthy"] is False
        assert "Low coverage" in " ".join(diagnosis["issues"])
        assert any(
            "diverse lessons" in rec.lower() or "threshold" in rec.lower()
            for rec in diagnosis["recommendations"]
        )

    def test_diagnose_slow_retrieval(self, temp_metrics_storage):
        """Test diagnosis when retrieval is slow."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        now = datetime.now()

        # Create events with HIGH latency
        slow_events = [
            RetrievalEvent(
                timestamp=(now - timedelta(minutes=i)).isoformat(),
                workflow_id="feature-dev",
                cluster="code",
                query_context="Task",
                retrieved_lesson_ids=["lesson-1"],
                retrieval_scores=[0.80],
                latency_ms=800.0,  # Very slow!
            )
            for i in range(10)
        ]

        for event in slow_events:
            collector.record_retrieval(event)

        diagnosis = collector.diagnose_retrieval_issues()

        assert diagnosis["healthy"] is False
        assert "Slow retrieval" in " ".join(diagnosis["issues"])
        assert any(
            "caching" in rec.lower()
            or "optimize" in rec.lower()
            or "indexes" in rec.lower()
            for rec in diagnosis["recommendations"]
        )

    def test_diagnose_healthy_system(
        self, temp_metrics_storage, sample_retrieval_events, sample_workflow_outcomes
    ):
        """Test diagnosis when system is healthy."""
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        # Add good events
        for event in sample_retrieval_events:
            collector.record_retrieval(event)

        for outcome in sample_workflow_outcomes:
            collector.record_workflow_outcome(outcome)

        diagnosis = collector.diagnose_retrieval_issues()

        # Should be healthy (good relevance, acceptable latency)
        assert diagnosis["healthy"] is True
        assert len(diagnosis["issues"]) == 0


# =============================================================================
# CONFIGURATION & ALERTING TESTS
# =============================================================================


class TestMemoryConfiguration:
    """Test memory system configuration."""

    def test_default_configuration(self):
        """Test default configuration values match user decisions."""
        config = MemorySystemConfig()

        # Q1: 5% tolerance
        assert config.max_acceptable_degradation_pct == 0.05

        # Q2: Weekly tuning
        assert config.tuning_interval_days == 7

        # Q3: 5% improvement target
        assert config.target_improvement_pct == 0.05

        # Q4: Both eng + product
        assert "eng" in config.alert_recipients["critical"]
        assert "product" in config.alert_recipients["critical"]

        # Q5: High threshold (0.80)
        assert config.similarity_threshold == 0.80

    def test_cluster_threshold_adjustments(self):
        """Test cluster-specific threshold adjustments."""
        config = MemorySystemConfig()

        # Code: use base threshold
        assert config.get_threshold_for_cluster("code") == 0.80

        # Content: slightly lower (more diversity)
        assert config.get_threshold_for_cluster("content") == 0.75

        # Analysis: use base threshold
        assert config.get_threshold_for_cluster("analysis") == 0.80


class TestAlertManager:
    """Test real alerting system."""

    def test_critical_alert_improvement_negative(self):
        """Test CRITICAL alert when improvement goes negative."""
        config = MemorySystemConfig()
        alert_manager = AlertManager(config)

        # Simulate metrics showing NEGATIVE improvement
        metrics = {
            "leading_indicators": {
                "retrieval_relevance": {"avg_relevance": 0.70},
                "retrieval_latency": {"p95_ms": 200},
            },
            "lagging_indicators": {
                "success_rates": {"improvement": -0.08}  # -8% worse!
            },
        }

        alerts = alert_manager.check_and_send_alerts(metrics)

        # Should have CRITICAL alert
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        assert len(critical_alerts) > 0

        critical = critical_alerts[0]
        assert "DISABLE MEMORY IMMEDIATELY" in critical.recommended_action
        assert "eng" in config.alert_recipients["critical"]
        assert "product" in config.alert_recipients["critical"]

    def test_warning_alert_below_target(self):
        """Test WARNING alert when below 5% target."""
        config = MemorySystemConfig()
        alert_manager = AlertManager(config)

        # Simulate metrics showing low but positive improvement
        metrics = {
            "leading_indicators": {
                "retrieval_relevance": {"avg_relevance": 0.68},
                "retrieval_latency": {"p95_ms": 220},
            },
            "lagging_indicators": {
                "success_rates": {"improvement": 0.03}  # Only 3% (below 5% target)
            },
        }

        alerts = alert_manager.check_and_send_alerts(metrics)

        # Should have WARNING alert
        warning_alerts = [a for a in alerts if a.severity == AlertSeverity.WARNING]
        assert len(warning_alerts) > 0

        warning = warning_alerts[0]
        assert "below target" in warning.title.lower()
        assert "eng" in config.alert_recipients["warning"]

    def test_info_alert_excellent_performance(self):
        """Test INFO alert when performance exceeds expectations."""
        config = MemorySystemConfig()
        alert_manager = AlertManager(config)

        # Simulate excellent metrics
        metrics = {
            "leading_indicators": {
                "retrieval_relevance": {"avg_relevance": 0.76},
                "retrieval_latency": {"p95_ms": 150},
            },
            "lagging_indicators": {
                "success_rates": {"improvement": 0.12}  # 12% improvement!
            },
        }

        alerts = alert_manager.check_and_send_alerts(metrics)

        # Should have INFO alert celebrating success
        info_alerts = [a for a in alerts if a.severity == AlertSeverity.INFO]
        assert len(info_alerts) > 0

        info = info_alerts[0]
        assert "Excellent" in info.title or "excellent" in info.message.lower()
        assert config.alert_recipients["info"] == ["eng"]


# =============================================================================
# REAL-WORLD SCENARIOS
# =============================================================================


class TestRealWorldMonitoring:
    """Test realistic monitoring scenarios."""

    def test_scenario_gradual_degradation(self, temp_metrics_storage):
        """
        SCENARIO: System gradually degrades over 2 weeks.
        EXPECTATION: Alerts trigger at appropriate thresholds.
        """
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))
        config = MemorySystemConfig()
        alert_manager = AlertManager(config)

        now = datetime.now()

        # Week 1: Good performance (8% improvement)
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"week1-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 18 else False,  # 90% success with lessons
                duration_seconds=1000.0,
                error_count=0,
                error_types=[],
                lessons_retrieved=["lesson-1"],
                lessons_used_count=1,
                timestamp=(now - timedelta(days=14, hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Week 2: Degrading (3% improvement - below target)
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"week2-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 16 else False,  # 80% success with lessons
                duration_seconds=1000.0,
                error_count=1 if not (i < 16) else 0,
                error_types=["timeout"] if not (i < 16) else [],
                lessons_retrieved=["lesson-1"],
                lessons_used_count=1,
                timestamp=(now - timedelta(days=7, hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Control group (no lessons) - 75% success
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"control-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 15 else False,  # 75% success
                duration_seconds=1200.0,
                error_count=0,
                error_types=[],
                lessons_retrieved=[],
                lessons_used_count=0,
                timestamp=(now - timedelta(hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Check metrics
        success_rates = collector.measure_workflow_success_rate(lookback_hours=24)

        # Should show degradation but still positive
        assert 0 < success_rates["improvement"] < 0.05, (
            "Should be below 5% target but still positive"
        )

        # Check alerts
        metrics = {
            "leading_indicators": {
                "retrieval_relevance": {"avg_relevance": 0.65},
                "retrieval_latency": {"p95_ms": 200},
            },
            "lagging_indicators": {"success_rates": success_rates},
        }

        alerts = alert_manager.check_and_send_alerts(metrics)

        # Should have WARNING (not critical, since still positive)
        warning_alerts = [a for a in alerts if a.severity == AlertSeverity.WARNING]
        assert len(warning_alerts) > 0

    def test_scenario_quick_recovery(self, temp_metrics_storage):
        """
        SCENARIO: System degrades, team fixes it, performance recovers.
        EXPECTATION: Metrics show recovery, alerts clear.
        """
        collector = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))
        config = MemorySystemConfig()
        alert_manager = AlertManager(config)

        now = datetime.now()

        # Phase 1: Poor performance (days -7 to -3)
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"poor-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 12 else False,  # 60% success
                duration_seconds=1500.0,
                error_count=2 if not (i < 12) else 0,
                error_types=["error"] if not (i < 12) else [],
                lessons_retrieved=["bad-lesson"],
                lessons_used_count=1,
                timestamp=(now - timedelta(days=5, hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Phase 2: After fixing bad lessons (days -2 to now)
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"good-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 18 else False,  # 90% success
                duration_seconds=1000.0,
                error_count=0,
                error_types=[],
                lessons_retrieved=["good-lesson"],
                lessons_used_count=1,
                timestamp=(now - timedelta(hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Control group
        for i in range(20):
            outcome = WorkflowOutcome(
                run_id=f"control-{i}",
                workflow_id="feature-dev",
                task_description="Task",
                cluster="code",
                success=True if i < 16 else False,  # 80% success
                duration_seconds=1100.0,
                error_count=0,
                error_types=[],
                lessons_retrieved=[],
                lessons_used_count=0,
                timestamp=(now - timedelta(hours=i)).isoformat(),
            )
            collector.record_workflow_outcome(outcome)

        # Recent metrics should show recovery
        success_rates = collector.measure_workflow_success_rate(lookback_hours=48)

        # Should show positive improvement (90% vs 80% = +10%)
        assert success_rates["improvement"] > 0.05, (
            "Should exceed 5% target after recovery"
        )

        # Check alerts
        metrics = {
            "leading_indicators": {
                "retrieval_relevance": {"avg_relevance": 0.78},
                "retrieval_latency": {"p95_ms": 180},
            },
            "lagging_indicators": {"success_rates": success_rates},
        }

        alerts = alert_manager.check_and_send_alerts(metrics)

        # Should have INFO alert (excellent performance)
        info_alerts = [a for a in alerts if a.severity == AlertSeverity.INFO]
        assert len(info_alerts) > 0


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================


class TestMetricsPersistence:
    """Test that metrics persist correctly to disk."""

    def test_save_and_load_metrics(
        self, temp_metrics_storage, sample_workflow_outcomes, sample_retrieval_events
    ):
        """Test REAL file I/O for metrics."""
        # Create collector and add data
        collector1 = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        for outcome in sample_workflow_outcomes:
            collector1.record_workflow_outcome(outcome)

        for event in sample_retrieval_events:
            collector1.record_retrieval(event)

        # Verify file was created
        assert temp_metrics_storage.exists()

        # Create new collector from same file
        collector2 = MemoryMetricsCollector(storage_path=str(temp_metrics_storage))

        # Should have same data
        assert len(collector2.workflow_outcomes) == len(sample_workflow_outcomes)
        assert len(collector2.retrieval_events) == len(sample_retrieval_events)

        # Metrics should match
        metrics1 = collector1.measure_workflow_success_rate(lookback_hours=24)
        metrics2 = collector2.measure_workflow_success_rate(lookback_hours=24)

        assert metrics1["improvement"] == metrics2["improvement"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
