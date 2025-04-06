"""Additional tests to cover edge cases in the API routes module."""

import json
import tempfile
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat


def test_empty_file_upload():
    """Test handling when an empty file is uploaded."""
    client = TestClient(app)

    # Create an empty file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        empty_file_path = f.name

    try:
        # Test with empty file upload
        with open(empty_file_path, "rb") as f:
            files = {"file": ("empty.har", f, "application/json")}
            response = client.post(
                f"/api/convert/{ConversionFormat.OPENAPI3.value}", files=files
            )

        # Verify error response
        assert response.status_code == 400
        assert (
            "empty" in response.json()["detail"].lower()
            or "invalid" in response.json()["detail"].lower()
        )
    finally:
        # Cleanup
        if os.path.exists(empty_file_path):
            os.unlink(empty_file_path)


def test_unsupported_target_format():
    """Test handling when an unsupported target format is specified."""
    client = TestClient(app)

    # Create a valid HAR file
    valid_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test", "version": "1.0"},
            "entries": [],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(valid_har).encode("utf-8"))
        valid_file_path = f.name

    try:
        # Test with invalid target format by mocking the available formats
        with mock.patch(
            "har_oa3_converter.api.routes.get_available_formats"
        ) as mock_formats:
            mock_formats.return_value = ["swagger", "har"]

            with open(valid_file_path, "rb") as f:
                files = {"file": ("test.har", f, "application/json")}
                response = client.post("/api/convert/openapi3", files=files)

            # Verify error response
            assert response.status_code == 400
            assert "unsupported target format" in response.json()["detail"].lower()
    finally:
        # Cleanup
        if os.path.exists(valid_file_path):
            os.unlink(valid_file_path)


def test_har_file_extension_handling():
    """Test handling of HAR file extension detection."""
    client = TestClient(app)

    # Create a valid HAR content but with different file extension
    valid_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test", "version": "1.0"},
            "entries": [],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(valid_har).encode("utf-8"))
        json_file_path = f.name

    try:
        # Mock convert_file to verify the file extension correction
        with mock.patch("har_oa3_converter.api.routes.convert_file") as mock_convert:
            # Return a temporary output path to simulate successful conversion
            def mock_conversion(*args, **kwargs):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
                    f.write(json.dumps({"openapi": "3.0.0"}).encode("utf-8"))
                    return f.name

            mock_convert.side_effect = mock_conversion

            # Test with JSON file containing HAR content
            with open(json_file_path, "rb") as f:
                files = {"file": ("test.json", f, "application/json")}
                params = {"source_format": "har"}
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                    files=files,
                    params=params,
                )

            # Verify that conversion was attempted and file extension was handled
            assert mock_convert.called
            # Check that the input file had .har extension
            args, _ = mock_convert.call_args
            assert args[0].endswith(".har")
    finally:
        # Cleanup
        if os.path.exists(json_file_path):
            os.unlink(json_file_path)


def test_response_format_handling():
    """Test handling of response format based on Accept header."""
    client = TestClient(app)

    # Create a minimal valid HAR file
    valid_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test", "version": "1.0"},
            "entries": [
                {
                    "request": {"method": "GET", "url": "https://example.com/api"},
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                }
            ],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(valid_har).encode("utf-8"))
        valid_file_path = f.name

    try:
        # Set up our mocking strategy:
        # 1. Mock FileHandler.load to return valid content
        # 2. Mock convert_file to return a valid output path
        # This approach avoids the actual conversion logic while testing the response format
        with mock.patch(
            "har_oa3_converter.api.routes.convert_file"
        ) as mock_convert, mock.patch(
            "har_oa3_converter.api.routes.FileHandler", autospec=True
        ) as mock_file_handler:
            # Setup mock for FileHandler to return expected data
            mock_file_handler.load.return_value = {
                "openapi": "3.0.0",
                "info": {"title": "Test API"},
            }

            # Create a valid output file for JSON testing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as out_file:
                out_file.write(json.dumps({"openapi": "3.0.0"}).encode("utf-8"))
                output_path = out_file.name

            # Make convert_file return our temporary output path
            mock_convert.return_value = output_path

            # Test with a JSON Accept header
            with open(valid_file_path, "rb") as f:
                files = {"file": ("test.har", f, "application/json")}
                headers = {"Accept": "application/json"}
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                    files=files,
                    headers=headers,
                )

                # Verify response type and status
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/json"

            # Clean up the JSON output file before creating YAML file
            os.unlink(output_path)

            # Create a YAML output file for YAML testing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as out_file:
                yaml_content = "openapi: 3.0.0\ninfo:\n  title: Test API"
                out_file.write(yaml_content.encode("utf-8"))
                yaml_output_path = out_file.name

            # Update the mock to return our YAML file path
            mock_convert.return_value = yaml_output_path
            mock_file_handler.load.return_value = {
                "openapi": "3.0.0",
                "info": {"title": "Test API"},
            }

            # Test with YAML Accept header
            with open(valid_file_path, "rb") as f:
                files = {"file": ("test.har", f, "application/json")}
                headers = {"Accept": "application/yaml"}
                response = client.post(
                    f"/api/convert/{ConversionFormat.OPENAPI3.value}",
                    files=files,
                    headers=headers,
                )

                # Verify response has YAML content type
                assert response.status_code == 200
                assert "yaml" in response.headers["content-type"].lower()

            # Clean up the YAML output file
            os.unlink(yaml_output_path)
    finally:
        # Cleanup
        if os.path.exists(valid_file_path):
            os.unlink(valid_file_path)
