"""Tests for API routes to increase coverage."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from fastapi import Depends, File, Form, UploadFile
from fastapi.testclient import TestClient

from har_oa3_converter.api.models import ConversionFormat, ConversionOptions
from har_oa3_converter.api.routes import (
    convert_document,
    get_conversion_options,
    router,
)
from har_oa3_converter.api.server import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


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


class TestApiRoutesExtra:
    """Additional tests for API routes to improve coverage."""

    def test_convert_options_model(self):
        """Test the ConversionOptions model directly."""
        # Test with defaults
        options = ConversionOptions()
        assert options.title is None
        assert options.version is None
        assert options.description is None
        assert options.servers is None
        assert options.base_path is None
        assert options.skip_validation is False

        # Test with custom values
        options = ConversionOptions(
            title="Test API",
            version="1.0.0",
            description="Test Description",
            servers=["https://example.com"],
            base_path="/api",
            skip_validation=True,
        )
        assert options.title == "Test API"
        assert options.version == "1.0.0"
        assert options.description == "Test Description"
        assert options.servers == ["https://example.com"]
        assert options.base_path == "/api"
        assert options.skip_validation is True

    @mock.patch("har_oa3_converter.api.routes.convert_file")
    def test_convert_document_json_content_response(
        self, mock_convert_file, client, sample_har_file
    ):
        """Test the convert_document endpoint with JSON content type."""
        # Mock convert_file to return a dict result
        mock_data = {"openapi": "3.0.0", "paths": {}}
        mock_convert_file.return_value = mock_data

        with open(sample_har_file, "rb") as f:
            response = client.post(
                "/api/convert/openapi3",
                files={"file": ("test.har", f, "application/json")},
                headers={"Accept": "application/json"},
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json()["openapi"] == "3.0.0"

    @mock.patch("har_oa3_converter.api.routes.convert_file")
    def test_convert_document_yaml_content_response(
        self, mock_convert_file, client, sample_har_file
    ):
        """Test the convert_document endpoint with YAML content type."""
        # Mock convert_file to return a dict result and bypass actual conversion
        mock_data = {"openapi": "3.0.0", "paths": {}}
        mock_convert_file.return_value = mock_data

        # Create a real sample file instead of mocking it
        sample_openapi = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(json.dumps(sample_openapi).encode("utf-8"))
            sample_file = f.name

        try:
            with open(sample_file, "rb") as f:
                response = client.post(
                    "/api/convert/openapi3?source_format=openapi3",
                    files={"file": ("test.json", f, "application/json")},
                    headers={"Accept": "application/yaml"},
                )

            assert response.status_code == 200
            assert "application/yaml" in response.headers["content-type"]
        finally:
            os.unlink(sample_file)

    @mock.patch("har_oa3_converter.api.routes.convert_file")
    def test_convert_document_with_accept_param(
        self, mock_convert_file, client, sample_har_file
    ):
        """Test the convert_document endpoint with explicit accept parameter."""
        # Mock convert_file to return a dict result
        mock_data = {"openapi": "3.0.0", "paths": {}}
        mock_convert_file.return_value = mock_data

        with open(sample_har_file, "rb") as f:
            response = client.post(
                "/api/convert/openapi3?accept=application/json",
                files={"file": ("test.har", f, "application/json")},
                headers={
                    "Accept": "application/yaml"
                },  # This will be overridden by the query param
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json()["openapi"] == "3.0.0"

    @mock.patch("har_oa3_converter.api.routes.convert_file")
    def test_convert_document_with_yaml_file_json_output(
        self, mock_convert_file, client
    ):
        """Test converting from YAML file to JSON output."""
        # Create a sample YAML file
        sample_yaml = (
            "openapi: 3.0.0\ninfo:\n  title: Test API\nversion: 1.0.0\npaths: {}"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            f.write(sample_yaml.encode("utf-8"))
            yaml_file = f.name

        try:
            # Mock convert_file to return a dict result
            mock_data = {"openapi": "3.0.0", "paths": {}}
            mock_convert_file.return_value = mock_data

            with open(yaml_file, "rb") as f:
                response = client.post(
                    "/api/convert/swagger?source_format=openapi3",
                    files={"file": ("test.yaml", f, "application/yaml")},
                    headers={"Accept": "application/json"},
                )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert response.json()["openapi"] == "3.0.0"
        finally:
            # Cleanup
            os.unlink(yaml_file)

    def test_convert_document_with_octet_stream_response(self, client, sample_har_file):
        """Test the convert_document endpoint with octet-stream content type."""
        with open(sample_har_file, "rb") as f:
            response = client.post(
                "/api/convert/openapi3",
                files={"file": ("test.har", f, "application/json")},
                headers={"Accept": "application/octet-stream"},
            )

        assert response.status_code == 200
        assert "application/" in response.headers["content-type"]

    def test_convert_document_with_json_extension(self, client):
        """Test converting a file with .json extension."""
        # Create a real sample JSON file
        sample_openapi = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(json.dumps(sample_openapi).encode("utf-8"))
            sample_file = f.name

        try:
            with open(sample_file, "rb") as f:
                response = client.post(
                    "/api/convert/swagger?source_format=openapi3",
                    files={"file": ("test.json", f, "application/json")},
                    headers={"Accept": "application/json"},
                )

            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
        finally:
            os.unlink(sample_file)
