"""
Tests for orchestration/telemetry.py — NoOpCounter, NoOpHistogram,
TelemetryManager, Metrics, get_telemetry.
"""

import pytest

from orchestration.telemetry import (
    Metrics,
    NoOpCounter,
    NoOpHistogram,
    TelemetryManager,
    get_telemetry,
    init_telemetry,
)

# ---------------------------------------------------------------------------
# NoOp classes
# ---------------------------------------------------------------------------


class TestNoOpCounter:
    def test_add_no_error(self):
        counter = NoOpCounter()
        counter.add(1)
        counter.add(5, attributes={"key": "val"})

    def test_add_returns_none(self):
        counter = NoOpCounter()
        result = counter.add(1)
        assert result is None


class TestNoOpHistogram:
    def test_record_no_error(self):
        hist = NoOpHistogram()
        hist.record(42.0)
        hist.record(0.1, attributes={"endpoint": "/api"})

    def test_record_returns_none(self):
        hist = NoOpHistogram()
        result = hist.record(99)
        assert result is None


# ---------------------------------------------------------------------------
# TelemetryManager — without OTEL
# ---------------------------------------------------------------------------


class TestTelemetryManagerNoOTEL:
    def setup_method(self):
        self.manager = TelemetryManager(service_name="test-service")

    def test_initialize_returns_false_without_otel(self):
        """Without OTEL or endpoint, initialize should return False."""
        import orchestration.telemetry as tel_module

        original = tel_module.OTEL_AVAILABLE
        tel_module.OTEL_AVAILABLE = False
        try:
            result = self.manager.initialize()
            assert result is False
        finally:
            tel_module.OTEL_AVAILABLE = original

    def test_tracer_is_none_before_init(self):
        assert self.manager.tracer is None

    def test_meter_is_none_before_init(self):
        assert self.manager.meter is None

    def test_create_counter_returns_noop_when_no_meter(self):
        counter = self.manager.create_counter("test.counter")
        assert isinstance(counter, NoOpCounter)

    def test_create_histogram_returns_noop_when_no_meter(self):
        hist = self.manager.create_histogram("test.histogram")
        assert isinstance(hist, NoOpHistogram)


# ---------------------------------------------------------------------------
# TelemetryManager.span — no-op context manager
# ---------------------------------------------------------------------------


class TestTelemetryManagerSpan:
    def test_span_noop_no_exception(self):
        manager = TelemetryManager()
        with manager.span("test_span") as span:
            assert span is None  # No tracer means None

    def test_span_noop_body_still_executes(self):
        manager = TelemetryManager()
        executed = {"v": False}
        with manager.span("test_span"):
            executed["v"] = True
        assert executed["v"] is True

    def test_span_noop_exception_propagates(self):
        manager = TelemetryManager()
        with pytest.raises(ValueError, match="boom"):
            with manager.span("failing_span"):
                raise ValueError("boom")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    def setup_method(self):
        self.manager = TelemetryManager()
        self.metrics = Metrics(self.manager)

    def test_record_workflow_run_no_error(self):
        self.metrics.record_workflow_run("feature-dev", "success", 1500.0)

    def test_record_workflow_run_error_status(self):
        self.metrics.record_workflow_run("feature-dev", "error", 500.0)

    def test_record_api_request_no_error(self):
        self.metrics.record_api_request("/api/workflows", "GET", 200, 45.0)

    def test_record_api_request_error_code(self):
        self.metrics.record_api_request("/api/workflows", "POST", 500, 12.0)

    def test_record_guardrail_block_no_error(self):
        self.metrics.record_guardrail_block("content-filter", "pii_detected")

    def test_workflow_runs_counter_is_noop(self):
        assert isinstance(self.metrics.workflow_runs, NoOpCounter)

    def test_api_requests_counter_is_noop(self):
        assert isinstance(self.metrics.api_requests, NoOpCounter)

    def test_workflow_duration_histogram_is_noop(self):
        assert isinstance(self.metrics.workflow_duration, NoOpHistogram)

    def test_api_latency_histogram_is_noop(self):
        assert isinstance(self.metrics.api_latency, NoOpHistogram)


# ---------------------------------------------------------------------------
# get_telemetry — singleton
# ---------------------------------------------------------------------------


class TestGetTelemetry:
    def test_returns_instance(self):
        t = get_telemetry()
        assert isinstance(t, TelemetryManager)

    def test_returns_same_instance_on_repeated_calls(self):
        t1 = get_telemetry()
        t2 = get_telemetry()
        assert t1 is t2


# ---------------------------------------------------------------------------
# init_telemetry
# ---------------------------------------------------------------------------


class TestInitTelemetry:
    def test_init_telemetry_returns_manager(self):
        manager = init_telemetry("my-service")
        assert isinstance(manager, TelemetryManager)
        assert manager.service_name == "my-service"
