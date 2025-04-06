"""Tests for error handling in the routes.py file."""

import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


# We'll test the error handling through the API endpoints instead of directly calling the async functions
# This is more reliable and avoids issues with async testing


def test_memory_error_in_conversion(client):
    """Test that memory errors during conversion are properly handled by the API."""
    # Create a mock for the convert_file function that raises a MemoryError
    with patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=MemoryError("Test memory error"),
    ):
        # Create a simple test file
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            tmp.write(b'{"test": "data"}')
            tmp.flush()

            # Make a request to the API
            with open(tmp.name, "rb") as f:
                response = client.post(
                    "/api/convert/openapi3",
                    files={"file": ("test.json", f, "application/json")},
                )

            # Verify the response
            assert response.status_code == 413
            error = response.json()
            assert "detail" in error
            assert (
                "memory" in error["detail"].lower()
                or "too large" in error["detail"].lower()
            )


def test_timeout_error_in_conversion(client):
    """Test that timeout errors during conversion are properly handled by the API."""
    # Create a mock for the convert_file function that raises a TimeoutError
    with patch(
        "har_oa3_converter.api.routes.convert_file",
        side_effect=TimeoutError("Test timeout error"),
    ):
        # Create a simple test file
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            tmp.write(b'{"test": "data"}')
            tmp.flush()

            # Make a request to the API
            with open(tmp.name, "rb") as f:
                response = client.post(
                    "/api/convert/openapi3",
                    files={"file": ("test.json", f, "application/json")},
                )

            # Verify the response
            assert response.status_code == 408
            error = response.json()
            assert "detail" in error
            assert (
                "timeout" in error["detail"].lower()
                or "timed out" in error["detail"].lower()
            )
