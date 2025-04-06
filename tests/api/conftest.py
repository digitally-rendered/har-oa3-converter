"""Shared test fixtures for the API tests."""

import json
import os
import tempfile
from typing import Dict, List, Optional

import pytest
import yaml
import jsonschema
from fastapi.testclient import TestClient

import schemathesis
from har_oa3_converter.api.server import app, custom_openapi
from har_oa3_converter.api.models import (
    ConversionFormat,
    ConversionOptions,
    FormatInfo,
    FormatResponse,
)


@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="module")
def openapi_schema():
    """Get the OpenAPI schema from the app."""
    return app.openapi()


@pytest.fixture(scope="module")
def schema():
    """Create a Schemathesis schema for API testing.

    Returns a properly configured Schemathesis schema that uses the app directly
    instead of making HTTP connections. This helps avoid connection errors and
    ensures tests are run consistently.
    """
    # Get the OpenAPI schema compatible with Schemathesis
    from tests.api.test_schemathesis import SCHEMA

    # Create and return the schema with app provided directly to avoid HTTP connection issues
    return schemathesis.from_dict(
        SCHEMA,
        app=app,  # Provide the app directly to avoid HTTP connection errors
        base_url="http://testserver",  # This is still needed for formatting URLs
    )


def execute_schemathesis_case(case, expected_status_codes=None):
    """Execute a Schemathesis test case using the standardized approach.

    This helper function provides a consistent way to execute Schemathesis test cases,
    helping to future-proof tests against API changes in Schemathesis.

    Args:
        case: The Schemathesis test case to execute
        expected_status_codes: A list of expected HTTP status codes for the response
            (defaults to [200, 400, 404, 422])

    Returns:
        The response from executing the test case
    """
    if expected_status_codes is None:
        expected_status_codes = [200, 400, 404, 422]

    # Execute the test case with the current best practice method
    response = case.call()

    # Verify response has an expected status code
    assert (
        response.status_code in expected_status_codes
    ), f"Unexpected status code: {response.status_code}"

    return response


@pytest.fixture(scope="module")
def sample_har_file():
    """Create a sample HAR file for testing.

    Returns a path to a temporary HAR file with sample data that
    gets cleaned up automatically after the test.
    """
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


@pytest.fixture(scope="module")
def invalid_file():
    """Create an invalid test file for testing error cases."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"This is not a valid HAR file")
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture(scope="module")
def model_json_schemas():
    """Get JSON schemas for our models."""
    return {
        "FormatInfo": FormatInfo.model_json_schema(),
        "FormatResponse": FormatResponse.model_json_schema(),
        "ConversionOptions": ConversionOptions.model_json_schema(),
    }


@pytest.fixture(scope="function")
def standard_headers():
    """Return standard headers for API requests."""
    return {"Accept": "application/json", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_formats():
    """Return a list of supported formats for testing."""
    return [
        {"name": "openapi3", "format": ConversionFormat.OPENAPI3},
        {"name": "swagger", "format": ConversionFormat.SWAGGER},
        {"name": "har", "format": ConversionFormat.HAR},
    ]
