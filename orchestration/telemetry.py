"""
OpenTelemetry integration for distributed tracing and metrics export.

Provides standardized observability for production deployments.
"""

import os
from contextlib import contextmanager
from typing import Any

from orchestration.config import get_config

# Try to import OpenTelemetry - gracefully handle if not installed
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None


class TelemetryManager:
    """Manages OpenTelemetry instrumentation."""

    def __init__(self, service_name: str = "agentic"):
        self.service_name = service_name
        self._tracer = None
        self._meter = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize OpenTelemetry instrumentation."""
        if not OTEL_AVAILABLE:
            print(
                "OpenTelemetry not available. Install with: pip install agentic[observability]"
            )
            return False

        if self._initialized:
            return True

        config = get_config()
        endpoint = config.observability.otlp_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT"
        )

        if not endpoint:
            print("OTEL_EXPORTER_OTLP_ENDPOINT not set. Telemetry disabled.")
            return False

        try:
            # Create resource
            resource = Resource.create(
                {
                    SERVICE_NAME: self.service_name,
                    "service.version": "0.2.0",
                    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
                }
            )

            # Initialize tracing
            tracer_provider = TracerProvider(resource=resource)
            span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
            trace.set_tracer_provider(tracer_provider)
            self._tracer = trace.get_tracer(self.service_name)

            # Initialize metrics
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint, insecure=True),
                export_interval_millis=60000,
            )
            meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(meter_provider)
            self._meter = metrics.get_meter(self.service_name)

            # Auto-instrument libraries
            HTTPXClientInstrumentor().instrument()

            self._initialized = True
            print(f"OpenTelemetry initialized with endpoint: {endpoint}")
            return True

        except Exception as e:
            print(f"Failed to initialize OpenTelemetry: {e}")
            return False

    def instrument_fastapi(self, app: Any) -> None:
        """Instrument FastAPI application."""
        if OTEL_AVAILABLE and self._initialized:
            FastAPIInstrumentor.instrument_app(app)

    @property
    def tracer(self):
        """Get tracer instance."""
        return self._tracer

    @property
    def meter(self):
        """Get meter instance."""
        return self._meter

    @contextmanager
    def span(self, name: str, attributes: dict | None = None):
        """Create a traced span."""
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def create_counter(self, name: str, description: str = "", unit: str = "1"):
        """Create a counter metric."""
        if not self._meter:
            return NoOpCounter()
        return self._meter.create_counter(name, description=description, unit=unit)

    def create_histogram(self, name: str, description: str = "", unit: str = "ms"):
        """Create a histogram metric."""
        if not self._meter:
            return NoOpHistogram()
        return self._meter.create_histogram(name, description=description, unit=unit)

    def create_gauge(self, name: str, callback, description: str = "", unit: str = "1"):
        """Create an observable gauge metric."""
        if not self._meter:
            return None
        return self._meter.create_observable_gauge(
            name,
            callbacks=[callback],
            description=description,
            unit=unit,
        )


class NoOpCounter:
    """No-op counter when telemetry is disabled."""

    def add(self, value: int, attributes: dict | None = None) -> None:
        pass


class NoOpHistogram:
    """No-op histogram when telemetry is disabled."""

    def record(self, value: float, attributes: dict | None = None) -> None:
        pass


# Global telemetry instance
_telemetry: TelemetryManager | None = None


def get_telemetry() -> TelemetryManager:
    """Get the global telemetry manager."""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryManager()
    return _telemetry


def init_telemetry(service_name: str = "agentic") -> TelemetryManager:
    """Initialize and return telemetry manager."""
    global _telemetry
    _telemetry = TelemetryManager(service_name)
    _telemetry.initialize()
    return _telemetry


# Pre-defined metrics
class Metrics:
    """Pre-defined application metrics."""

    def __init__(self, telemetry: TelemetryManager):
        self.telemetry = telemetry

        # Counters
        self.workflow_runs = telemetry.create_counter(
            "agentic.workflow.runs",
            "Total workflow runs",
        )
        self.workflow_errors = telemetry.create_counter(
            "agentic.workflow.errors",
            "Total workflow errors",
        )
        self.guardrail_blocks = telemetry.create_counter(
            "agentic.guardrail.blocks",
            "Content blocked by guardrails",
        )
        self.api_requests = telemetry.create_counter(
            "agentic.api.requests",
            "Total API requests",
        )

        # Histograms
        self.workflow_duration = telemetry.create_histogram(
            "agentic.workflow.duration",
            "Workflow execution duration",
            "ms",
        )
        self.api_latency = telemetry.create_histogram(
            "agentic.api.latency",
            "API request latency",
            "ms",
        )
        self.memory_search_duration = telemetry.create_histogram(
            "agentic.memory.search_duration",
            "Memory search duration",
            "ms",
        )

    def record_workflow_run(
        self, workflow: str, status: str, duration_ms: float
    ) -> None:
        """Record a workflow run."""
        self.workflow_runs.add(1, {"workflow": workflow, "status": status})
        self.workflow_duration.record(duration_ms, {"workflow": workflow})
        if status == "error":
            self.workflow_errors.add(1, {"workflow": workflow})

    def record_api_request(
        self, endpoint: str, method: str, status_code: int, latency_ms: float
    ) -> None:
        """Record an API request."""
        self.api_requests.add(
            1,
            {
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code),
            },
        )
        self.api_latency.record(
            latency_ms,
            {
                "endpoint": endpoint,
                "method": method,
            },
        )

    def record_guardrail_block(self, guardrail: str, reason: str) -> None:
        """Record a guardrail block."""
        self.guardrail_blocks.add(1, {"guardrail": guardrail, "reason": reason})


# Middleware for FastAPI
async def telemetry_middleware(request, call_next):
    """Middleware to record request metrics."""
    import time

    telemetry = get_telemetry()
    start_time = time.time()

    with telemetry.span(
        "http_request",
        {
            "http.method": request.method,
            "http.url": str(request.url),
        },
    ) as span:
        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        if span:
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.duration_ms", duration_ms)

    return response
