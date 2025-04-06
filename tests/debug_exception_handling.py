"""Debug test for exception handling in the API routes."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


def test_timeout_exception_handling(client):
    """Test that TimeoutError is properly caught and returns 408 status code."""
    # Create a minimal HAR file
    har_data = {"log": {"entries": []}}

    # Patch convert_file to raise a TimeoutError
    with patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=TimeoutError("Schema validation timeout"),
    ):
        # Make a direct request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("test.har", json.dumps(har_data), "application/json")},
        )

        # Check the response status code
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

        # Assert appropriate status code
        assert (
            response.status_code == 408
        ), f"Expected 408 status code but got {response.status_code}"


def test_memory_exception_handling(client):
    """Test that MemoryError is properly caught and returns 413 status code."""
    # Create a minimal HAR file
    har_data = {"log": {"entries": []}}

    # Patch convert_file to raise a MemoryError
    with patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=MemoryError("Not enough memory"),
    ):
        # Make a direct request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("test.har", json.dumps(har_data), "application/json")},
        )

        # Check the response status code
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

        # Assert appropriate status code
        assert (
            response.status_code == 413
        ), f"Expected 413 status code but got {response.status_code}"
