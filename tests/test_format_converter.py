"""Tests for the format converter module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.format_converter import (
    CONVERTERS,
    FORMAT_EXTENSIONS,
    FormatConverter,
    HarToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file,
)


@pytest.fixture
def sample_har_file():
    """Create a sample HAR file for testing."""
    sample_data = {
        "log": {
            "version": "1.2",
            "creator": {"name": "Browser DevTools", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "queryString": [{"name": "page", "value": "1"}],
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {"data": [{"id": 1, "name": "Test User"}]}
                            ),
                        },
                    },
                }
            ],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def sample_openapi3_file():
    """Create a sample OpenAPI 3 file for testing."""
    sample_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                    },
                                                },
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
        yaml.dump(sample_data, f)
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestFormatConverter:
    """Test class for format converter."""

    def test_get_available_formats(self):
        """Test getting available formats."""
        formats = get_available_formats()
        assert "har" in formats
        assert "openapi3" in formats
        assert "swagger" in formats

    def test_get_converter_for_formats(self):
        """Test getting converter for specific formats."""
        har_to_openapi = get_converter_for_formats("har", "openapi3")
        assert har_to_openapi == HarToOpenApi3Converter

        openapi_to_swagger = get_converter_for_formats("openapi3", "swagger")
        assert openapi_to_swagger == OpenApi3ToSwaggerConverter

        # Non-existent conversion
        nonexistent = get_converter_for_formats("swagger", "har")
        assert nonexistent is None

    def test_guess_format_from_file(self):
        """Test guessing format from file extension."""
        assert guess_format_from_file("test.har") == "har"
        assert guess_format_from_file("test.yaml") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.json") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.txt") is None

    def test_har_to_openapi3_conversion(self, sample_har_file):
        """Test HAR to OpenAPI 3 conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            output_path = f.name

        try:
            # Convert HAR to OpenAPI 3
            converter = HarToOpenApi3Converter()
            result = converter.convert(sample_har_file, output_path, title="Test API")

            assert result is not None
            assert "openapi" in result
            assert result["openapi"] == "3.0.0"
            assert "paths" in result
            assert "/api/users" in result["paths"]
            assert "get" in result["paths"]["/api/users"]

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                data = yaml.safe_load(f)
                assert data == result
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_openapi3_to_swagger_conversion(self, sample_openapi3_file):
        """Test OpenAPI 3 to Swagger conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            # Convert OpenAPI 3 to Swagger
            converter = OpenApi3ToSwaggerConverter()
            result = converter.convert(sample_openapi3_file, output_path)

            assert result is not None
            assert "swagger" in result
            assert result["swagger"] == "2.0"
            assert "paths" in result
            assert "/api/users" in result["paths"]
            assert "get" in result["paths"]["/api/users"]

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                data = json.load(f)
                assert data == result
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_convert_file(self, sample_har_file, sample_openapi3_file):
        """Test convert_file function."""
        # HAR to OpenAPI 3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            har_to_openapi_output = f.name

        # OpenAPI 3 to Swagger
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            openapi_to_swagger_output = f.name

        try:
            # Test HAR to OpenAPI 3
            result1 = convert_file(
                sample_har_file,
                har_to_openapi_output,
                "har",
                "openapi3",
                title="Test API",
            )

            assert result1 is not None
            assert "openapi" in result1
            assert os.path.exists(har_to_openapi_output)

            # Test OpenAPI 3 to Swagger
            result2 = convert_file(
                sample_openapi3_file, openapi_to_swagger_output, "openapi3", "swagger"
            )

            assert result2 is not None
            assert "swagger" in result2
            assert os.path.exists(openapi_to_swagger_output)

            # Test with format auto-detection
            with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
                auto_detect_output = f.name

            try:
                result3 = convert_file(sample_har_file, auto_detect_output)
                assert result3 is not None
                assert "openapi" in result3
                assert os.path.exists(auto_detect_output)
            finally:
                if os.path.exists(auto_detect_output):
                    os.unlink(auto_detect_output)

        finally:
            # Cleanup
            if os.path.exists(har_to_openapi_output):
                os.unlink(har_to_openapi_output)
            if os.path.exists(openapi_to_swagger_output):
                os.unlink(openapi_to_swagger_output)

    def test_nonexistent_file(self):
        """Test with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            convert_file("nonexistent.har", "output.yaml")

    def test_invalid_conversion(self, sample_har_file):
        """Test with invalid conversion."""
        with pytest.raises(ValueError):
            convert_file(sample_har_file, "output.txt", "har", "nonexistent_format")
