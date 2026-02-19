"""
Observability system for metrics, tracing, and logging.

Provides comprehensive monitoring for AI agent workflows.
"""

import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog


@dataclass
class Metric:
    """A single metric data point."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metric_type: str = "gauge"  # gauge, counter, histogram


@dataclass
class Span:
    """A tracing span."""

    trace_id: str
    span_id: str
    name: str
    parent_id: str | None = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "OK"

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
        )

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_status(self, status: str) -> None:
        self.status = status

    def end(self) -> None:
        self.end_time = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class MetricsCollector:
    """Collect and manage metrics."""

    def __init__(self):
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = defaultdict(list)
        self.history: list[Metric] = []

    def increment(
        self, name: str, value: float = 1.0, labels: dict | None = None
    ) -> None:
        """Increment a counter."""
        key = self._make_key(name, labels)
        self.counters[key] += value
        self._record(name, self.counters[key], labels, "counter")

    def set_gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        self._record(name, value, labels, "gauge")

    def observe(self, name: str, value: float, labels: dict | None = None) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        self._record(name, value, labels, "histogram")

    def _make_key(self, name: str, labels: dict | None = None) -> str:
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def _record(
        self, name: str, value: float, labels: dict | None, metric_type: str
    ) -> None:
        metric = Metric(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=metric_type,
        )
        self.history.append(metric)
        # Keep only last 10000 metrics
        if len(self.history) > 10000:
            self.history = self.history[-5000:]

    def get_counter(self, name: str, labels: dict | None = None) -> float:
        """Get counter value."""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict | None = None) -> float:
        """Get gauge value."""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)

    def get_histogram_stats(
        self, name: str, labels: dict | None = None
    ) -> dict[str, float]:
        """Get histogram statistics."""
        key = self._make_key(name, labels)
        values = self.histograms.get(key, [])
        if not values:
            return {
                "count": 0,
                "sum": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }

        sorted_values = sorted(values)
        count = len(values)
        return {
            "count": count,
            "sum": sum(values),
            "avg": sum(values) / count,
            "min": min(values),
            "max": max(values),
            "p50": sorted_values[int(count * 0.5)] if count > 0 else 0,
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all current metric values."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: self.get_histogram_stats(k) for k in self.histograms},
        }

    @contextmanager
    def timer(
        self, name: str, labels: dict | None = None
    ) -> Generator[None, None, None]:
        """Context manager to time operations."""
        start = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start) * 1000  # ms
            self.observe(name, duration, labels)


class Tracer:
    """Distributed tracing support."""

    def __init__(self):
        self.spans: dict[str, Span] = {}
        self.active_traces: dict[str, list[str]] = defaultdict(list)

    def start_trace(self, name: str, attributes: dict | None = None) -> Span:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:8]

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            attributes=attributes or {},
        )

        self.spans[span_id] = span
        self.active_traces[trace_id].append(span_id)
        return span

    def start_span(
        self,
        name: str,
        parent: Span | None = None,
        attributes: dict | None = None,
    ) -> Span:
        """Start a new span, optionally as child of parent."""
        if parent:
            trace_id = parent.trace_id
            parent_id = parent.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_id = None

        span_id = str(uuid.uuid4())[:8]

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            parent_id=parent_id,
            attributes=attributes or {},
        )

        self.spans[span_id] = span
        self.active_traces[trace_id].append(span_id)
        return span

    def end_span(self, span: Span) -> None:
        """End a span."""
        span.end()

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace."""
        span_ids = self.active_traces.get(trace_id, [])
        return [self.spans[sid] for sid in span_ids if sid in self.spans]

    @contextmanager
    def trace(
        self,
        name: str,
        parent: Span | None = None,
        attributes: dict | None = None,
    ) -> Generator[Span, None, None]:
        """Context manager for tracing."""
        span = self.start_span(name, parent, attributes)
        try:
            yield span
        except Exception as e:
            span.set_status("ERROR")
            span.set_attribute("error", str(e))
            raise
        finally:
            span.end()


class Logger:
    """Structured logging with context."""

    def __init__(self, name: str = "agentic"):
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Set up standard logging
        logging.basicConfig(
            format="%(message)s",
            level=logging.INFO,
        )

        self.logger = structlog.get_logger(name)
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "Logger":
        """Bind context to logger."""
        new_logger = Logger.__new__(Logger)
        new_logger.logger = self.logger.bind(**kwargs)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self.logger.exception(message, **kwargs)


class ObservabilityStack:
    """Combined observability stack."""

    def __init__(self, name: str = "agentic"):
        self.metrics = MetricsCollector()
        self.tracer = Tracer()
        self.logger = Logger(name)

    @contextmanager
    def observe(
        self,
        operation: str,
        labels: dict | None = None,
    ) -> Generator[Span, None, None]:
        """Combined context manager for metrics and tracing."""
        # Start trace
        span = self.tracer.start_span(operation)
        if labels:
            for k, v in labels.items():
                span.set_attribute(k, v)

        # Increment counter
        self.metrics.increment(f"{operation}_total", labels=labels)

        start_time = time.time()
        try:
            yield span
            span.set_status("OK")
        except Exception as e:
            span.set_status("ERROR")
            span.set_attribute("error", str(e))
            self.metrics.increment(f"{operation}_errors", labels=labels)
            self.logger.error(f"{operation} failed", error=str(e), **(labels or {}))
            raise
        finally:
            # Record duration
            duration = (time.time() - start_time) * 1000
            self.metrics.observe(f"{operation}_duration_ms", duration, labels=labels)
            span.end()

    def get_health(self) -> dict[str, Any]:
        """Get observability health status."""
        return {
            "metrics": {
                "counters": len(self.metrics.counters),
                "gauges": len(self.metrics.gauges),
                "histograms": len(self.metrics.histograms),
            },
            "traces": {
                "active": len(self.tracer.active_traces),
                "spans": len(self.tracer.spans),
            },
        }


# Global instance
_stack: ObservabilityStack | None = None


def get_observability() -> ObservabilityStack:
    """Get the global observability stack."""
    global _stack
    if _stack is None:
        _stack = ObservabilityStack()
    return _stack


def set_observability(stack: ObservabilityStack) -> None:
    """Set the global observability stack."""
    global _stack
    _stack = stack
