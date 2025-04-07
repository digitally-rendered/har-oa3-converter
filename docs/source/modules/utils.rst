Utilities Module
==============

.. py:module:: har_oa3_converter.utils

The utilities module provides common utilities used throughout the application.

Logging
-------

.. py:module:: har_oa3_converter.utils.logging

This module provides structured logging capabilities for the application.

.. py:function:: configure_logging(log_level=None, log_file=None)

   Configure the logging system with the specified log level and file.

   :param log_level: Log level (debug, info, warning, error)
   :type log_level: Optional[Union[str, int]]
   :param log_file: Path to log file (if None, logs to stdout)
   :type log_file: Optional[str]

.. py:function:: get_logger(name)

   Get a logger with the specified name, configured with the application settings.

   :param name: Logger name
   :type name: str
   :return: Configured logger
   :rtype: logging.Logger

Telemetry
---------

.. py:module:: har_oa3_converter.utils.telemetry

This module provides OpenTelemetry integration for distributed tracing and metrics.

.. py:function:: init_telemetry(service_name="har-oa3-converter", exporter=None, metrics_port=None)

   Initialize OpenTelemetry and Prometheus metrics.

   :param service_name: Name of the service for telemetry
   :type service_name: str
   :param exporter: Exporter type (console, otlp)
   :type exporter: Optional[str]
   :param metrics_port: Port for Prometheus metrics server
   :type metrics_port: Optional[int]

.. py:function:: get_tracer()

   Get the OpenTelemetry tracer for the application.

   :return: OpenTelemetry tracer
   :rtype: opentelemetry.trace.Tracer

.. py:decorator:: traced(name=None, labels=None)

   Decorator to add OpenTelemetry tracing to a function.

   :param name: Name of the span (defaults to function name)
   :type name: Optional[str]
   :param labels: Labels to add to the span
   :type labels: Optional[Dict[str, str]]
