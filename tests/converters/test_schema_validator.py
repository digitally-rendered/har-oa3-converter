"""Tests for the schema validator module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converters.schema_validator import (
    validate_format,
    detect_format,
    validate_file,
    validate_schema_object,
    SUPPORTED_FORMATS,
)

# Import centralized schemas
from har_oa3_converter.schemas import (
    HAR_SCHEMA,
    OPENAPI3_SCHEMA,
    SWAGGER_SCHEMA,
    POSTMAN_SCHEMA,
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
                            "text": '{"data": []}',
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
            "/api/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "OK"}},
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
            "/api/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }


@pytest.fixture
def sample_postman_data():
    """Sample Postman Collection data for testing."""
    return {
        "info": {
            "name": "Test Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_postman_id": "test-id",
        },
        "item": [
            {
                "name": "Test Request",
                "request": {"method": "GET", "url": "https://example.com/api/users"},
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
def sample_openapi3_file(sample_openapi3_data):
    """Create a sample OpenAPI 3 file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_openapi3_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def sample_swagger_file(sample_swagger_data):
    """Create a sample Swagger 2.0 file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_swagger_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def sample_postman_file(sample_postman_data):
    """Create a sample Postman Collection file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_postman_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestSchemaValidator:
    """Test class for schema validator module."""

    def test_validate_format_har(self, sample_har_data):
        """Test validating HAR format."""
        is_valid, error = validate_format(sample_har_data, "har")
        assert is_valid
        assert error is None

        # Test invalid HAR data
        invalid_data = {"log": {}}
        is_valid, error = validate_format(invalid_data, "har")
        assert not is_valid
        assert error is not None
        assert "Validation error" in error

    def test_validate_format_openapi3(self, sample_openapi3_data):
        """Test validating OpenAPI 3 format."""
        is_valid, error = validate_format(sample_openapi3_data, "openapi3")
        assert is_valid
        assert error is None

        # Test invalid OpenAPI 3 data
        invalid_data = {"openapi": "3.0.0"}
        is_valid, error = validate_format(invalid_data, "openapi3")
        assert not is_valid
        assert error is not None

    def test_validate_format_swagger(self, sample_swagger_data):
        """Test validating Swagger format."""
        is_valid, error = validate_format(sample_swagger_data, "swagger")
        assert is_valid
        assert error is None

        # Test invalid Swagger data
        invalid_data = {"swagger": "2.0"}
        is_valid, error = validate_format(invalid_data, "swagger")
        assert not is_valid
        assert error is not None

    def test_validate_format_postman(self, sample_postman_data):
        """Test validating Postman format."""
        is_valid, error = validate_format(sample_postman_data, "postman")
        assert is_valid
        assert error is None

        # Test invalid Postman data
        invalid_data = {"info": {"name": "Test"}}
        is_valid, error = validate_format(invalid_data, "postman")
        assert not is_valid
        assert error is not None

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
        format_name, error = detect_format({"foo": "bar"})
        assert format_name is None
        assert error is not None
        assert "Unable to detect format" in error

        # Test with empty dict
        format_name, error = detect_format({})
        assert format_name is None
        assert error is not None

        # Verify SUPPORTED_FORMATS contains all expected formats
        assert all(
            format in SUPPORTED_FORMATS
            for format in ["har", "openapi3", "swagger", "postman"]
        )

    def test_validate_file_har(self, sample_har_file):
        """Test validating HAR file."""
        is_valid, format_name, error = validate_file(sample_har_file)
        assert is_valid
        assert format_name == "har"
        assert error is None

    def test_validate_file_openapi3(self, sample_openapi3_file):
        """Test validating OpenAPI 3 file."""
        is_valid, format_name, error = validate_file(sample_openapi3_file)
        assert is_valid
        assert format_name == "openapi3"
        assert error is None

    def test_validate_file_swagger(self, sample_swagger_file):
        """Test validating Swagger file."""
        is_valid, format_name, error = validate_file(sample_swagger_file)
        assert is_valid
        assert format_name == "swagger"
        assert error is None

    def test_validate_file_postman(self, sample_postman_file):
        """Test validating Postman file."""
        is_valid, format_name, error = validate_file(sample_postman_file)
        assert is_valid
        assert format_name == "postman"
        assert error is None

    def test_validate_file_nonexistent(self):
        """Test validating nonexistent file."""
        with pytest.raises(Exception):
            validate_file("nonexistent.json")

    def test_validate_file_invalid_json(self):
        """Test validating file with invalid JSON."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(b"invalid json")
            file_path = f.name

        try:
            is_valid, format_name, error = validate_file(file_path)
            assert not is_valid
            assert format_name is None
            assert "Failed to load file" in error
            assert "Expecting value" in error
        finally:
            os.unlink(file_path)
