"""Telemetry configuration models.

This module provides data models for telemetry configuration based on JSON schema.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import jsonschema

from har_oa3_converter.utils import get_logger

logger = get_logger(__name__)

# Load the JSON schema for telemetry configuration
schema_path = Path(__file__).parent.parent / "schemas" / "telemetry_config.json"
with open(schema_path, "r") as f:
    TELEMETRY_CONFIG_SCHEMA = json.load(f)


class TelemetryConfig:
    """Telemetry configuration model.

    This class provides a structured way to represent telemetry configuration
    based on the JSON schema definition.
    """

    def __init__(
        self,
        enabled: bool = True,
        service_name: str = "har-oa3-converter",
        exporter: str = "console",
        exporter_endpoint: Optional[str] = None,
        metrics_port: Optional[int] = None,
        log_level: str = "info",
        attributes: Optional[Dict[str, str]] = None,
        sampling_rate: float = 1.0,
    ):
        """Initialize telemetry configuration.

        Args:
            enabled: Whether telemetry collection is enabled
            service_name: Name of the service for telemetry reporting
            exporter: Type of OpenTelemetry exporter to use
            exporter_endpoint: Endpoint URL for the OTLP exporter
            metrics_port: Port to expose Prometheus metrics on
            log_level: Log level for telemetry components
            attributes: Additional resource attributes
            sampling_rate: Sampling rate for traces (0.0-1.0)
        """
        self.enabled = enabled
        self.service_name = service_name
        self.exporter = exporter
        self.exporter_endpoint = exporter_endpoint
        self.metrics_port = metrics_port
        self.log_level = log_level
        self.attributes = attributes or {}
        self.sampling_rate = sampling_rate

        # Validate against schema
        self.validate()

    def validate(self) -> None:
        """Validate configuration against JSON schema.

        Raises:
            jsonschema.exceptions.ValidationError: If validation fails
        """
        jsonschema.validate(self.to_dict(), TELEMETRY_CONFIG_SCHEMA)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        config_dict = {
            "enabled": self.enabled,
            "service_name": self.service_name,
            "exporter": self.exporter,
            "log_level": self.log_level,
            "sampling_rate": self.sampling_rate,
            "attributes": self.attributes,
        }

        if self.exporter_endpoint:
            config_dict["exporter_endpoint"] = self.exporter_endpoint

        if self.metrics_port:
            config_dict["metrics_port"] = self.metrics_port

        return config_dict

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TelemetryConfig":
        """Create configuration from dictionary.

        Args:
            config_dict: Dictionary representation of configuration

        Returns:
            TelemetryConfig instance
        """
        return cls(
            enabled=config_dict.get("enabled", True),
            service_name=config_dict.get("service_name", "har-oa3-converter"),
            exporter=config_dict.get("exporter", "console"),
            exporter_endpoint=config_dict.get("exporter_endpoint"),
            metrics_port=config_dict.get("metrics_port"),
            log_level=config_dict.get("log_level", "info"),
            attributes=config_dict.get("attributes", {}),
            sampling_rate=config_dict.get("sampling_rate", 1.0),
        )

    @classmethod
    def from_json_file(cls, file_path: str) -> "TelemetryConfig":
        """Load configuration from JSON file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            TelemetryConfig instance
        """
        try:
            with open(file_path, "r") as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(
                f"Failed to load telemetry config from {file_path}: {str(e)}"
            )
            return cls()

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Load configuration from environment variables.

        Returns:
            TelemetryConfig instance
        """
        # Extract environment variables related to telemetry
        enabled = os.environ.get("TELEMETRY_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        service_name = os.environ.get("OTEL_SERVICE_NAME", "har-oa3-converter")
        exporter = os.environ.get("OTEL_EXPORTER", "console")
        exporter_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        metrics_port_str = os.environ.get("PROMETHEUS_METRICS_PORT")
        log_level = os.environ.get("TELEMETRY_LOG_LEVEL", "info")
        sampling_rate_str = os.environ.get("OTEL_TRACES_SAMPLER_ARG")

        # Convert numeric values
        metrics_port = int(metrics_port_str) if metrics_port_str else None
        sampling_rate = float(sampling_rate_str) if sampling_rate_str else 1.0

        # Extract custom attributes from environment
        attributes = {}
        for key, value in os.environ.items():
            if key.startswith("OTEL_RESOURCE_ATTR_"):
                attr_name = key[19:].lower().replace("_", ".")
                attributes[attr_name] = value

        return cls(
            enabled=enabled,
            service_name=service_name,
            exporter=exporter,
            exporter_endpoint=exporter_endpoint,
            metrics_port=metrics_port,
            log_level=log_level,
            attributes=attributes,
            sampling_rate=sampling_rate,
        )
