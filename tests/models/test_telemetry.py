"""Tests for telemetry configuration models."""

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import jsonschema
import pytest

from har_oa3_converter.models.telemetry import TELEMETRY_CONFIG_SCHEMA, TelemetryConfig


def test_telemetry_config_init():
    """Test telemetry configuration initialization with default values."""
    config = TelemetryConfig()
    assert config.enabled is True
    assert config.service_name == "har-oa3-converter"
    assert config.exporter == "console"
    assert config.exporter_endpoint is None
    assert config.metrics_port is None
    assert config.log_level == "info"
    assert config.attributes == {}
    assert config.sampling_rate == 1.0


def test_telemetry_config_custom_values():
    """Test telemetry configuration with custom values."""
    config = TelemetryConfig(
        enabled=False,
        service_name="test-service",
        exporter="otlp",
        exporter_endpoint="http://collector:4317",
        metrics_port=9090,
        log_level="debug",
        attributes={"env": "test"},
        sampling_rate=0.5,
    )

    assert config.enabled is False
    assert config.service_name == "test-service"
    assert config.exporter == "otlp"
    assert config.exporter_endpoint == "http://collector:4317"
    assert config.metrics_port == 9090
    assert config.log_level == "debug"
    assert config.attributes == {"env": "test"}
    assert config.sampling_rate == 0.5


def test_telemetry_config_validation():
    """Test validation against JSON schema."""
    # Valid configuration should not raise exception
    valid_config = TelemetryConfig(
        enabled=True,
        service_name="test-service",
        exporter="console",
    )
    valid_config.validate()  # Should not raise

    # Invalid exporter value should raise exception
    with pytest.raises(jsonschema.exceptions.ValidationError):
        config = TelemetryConfig(
            service_name="test-service",
            exporter="invalid-exporter",  # Not in enum
        )
        config.validate()


def test_telemetry_config_to_dict():
    """Test converting configuration to dictionary."""
    config = TelemetryConfig(
        enabled=True,
        service_name="test-service",
        exporter="otlp",
        exporter_endpoint="http://collector:4317",
        metrics_port=9090,
        log_level="debug",
        attributes={"env": "test"},
        sampling_rate=0.5,
    )

    config_dict = config.to_dict()
    assert config_dict["enabled"] is True
    assert config_dict["service_name"] == "test-service"
    assert config_dict["exporter"] == "otlp"
    assert config_dict["exporter_endpoint"] == "http://collector:4317"
    assert config_dict["metrics_port"] == 9090
    assert config_dict["log_level"] == "debug"
    assert config_dict["attributes"] == {"env": "test"}
    assert config_dict["sampling_rate"] == 0.5

    # Test with optional fields as None
    config = TelemetryConfig(
        enabled=True,
        service_name="test-service",
    )

    config_dict = config.to_dict()
    assert "exporter_endpoint" not in config_dict
    assert "metrics_port" not in config_dict


def test_telemetry_config_from_dict():
    """Test creating configuration from dictionary."""
    config_dict = {
        "enabled": False,
        "service_name": "dict-service",
        "exporter": "otlp",
        "exporter_endpoint": "http://otlp:4317",
        "metrics_port": 9091,
        "log_level": "warning",
        "attributes": {"source": "dict"},
        "sampling_rate": 0.1,
    }

    config = TelemetryConfig.from_dict(config_dict)
    assert config.enabled is False
    assert config.service_name == "dict-service"
    assert config.exporter == "otlp"
    assert config.exporter_endpoint == "http://otlp:4317"
    assert config.metrics_port == 9091
    assert config.log_level == "warning"
    assert config.attributes == {"source": "dict"}
    assert config.sampling_rate == 0.1

    # Test with missing fields (should use defaults)
    minimal_dict = {"service_name": "minimal"}
    config = TelemetryConfig.from_dict(minimal_dict)
    assert config.enabled is True  # Default
    assert config.service_name == "minimal"
    assert config.exporter == "console"  # Default


def test_telemetry_config_from_json_file():
    """Test loading configuration from JSON file."""
    config_json = json.dumps(
        {
            "enabled": False,
            "service_name": "file-service",
            "exporter": "otlp",
            "metrics_port": 9092,
        }
    )

    # Mock open to return our JSON content
    with patch("builtins.open", mock_open(read_data=config_json)):
        config = TelemetryConfig.from_json_file("config.json")

    assert config.enabled is False
    assert config.service_name == "file-service"
    assert config.exporter == "otlp"
    assert config.metrics_port == 9092

    # Test handling file not found
    with patch("builtins.open", side_effect=FileNotFoundError()):
        config = TelemetryConfig.from_json_file("nonexistent.json")

    # Should return default config
    assert config.enabled is True
    assert config.service_name == "har-oa3-converter"

    # Test handling invalid JSON
    with patch("builtins.open", mock_open(read_data="invalid json")):
        config = TelemetryConfig.from_json_file("invalid.json")

    # Should return default config
    assert config.enabled is True
    assert config.service_name == "har-oa3-converter"


def test_telemetry_config_from_env():
    """Test loading configuration from environment variables."""
    # Save original environment
    original_env = os.environ.copy()

    try:
        # Set environment variables
        os.environ.clear()
        os.environ.update(
            {
                "TELEMETRY_ENABLED": "false",
                "OTEL_SERVICE_NAME": "env-service",
                "OTEL_EXPORTER": "otlp",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otlp:4317",
                "PROMETHEUS_METRICS_PORT": "9093",
                "TELEMETRY_LOG_LEVEL": "error",
                "OTEL_TRACES_SAMPLER_ARG": "0.25",
                "OTEL_RESOURCE_ATTR_DEPLOYMENT_ENV": "production",
                "OTEL_RESOURCE_ATTR_SERVICE_VERSION": "1.0.0",
            }
        )

        config = TelemetryConfig.from_env()

        assert config.enabled is False
        assert config.service_name == "env-service"
        assert config.exporter == "otlp"
        assert config.exporter_endpoint == "http://otlp:4317"
        assert config.metrics_port == 9093
        assert config.log_level == "error"
        assert config.sampling_rate == 0.25
        assert config.attributes["deployment.env"] == "production"
        assert config.attributes["service.version"] == "1.0.0"

        # Test with minimal environment
        os.environ.clear()
        config = TelemetryConfig.from_env()

        # Should use defaults
        assert config.enabled is True
        assert config.service_name == "har-oa3-converter"
        assert config.exporter == "console"

    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


def test_schema_validation():
    """Test that the schema itself is valid and properly formatted."""
    # Ensure the schema is valid
    jsonschema.Draft7Validator.check_schema(TELEMETRY_CONFIG_SCHEMA)

    # Check required fields are defined
    assert "properties" in TELEMETRY_CONFIG_SCHEMA
    assert "required" in TELEMETRY_CONFIG_SCHEMA
    assert "enabled" in TELEMETRY_CONFIG_SCHEMA["required"]
    assert "service_name" in TELEMETRY_CONFIG_SCHEMA["required"]

    # Check core property definitions
    properties = TELEMETRY_CONFIG_SCHEMA["properties"]
    assert "enabled" in properties
    assert "service_name" in properties
    assert "exporter" in properties
    assert "metrics_port" in properties

    # Check enum values for exporter
    assert "enum" in properties["exporter"]
    exporters = properties["exporter"]["enum"]
    assert "console" in exporters
    assert "otlp" in exporters
    assert "none" in exporters
