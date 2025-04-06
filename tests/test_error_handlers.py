"""Tests for error handling in the API routes."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat
from har_oa3_converter.api.routes import convert_document


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


def test_timeout_error_handler(client):
    """Test that TimeoutError is properly handled and returns HTTP 408."""
    # Create a test HAR file
    har_data = {"log": {"entries": []}}
    
    # Patch the convert_file function to raise TimeoutError at both levels
    with patch('har_oa3_converter.converters.format_converter.convert_file', 
              side_effect=TimeoutError("Schema validation timeout")), \
         patch('har_oa3_converter.api.routes.convert_file', 
              side_effect=TimeoutError("Schema validation timeout")):
        
        # Make the API request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("test.har", json.dumps(har_data), "application/json")},
        )
        
        # Verify it returns the expected status code and message
        assert response.status_code == 408, f"Expected 408 status code but got {response.status_code}"
        # Verify the response contains the expected error message
        response_data = response.json()
        assert "detail" in response_data
        assert "timeout" in response_data["detail"].lower() or "timed out" in response_data["detail"].lower()


def test_memory_error_handler(client):
    """Test that MemoryError is properly handled and returns HTTP 413."""
    # Create a test HAR file
    har_data = {"log": {"entries": []}}
    
    # Patch the convert_file function to raise MemoryError at both levels
    with patch('har_oa3_converter.converters.format_converter.convert_file',
              side_effect=MemoryError("Not enough memory")), \
         patch('har_oa3_converter.api.routes.convert_file',
              side_effect=MemoryError("Not enough memory")):
        
        # Make the API request
        response = client.post(
            f"/api/convert/{ConversionFormat.OPENAPI3.value}",
            files={"file": ("large.har", json.dumps(har_data), "application/json")},
        )
        
        # Verify it returns the expected status code and message
        assert response.status_code == 413, f"Expected 413 status code but got {response.status_code}"
        # Verify the response contains the expected error message
        response_data = response.json()
        assert "detail" in response_data
        assert "memory" in response_data["detail"].lower() or "large" in response_data["detail"].lower()
