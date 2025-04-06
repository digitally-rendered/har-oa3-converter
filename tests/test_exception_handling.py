"""Tests for exception handling in the API routes."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_408_REQUEST_TIMEOUT, HTTP_413_REQUEST_ENTITY_TOO_LARGE

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


def test_timeout_exception_handling(client):
    """Test that TimeoutError is properly caught and returns 408 status code."""
    # Create a minimal HAR file for testing
    har_data = {"log": {"entries": []}}

    # Mock convert_file to raise TimeoutError at both levels
    with patch(
        "har_oa3_converter.converters.format_converter.convert_file",
        side_effect=TimeoutError("Schema validation timeout"),
    ), patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=TimeoutError("Schema validation timeout"),
    ):
        # Make the request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("test.har", json.dumps(har_data), "application/json")},
        )

        # Check response
        assert (
            response.status_code == HTTP_408_REQUEST_TIMEOUT
        ), f"Expected 408 status code but got {response.status_code}"
        # Verify the response contains the expected error message
        response_data = response.json()
        assert "detail" in response_data
        assert (
            "timeout" in response_data["detail"].lower()
            or "timed out" in response_data["detail"].lower()
        )


def test_memory_error_handling(client):
    """Test that MemoryError is properly caught and returns 413 status code."""
    # Create a minimal HAR file for testing
    har_data = {"log": {"entries": []}}

    # Mock convert_file to raise MemoryError at both levels
    with patch(
        "har_oa3_converter.converters.format_converter.convert_file",
        side_effect=MemoryError("Not enough memory"),
    ), patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=MemoryError("Not enough memory"),
    ):
        # Make the request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("large.har", json.dumps(har_data), "application/json")},
        )

        # Check response
        assert (
            response.status_code == HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ), f"Expected 413 status code but got {response.status_code}"
        # Verify the response contains the expected error message
        response_data = response.json()
        assert "detail" in response_data
        assert (
            "memory" in response_data["detail"].lower()
            or "large" in response_data["detail"].lower()
        )
