"""Telemetry utilities for har-oa3-converter.

This module provides OpenTelemetry tracing and Prometheus metrics functionality.
It configures tracers, metrics, and exporters with appropriate configuration.
"""

import json
import os
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

# Import OpenTelemetry components
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

# Import Prometheus metrics
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

# Import logging for fallback and coordination
from har_oa3_converter.utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Define module-level variables for tracers and metrics
_tracer_provider = None
_tracer = None

# JSON Schema for telemetry configuration
TELEMETRY_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean"},
        "service_name": {"type": "string"},
        "exporter": {"type": "string", "enum": ["console", "otlp", "none"]},
        "exporter_endpoint": {"type": "string"},
        "metrics_port": {"type": "integer"},
        "attributes": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["enabled", "service_name"],
}

# Define metrics
conversion_counter = Counter(
    "har_oa3_conversions_total",
    "Total number of conversions performed",
    ["source_format", "target_format", "status"],
)

conversion_duration = Histogram(
    "har_oa3_conversion_duration_seconds",
    "Time spent on conversions",
    ["source_format", "target_format"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

api_requests = Counter(
    "har_oa3_api_requests_total",
    "Total number of API requests",
    ["endpoint", "method", "status"],
)

api_request_duration = Histogram(
    "har_oa3_api_request_duration_seconds",
    "Time spent processing API requests",
    ["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
)

active_conversions = Gauge(
    "har_oa3_active_conversions", "Number of conversions currently being processed"
)


def init_telemetry(
    service_name: str = "har-oa3-converter",
    exporter: str = "console",
    exporter_endpoint: Optional[str] = None,
    metrics_port: Optional[int] = None,
    attributes: Optional[Dict[str, str]] = None,
) -> None:
    """Initialize OpenTelemetry and Prometheus metrics.

    Args:
        service_name: Name of the service for telemetry reporting
        exporter: Type of exporter to use ('console', 'otlp', or 'none')
        exporter_endpoint: Endpoint for OTLP exporter
        metrics_port: Port to expose Prometheus metrics on
        attributes: Additional resource attributes
    """
    global _tracer_provider, _tracer

    # Create resource with service information
    resource_attributes = {
        "service.name": service_name,
        "service.namespace": "har_oa3_converter",
        "service.version": os.environ.get("SERVICE_VERSION", "dev"),
    }

    # Add custom attributes if provided
    if attributes:
        resource_attributes.update(attributes)

    # Use Resource.create with type annotations that match expected types
    # Resource.create expects Mapping which is covariant, not Dict which is invariant
    from typing import Mapping

    resource = Resource.create({k: v for k, v in resource_attributes.items()})

    # Create tracer provider with resource
    _tracer_provider = TracerProvider(resource=resource)

    # Configure exporter based on type
    if exporter.lower() == "console":
        # Console exporter for development and debugging
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
        _tracer_provider.add_span_processor(span_processor)
        logger.info("Configured OpenTelemetry with console exporter")
    elif exporter.lower() == "otlp":
        # OTLP (OpenTelemetry Protocol) exporter for production use
        if not exporter_endpoint:
            exporter_endpoint = os.environ.get(
                "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
            )

        otlp_exporter = OTLPSpanExporter(endpoint=exporter_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        _tracer_provider.add_span_processor(span_processor)
        logger.info(
            f"Configured OpenTelemetry with OTLP exporter at {exporter_endpoint}"
        )
    elif exporter.lower() == "none":
        # No exporter, just use logging
        logger.info("OpenTelemetry tracing disabled (exporter=none)")
    else:
        logger.warning(
            f"Unknown exporter type '{exporter}', defaulting to console exporter"
        )
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
        _tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider and get tracer
    trace.set_tracer_provider(_tracer_provider)
    _tracer = trace.get_tracer(__name__)

    # Start Prometheus metrics server if port is specified
    if metrics_port:
        try:
            start_http_server(metrics_port)
            logger.info(f"Started Prometheus metrics server on port {metrics_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {str(e)}")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer for creating spans.

    Returns:
        OpenTelemetry tracer
    """
    global _tracer

    if _tracer is None:
        # Initialize with defaults if not already done
        init_telemetry()

    # Ensure we always return a valid Tracer and never None
    if _tracer is None:
        # Fallback to a no-op tracer if initialization failed somehow
        logger.warning("Telemetry not initialized properly, using no-op tracer")
        return trace.get_tracer("har_oa3_converter_noop")

    return _tracer


T = TypeVar("T")


def traced(
    span_name: Optional[str] = None, attributes: Optional[Dict[str, str]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add OpenTelemetry tracing to a function.

    Args:
        span_name: Name for the span (defaults to function name)
        attributes: Additional span attributes

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            tracer = get_tracer()
            name = span_name or func.__name__

            with tracer.start_as_current_span(name) as span:
                # Add standard attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Add custom attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def timed(
    metric_histogram: Histogram, labels: Optional[Dict[str, str]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to measure function execution time using Prometheus metrics.

    Args:
        metric_histogram: Prometheus histogram to record times in
        labels: Labels to attach to metrics

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            label_values = labels or {}
            with metric_histogram.labels(**label_values).time():
                return func(*args, **kwargs)

        return wrapper

    return decorator


def conversion_metrics(
    source_format: str, target_format: str
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add conversion-specific metrics and tracing.

    Args:
        source_format: Source format name
        target_format: Target format name

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Increment active conversion gauge
            active_conversions.inc()

            try:
                # Start timer for conversion duration
                with conversion_duration.labels(
                    source_format=source_format, target_format=target_format
                ).time():
                    # Execute conversion function
                    result = func(*args, **kwargs)

                # Record successful conversion
                conversion_counter.labels(
                    source_format=source_format,
                    target_format=target_format,
                    status="success",
                ).inc()

                return result
            except Exception as e:
                # Record failed conversion
                conversion_counter.labels(
                    source_format=source_format,
                    target_format=target_format,
                    status="error",
                ).inc()
                raise
            finally:
                # Decrement active conversion gauge
                active_conversions.dec()

        return wrapper

    return decorator


def configure_telemetry_from_env() -> None:
    """Configure telemetry based on environment variables."""
    service_name = os.environ.get("OTEL_SERVICE_NAME", "har-oa3-converter")
    exporter = os.environ.get("OTEL_EXPORTER", "console")
    exporter_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    metrics_port_str = os.environ.get("PROMETHEUS_METRICS_PORT")
    metrics_port = int(metrics_port_str) if metrics_port_str else None

    # Get additional attributes from environment
    attributes = {}
    for key, value in os.environ.items():
        if key.startswith("OTEL_RESOURCE_ATTR_"):
            attr_name = key[19:].lower().replace("_", ".")
            attributes[attr_name] = value

    init_telemetry(
        service_name=service_name,
        exporter=exporter,
        exporter_endpoint=exporter_endpoint,
        metrics_port=metrics_port,
        attributes=attributes,
    )
