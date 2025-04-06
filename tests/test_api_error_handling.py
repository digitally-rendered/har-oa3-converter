"""Tests for error handling in the API routes."""

import json
import tempfile
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


def test_api_timeout_exception(client):
    """Test API behavior when TimeoutError is raised during conversion."""
    # Create test data
    har_data = {"log": {"entries": []}}
    
    # Create a temporary file for consistent testing
    with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
        tmp_file.write(json.dumps(har_data).encode('utf-8'))
        tmp_path = tmp_file.name
    
    try:
        # Patch the convert_file function to raise TimeoutError
        # We need to patch at the module level where the function is actually called
        with patch('har_oa3_converter.converters.format_converter.convert_file', 
                  side_effect=TimeoutError("Schema validation timeout")), \
             patch('har_oa3_converter.api.routes.convert_file', 
                  side_effect=TimeoutError("Schema validation timeout")):
            
            # Send the API request with the test file
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                    files={"file": ("test.har", f)},
                )
            
            # Verify the response has a 408 status code
            assert response.status_code == 408, f"Expected 408 status code but got {response.status_code}"
            # Check that the response contains the expected error message
            response_data = response.json()
            assert "detail" in response_data
            assert "timeout" in response_data["detail"].lower() or "timed out" in response_data["detail"].lower()
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_api_memory_exception(client):
    """Test API behavior when MemoryError is raised during conversion."""
    # Create test data
    har_data = {"log": {"entries": []}}
    
    # Create a temporary file for consistent testing
    with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
        tmp_file.write(json.dumps(har_data).encode('utf-8'))
        tmp_path = tmp_file.name
    
    try:
        # Patch the convert_file function to raise MemoryError
        # We need to patch at the module level where the function is actually called
        with patch('har_oa3_converter.converters.format_converter.convert_file', 
                  side_effect=MemoryError("Not enough memory")), \
             patch('har_oa3_converter.api.routes.convert_file', 
                  side_effect=MemoryError("Not enough memory")):
            
            # Send the API request with the test file
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                    files={"file": ("large.har", f)},
                )
            
            # Verify the response has a 413 status code
            assert response.status_code == 413, f"Expected 413 status code but got {response.status_code}"
            # Check that the response contains the expected error message
            response_data = response.json()
            assert "detail" in response_data
            assert "memory" in response_data["detail"].lower() or "large" in response_data["detail"].lower()
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
