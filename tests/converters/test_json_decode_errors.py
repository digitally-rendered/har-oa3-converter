"""Tests for JSON decode error handling in converter modules."""

import json
import os
import tempfile
from unittest import mock

import pytest
import yaml

from har_oa3_converter.converters.format_converter import (
    HarToOpenApi3Converter,
    OpenApi3ToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
    convert_file,
)
from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter
from har_oa3_converter.converters.schema_validator import validate_file


def test_har_to_oas3_json_decode_error():
    """Test handling of JSON decode errors in HarToOas3Converter."""
    # Create an invalid JSON file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(b"This is not valid JSON")
        invalid_file_path = f.name

    try:
        converter = HarToOas3Converter()

        # Should raise the appropriate exception
        with pytest.raises(json.JSONDecodeError):
            converter.convert(invalid_file_path)
    finally:
        os.unlink(invalid_file_path)


def test_har_to_openapi3_converter_json_decode_error():
    """Test handling of JSON decode errors in HarToOpenApi3Converter."""
    # Create an invalid JSON file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(b"This is not valid JSON")
        invalid_file_path = f.name

    try:
        # Mock the validation to bypass it
        with mock.patch(
            "har_oa3_converter.converters.format_converter.validate_file"
        ) as mock_validate:
            mock_validate.return_value = (True, "har", None)

            converter = HarToOpenApi3Converter()

            # Should properly handle and wrap the exception
            with pytest.raises(ValueError) as excinfo:
                converter.convert(invalid_file_path)

            # Error message may vary but should be related to JSON parsing
            error_msg = str(excinfo.value).lower()
            assert (
                "json" in error_msg
                or "expecting value" in error_msg
                or "decode" in error_msg
            )
    finally:
        os.unlink(invalid_file_path)


def test_openapi3_to_openapi3_converter_json_decode_error():
    """Test handling of JSON decode errors in OpenApi3ToOpenApi3Converter."""
    # Create an invalid JSON file with .json extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(b"This is not valid JSON")
        invalid_file_path = f.name

    try:
        # Mock the validation to bypass it and focus on JSON decoding
        with mock.patch(
            "har_oa3_converter.converters.format_converter.validate_file"
        ) as mock_validate:
            mock_validate.return_value = (True, "openapi3", None)

            converter = OpenApi3ToOpenApi3Converter()

            # Should properly handle and wrap the exception
            with pytest.raises(ValueError) as excinfo:
                converter.convert(invalid_file_path)

            # Error message may vary but should be related to JSON parsing
            error_msg = str(excinfo.value).lower()
            assert (
                "json" in error_msg
                or "expecting value" in error_msg
                or "decode" in error_msg
                or "decode" in str(excinfo.value).lower()
            )
    finally:
        os.unlink(invalid_file_path)


def test_yaml_decode_error():
    """Test handling of YAML decode errors."""
    # Create an invalid YAML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        f.write(b"invalid: - yaml: content: :")
        invalid_file_path = f.name

    try:
        # Mock validation to bypass it
        with mock.patch(
            "har_oa3_converter.converters.format_converter.validate_file"
        ) as mock_validate:
            mock_validate.return_value = (True, "openapi3", None)

            converter = OpenApi3ToOpenApi3Converter()

            # Should handle YAML parse errors
            with pytest.raises((yaml.YAMLError, ValueError)) as excinfo:
                converter.convert(invalid_file_path)

            # Verify error message contains YAML information
            error_message = str(excinfo.value).lower()
            assert "yaml" in error_message or "parse" in error_message
    finally:
        os.unlink(invalid_file_path)


def test_convert_file_json_decode_error():
    """Test handling of JSON decode errors in convert_file function."""
    # Create an invalid JSON file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(b"This is not valid JSON")
        source_path = f.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        target_path = f.name

    try:
        # Test convert_file with explicit format to avoid auto-detection issues
        with pytest.raises(ValueError) as excinfo:
            convert_file(
                source_path=source_path,
                target_path=target_path,
                source_format="openapi3",
                target_format="swagger",
            )

        # Error message may vary but should have JSON-related terms
        error_msg = str(excinfo.value).lower()
        assert (
            "invalid" in error_msg
            or "json" in error_msg
            or "expecting value" in error_msg
            or "decode" in error_msg
        )
    finally:
        # Cleanup
        for path in [source_path, target_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_schema_validator_json_decode_error():
    """Test handling of JSON decode errors in schema validator."""
    # Create an invalid JSON file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(b"{ Invalid JSON")
        invalid_file_path = f.name

    try:
        # Should properly handle JSON decode errors
        is_valid, format_name, error = validate_file(invalid_file_path)

        # Validation should fail with appropriate error
        assert is_valid is False
        assert error is not None  # There should be an error message
        error_lower = error.lower() if error else ""
        assert (
            "json" in error_lower
            or "expecting value" in error_lower
            or "decode" in error_lower
            or "invalid" in error_lower
        )
    finally:
        os.unlink(invalid_file_path)
