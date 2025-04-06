"""Tests for error handling in API routes to increase coverage."""

import json
import os
import tempfile
from unittest import mock
from pathlib import Path

import pytest
from fastapi import UploadFile, HTTPException
from fastapi.testclient import TestClient

from har_oa3_converter.api.models import ConversionOptions, ConversionFormat
from har_oa3_converter.api.routes import (
    router,
    get_conversion_options,
    convert_document,
)
from har_oa3_converter.api.server import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_openapi_json():
    """Create a sample OpenAPI 3 JSON file for testing."""
    sample_data = {
        "openapi": "3.0.0",
        "info": {"title": "Sample API", "version": "1.0.0"},
        "paths": {},
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json.dumps(sample_data).encode("utf-8"))
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


class TestApiRoutesErrorHandling:
    """Tests for error handling in API routes to improve coverage."""

    def test_convert_document_no_file(self, client):
        """Test error when no file is uploaded."""
        # Call the API without providing a file
        response = client.post("/api/convert/openapi3")

        # FastAPI returns 422 for validation errors
        assert response.status_code == 422  # Unprocessable Entity
        assert "field required" in response.text.lower()

    def test_convert_document_invalid_target_format(self, client, sample_openapi_json):
        """Test error when an invalid target format is provided."""
        # Use an invalid target format
        with open(sample_openapi_json, "rb") as f:
            response = client.post(
                "/api/convert/invalid_format",
                files={"file": ("test.json", f, "application/json")},
            )

        # FastAPI returns 422 for validation errors (enum validation)
        assert response.status_code == 422
        # Check for the actual error message FastAPI is returning
        assert "input should be" in response.text.lower()

    def test_content_type_detection_yaml_suffix(self, client, sample_openapi_json):
        """Test content type detection with YAML suffix."""
        # Mock a file with a .yaml suffix
        with open(sample_openapi_json, "rb") as f:
            # Create a request with an accept header for JSON but a .yaml file
            response = client.post(
                "/api/convert/swagger?output_suffix=.yaml",
                files={"file": ("test.yaml", f, "application/yaml")},
                headers={"Accept": "application/yaml"},
            )

        # Verify response has the right content type
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/yaml"

    def test_json_to_yaml_conversion(self, client, sample_openapi_json):
        """Test converting from JSON input to YAML output format."""
        # Test JSON input to YAML output conversion path
        with open(sample_openapi_json, "rb") as f:
            response = client.post(
                "/api/convert/swagger?output_suffix=.yaml",
                files={"file": ("test.json", f, "application/json")},
                headers={"Accept": "application/yaml"},
            )

        # Verify response type is YAML
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/yaml"
        # Basic check that it looks like YAML (indentation with spaces)
        assert ":\n" in response.text
        assert "  " in response.text  # Check for indentation

    def test_yaml_file_with_json_output(self, client):
        """Test converting from YAML file to JSON output."""
        # Create a YAML file
        yaml_content = """openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths: {}"""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_content.encode("utf-8"))
            yaml_path = tmp.name

        try:
            # Test YAML input to JSON output conversion
            with open(yaml_path, "rb") as f:
                response = client.post(
                    "/api/convert/swagger?output_suffix=.json",
                    files={"file": ("test.yaml", f, "application/yaml")},
                    headers={"Accept": "application/json"},
                )

            # Verify response type is JSON
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            # Check it's valid JSON
            assert json.loads(response.content)
        finally:
            if os.path.exists(yaml_path):
                os.unlink(yaml_path)

    def test_response_with_custom_accept_header(self, client, sample_openapi_json):
        """Test the API respects the Accept header."""
        # Test with explicit application/json Accept header
        with open(sample_openapi_json, "rb") as f:
            response = client.post(
                "/api/convert/swagger",
                files={"file": ("test.json", f, "application/json")},
                headers={"Accept": "application/json"},
            )

        # Verify response matches requested content type
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_default_content_type_fallback(self, client, sample_openapi_json):
        """Test the default content-type when none is specified."""
        # Make a request without specifying content type
        with open(sample_openapi_json, "rb") as f:
            response = client.post(
                "/api/convert/swagger",
                files={"file": ("test.json", f, "")},  # No content-type
                # Explicitly don't set any Accept header
            )

        # Verify response still works (either JSON or YAML is fine)
        assert response.status_code == 200
        # Just check it returned a valid content type
        assert "application/" in response.headers["content-type"]
