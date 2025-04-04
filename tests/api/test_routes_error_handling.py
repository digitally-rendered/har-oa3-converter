"""Tests for error handling in API routes, focusing on JSON decoding errors."""

import json
import tempfile
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat


def test_api_json_decode_error():
    """Test handling of JSON decode errors in API routes."""
    client = TestClient(app)
    
    # Create an invalid JSON file that will trigger JSONDecodeError
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(b"This is not valid JSON")
        invalid_file_path = f.name
    
    try:
        # Test the API with the invalid file
        with open(invalid_file_path, "rb") as f:
            files = {"file": ("test.har", f, "application/json")}
            response = client.post(f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files)
        
        # Verify error response
        assert response.status_code == 400
        response_detail = response.json()["detail"].lower()
        assert any(term in response_detail for term in ["invalid", "file", "expecting value", "conversion failed"])
    finally:
        # Cleanup
        if os.path.exists(invalid_file_path):
            os.unlink(invalid_file_path)


def test_api_missing_file_error():
    """Test handling of missing file errors in API routes."""
    client = TestClient(app)
    
    # Send request without a file
    response = client.post(f"/api/convert/{ConversionFormat.OPENAPI3.value}")
    
    # Verify error response
    assert response.status_code == 422  # Validation error
    assert "file" in str(response.json()).lower()


def test_api_invalid_format_error():
    """Test handling of invalid format errors in API routes."""
    client = TestClient(app)
    
    # Create a valid JSON file but with invalid content for HAR
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps({"invalid": "content"}).encode("utf-8"))
        invalid_content_path = f.name
    
    try:
        # Test the API with the invalid content
        with open(invalid_content_path, "rb") as f:
            files = {"file": ("test.json", f, "application/json")}
            response = client.post(f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files)
        
        # Verify error response
        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
    finally:
        # Cleanup
        if os.path.exists(invalid_content_path):
            os.unlink(invalid_content_path)


def test_api_conversion_exception():
    """Test handling of exceptions during conversion in API routes."""
    client = TestClient(app)
    
    # Create a minimal valid HAR file
    valid_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test", "version": "1.0"},
            "entries": []
        }
    }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(valid_har).encode("utf-8"))
        valid_file_path = f.name
    
    try:
        # Mock the convert_file function to raise an exception
        with mock.patch("har_oa3_converter.api.routes.convert_file") as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            # Test the API with the valid file but mocked exception
            with open(valid_file_path, "rb") as f:
                files = {"file": ("test.har", f, "application/json")}
                response = client.post(f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files)
            
            # Verify error response - in the actual implementation, exceptions are converted to 400 errors
            assert response.status_code == 400
            assert "conversion failed" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower() or "error" in response.json()["detail"].lower()
    finally:
        # Cleanup
        if os.path.exists(valid_file_path):
            os.unlink(valid_file_path)
