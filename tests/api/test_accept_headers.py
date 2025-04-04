"""Tests for Accept header handling in the API routes."""

import json
import tempfile
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat
from har_oa3_converter.utils.file_handler import FileHandler


def test_json_accept_header():
    """Test that the API correctly handles JSON Accept headers."""
    client = TestClient(app)
    
    # Create a simple valid HAR file
    valid_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api"
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "text": "{}"
                        }
                    }
                }
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(valid_har).encode("utf-8"))
        valid_file_path = f.name
    
    try:
        # Mock FileHandler and convert_file to avoid actual file processing
        # but still test the content type determination
        with mock.patch("har_oa3_converter.api.routes.convert_file") as mock_convert, \
             mock.patch.object(FileHandler, "load", return_value={"openapi": "3.0.0"}):
             
            # Set up the mock to return a temp file path with JSON content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_out:
                temp_out.write(json.dumps({"openapi": "3.0.0"}).encode("utf-8"))
                output_path = temp_out.name
            
            mock_convert.return_value = output_path
            
            # Test with JSON Accept header
            with open(valid_file_path, "rb") as f:
                files = {"file": ("test.har", f, "application/json")}
                headers = {"Accept": "application/json"}
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}", 
                    files=files, 
                    headers=headers
                )
                
            # Verify JSON response
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            
            # Cleanup the temp file
            os.unlink(output_path)
    finally:
        # Cleanup the input file
        if os.path.exists(valid_file_path):
            os.unlink(valid_file_path)
