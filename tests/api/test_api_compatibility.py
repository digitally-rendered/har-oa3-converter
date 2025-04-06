"""API compatibility tests for schema validation using pytest directly instead of Schemathesis."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import jsonschema

from har_oa3_converter.api.server import app, custom_openapi
from har_oa3_converter.api.models import ConversionFormat

# Make sure we use the custom OpenAPI schema with version 3.0.3
app.openapi = custom_openapi


# Create a test client
@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def openapi_schema():
    """Get the OpenAPI schema from the app."""
    return app.openapi()


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


def test_openapi_schema_structure_valid(openapi_schema):
    """Test that the OpenAPI schema structure is valid."""
    # Verify OpenAPI version is set to 3.0.3 as needed for Schemathesis
    assert openapi_schema["openapi"] == "3.0.3"

    # Verify that paths exist
    assert "paths" in openapi_schema
    assert "/api/formats" in openapi_schema["paths"]
    assert "/api/convert/{target_format}" in openapi_schema["paths"]


def test_json_schema_validation_present(openapi_schema):
    """Test that JSON schema validation is present in the schema."""
    # Check if the validation extension is included in request body schemas
    for path_data in openapi_schema["paths"].values():
        for operation in path_data.values():
            if "requestBody" in operation and "content" in operation["requestBody"]:
                for content_type, content_schema in operation["requestBody"][
                    "content"
                ].items():
                    if "schema" in content_schema:
                        assert "x-json-schema-validation" in content_schema["schema"]


def test_api_formats_endpoint(client):
    """Test the formats endpoint returns valid list of formats."""
    response = client.get("/api/formats")
    assert response.status_code == 200

    data = response.json()

    # Handle both structured response (FormatResponse) and legacy list format
    if isinstance(data, dict) and "formats" in data:
        # New structured format with FormatResponse model
        formats = data["formats"]
        assert isinstance(formats, list)

        # Extract format names from the format objects
        format_names = [fmt["name"] for fmt in formats if "name" in fmt]
        assert "har" in format_names
        assert "openapi3" in format_names
        assert "swagger" in format_names
    else:
        # Legacy list format (backward compatibility)
        assert isinstance(data, list)
        assert "har" in data
        assert "openapi3" in data
        assert "swagger" in data


def test_api_convert_endpoint_with_har(client, sample_har_file):
    """Test the convert endpoint with a valid HAR file."""
    target_format = ConversionFormat.OPENAPI3.value

    with open(sample_har_file, "rb") as f:
        files = {"file": ("test.har", f, "application/json")}
        response = client.post(
            f"/api/convert/{target_format}",
            files=files,
            data={"title": "Test API", "version": "1.0.0"},
        )

    assert response.status_code == 200
    result = response.json()

    # Check the returned document is a valid OpenAPI 3.0 schema
    assert "openapi" in result
    assert result["openapi"].startswith("3.")
    assert "info" in result
    assert "title" in result["info"]
    assert "paths" in result


def test_api_input_validation(client):
    """Test input validation for the API endpoints."""
    # Test missing file
    response = client.post(f"/api/convert/{ConversionFormat.OPENAPI3.value}")
    assert response.status_code in [400, 422]

    # Test invalid format
    with tempfile.NamedTemporaryFile(delete=False) as invalid_file:
        invalid_file.write(b"This is not a valid HAR file")
        invalid_file.flush()

        with open(invalid_file.name, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = client.post(
                f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files
            )

        os.unlink(invalid_file.name)

    assert response.status_code in [400, 422]
    error_data = response.json()
    assert "detail" in error_data


def test_api_accept_header_handling(client, sample_har_file):
    """Test handling of Accept headers for content negotiation."""
    formats_and_headers = [
        ("application/json", "application/json"),
        ("application/yaml", "application/yaml"),
        ("application/x-yaml", "application/yaml"),
        ("text/yaml", "application/yaml"),
    ]

    for accept_header, expected_content_type in formats_and_headers:
        with open(sample_har_file, "rb") as f:
            files = {"file": ("test.har", f, "application/json")}
            headers = {"Accept": accept_header}
            response = client.post(
                f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                files=files,
                headers=headers,
            )

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        assert content_type.lower() == expected_content_type.lower()


def test_api_custom_options(client, sample_har_file):
    """Test that custom options are properly applied."""
    custom_title = "Custom API Test Title"
    custom_version = "2.5.0"
    custom_description = "Custom API Description for Testing"

    with open(sample_har_file, "rb") as f:
        files = {"file": ("test.har", f, "application/json")}
        data = {
            "title": custom_title,
            "version": custom_version,
            "description": custom_description,
            "servers": "https://api.example.com",
        }
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files, data=data
        )

    assert response.status_code == 200
    result = response.json()

    # Verify our custom options were applied
    assert result["info"]["title"] == custom_title
    assert result["info"]["version"] == custom_version
    assert result["info"]["description"] == custom_description
