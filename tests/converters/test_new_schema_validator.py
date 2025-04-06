"""Tests for the new schema validator module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converters.new_schema_validator import (
    validate_format,
    detect_format,
    validate_file,
    SUPPORTED_FORMATS,
)


@pytest.fixture
def sample_har_data():
    """Sample HAR data for testing."""
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Browser DevTools", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/resource",
                        "headers": [],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "text": '{"data":"example"}',
                            "mimeType": "application/json",
                        },
                    },
                }
            ],
        }
    }


@pytest.fixture
def sample_openapi3_data():
    """Sample OpenAPI 3 data for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/resource": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"data": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    }
                }
            }
        },
    }


@pytest.fixture
def sample_swagger_data():
    """Sample Swagger 2.0 data for testing."""
    return {
        "swagger": "2.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/resource": {"get": {"responses": {"200": {"description": "OK"}}}}
        },
    }


@pytest.fixture
def sample_postman_data():
    """Sample Postman Collection data for testing."""
    return {
        "info": {
            "_postman_id": "test-id",
            "name": "Test Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [
            {
                "name": "Test Request",
                "request": {
                    "method": "GET",
                    "url": {"raw": "https://example.com/api/resource"},
                },
                "response": [],
            }
        ],
    }


@pytest.fixture
def sample_har_file(sample_har_data):
    """Create a sample HAR file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_har_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def sample_invalid_file():
    """Create a sample invalid file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(b"invalid json")
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestNewSchemaValidator:
    """Test class for new schema validator module."""

    def test_validate_format_har(self, sample_har_data):
        """Test validating HAR format."""
        is_valid, error = validate_format(sample_har_data, "har")
        assert is_valid
        assert error is None

        # Test with invalid data
        invalid_data = {"invalid": "data"}
        is_valid, error = validate_format(invalid_data, "har")
        assert not is_valid
        assert error is not None
        assert "Validation error" in error

    def test_validate_format_openapi3(self, sample_openapi3_data):
        """Test validating OpenAPI 3 format."""
        is_valid, error = validate_format(sample_openapi3_data, "openapi3")
        assert is_valid
        assert error is None

    def test_validate_format_swagger(self, sample_swagger_data):
        """Test validating Swagger format."""
        is_valid, error = validate_format(sample_swagger_data, "swagger")
        assert is_valid
        assert error is None

    def test_validate_format_postman(self, sample_postman_data):
        """Test validating Postman format."""
        is_valid, error = validate_format(sample_postman_data, "postman")
        assert is_valid
        assert error is None

    def test_validate_format_unknown(self):
        """Test validating unknown format."""
        is_valid, error = validate_format({}, "unknown")
        assert not is_valid
        assert "Unknown format" in error

    def test_detect_format_har(self, sample_har_data):
        """Test detecting HAR format."""
        format_name, error = detect_format(sample_har_data)
        assert format_name == "har"
        assert error is None

    def test_detect_format_openapi3(self, sample_openapi3_data):
        """Test detecting OpenAPI 3 format."""
        format_name, error = detect_format(sample_openapi3_data)
        assert format_name == "openapi3"
        assert error is None

    def test_detect_format_swagger(self, sample_swagger_data):
        """Test detecting Swagger format."""
        format_name, error = detect_format(sample_swagger_data)
        assert format_name == "swagger"
        assert error is None

    def test_detect_format_postman(self, sample_postman_data):
        """Test detecting Postman format."""
        format_name, error = detect_format(sample_postman_data)
        assert format_name == "postman"
        assert error is None

    def test_detect_format_unknown(self):
        """Test detecting unknown format."""
        unknown_data = {"foo": "bar"}
        format_name, error = detect_format(unknown_data)
        assert format_name is None
        assert "Unable to detect format" in error

    def test_validate_file_har(self, sample_har_file):
        """Test validating a HAR file."""
        is_valid, format_name, error = validate_file(sample_har_file)
        assert is_valid
        assert format_name == "har"
        assert error is None

    def test_validate_file_nonexistent(self):
        """Test validating a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            validate_file("nonexistent.json")

    def test_validate_file_invalid(self, sample_invalid_file):
        """Test validating an invalid file."""
        is_valid, format_name, error = validate_file(sample_invalid_file)
        assert not is_valid
        assert format_name is None
        assert error is not None

    def test_supported_formats(self):
        """Test that all supported formats are defined."""
        assert "har" in SUPPORTED_FORMATS
        assert "openapi3" in SUPPORTED_FORMATS
        assert "swagger" in SUPPORTED_FORMATS
        assert "postman" in SUPPORTED_FORMATS
        assert len(SUPPORTED_FORMATS) == 4
