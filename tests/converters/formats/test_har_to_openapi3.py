"""Tests for the HAR to OpenAPI 3 converter."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from har_oa3_converter.converters.formats.har_to_openapi3 import HarToOpenApi3Converter


@pytest.fixture
def sample_har_data():
    """Sample HAR data for testing."""
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Test", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/users",
                        "httpVersion": "HTTP/1.1",
                        "headers": [{"name": "Accept", "value": "application/json"}],
                        "queryString": [{"name": "page", "value": "1"}],
                        "cookies": [],
                        "headersSize": -1,
                        "bodySize": -1,
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "httpVersion": "HTTP/1.1",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "cookies": [],
                        "content": {
                            "size": 74,
                            "mimeType": "application/json",
                            "text": '{"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}',
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": -1,
                    },
                    "cache": {},
                    "timings": {"send": 0, "wait": 0, "receive": 0},
                }
            ],
        }
    }


class TestHarToOpenApi3Converter:
    """Tests for the HAR to OpenAPI 3 converter."""

    def test_get_source_format(self):
        """Test the get_source_format class method."""
        assert HarToOpenApi3Converter.get_source_format() == "har"

    def test_get_target_format(self):
        """Test the get_target_format class method."""
        assert HarToOpenApi3Converter.get_target_format() == "openapi3"

    def test_convert_with_options(self, sample_har_data):
        """Test converting HAR to OpenAPI 3 with custom options."""
        # Create a temporary HAR file
        tmp_file_path = tempfile.mktemp(suffix=".json")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(sample_har_data, tmp_file)

        try:
            # Create a temporary output file
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as out_file:
                out_file_path = out_file.name

            # Mock the HarToOas3Converter to verify it's called with the right parameters
            with patch(
                "har_oa3_converter.converters.har_to_oas3.HarToOas3Converter.convert_from_string"
            ) as mock_convert:
                # Set up the mock to return a valid OpenAPI 3 spec
                mock_convert.return_value = {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Custom API Title",
                        "version": "2.0.0",
                        "description": "Custom API Description",
                    },
                    "paths": {},
                }

                # Create the converter and convert the file
                converter = HarToOpenApi3Converter()
                result = converter.convert(
                    tmp_file_path,
                    out_file_path,
                    title="Custom API Title",
                    version="2.0.0",
                    description="Custom API Description",
                    servers=[{"url": "https://api.example.com"}],
                )

                # Verify the result
                assert result["openapi"] == "3.0.0"
                assert result["info"]["title"] == "Custom API Title"
                assert result["info"]["version"] == "2.0.0"
                assert result["info"]["description"] == "Custom API Description"

                # Verify the mock was called once
                mock_convert.assert_called_once()

                # Verify the output file exists and contains the converted data
                assert os.path.exists(out_file_path)
                with open(out_file_path, "r") as f:
                    output_data = json.load(f)
                    assert output_data == result
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(out_file_path):
                os.unlink(out_file_path)

    def test_convert_without_target_path(self, sample_har_data):
        """Test converting HAR to OpenAPI 3 without specifying a target path."""
        # Create a temporary HAR file
        tmp_file_path = tempfile.mktemp(suffix=".json")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(sample_har_data, tmp_file)

        try:
            # Mock the HarToOas3Converter
            with patch(
                "har_oa3_converter.converters.har_to_oas3.HarToOas3Converter.convert_from_string"
            ) as mock_convert:
                # Set up the mock to return a valid OpenAPI 3 spec
                mock_convert.return_value = {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "API Documentation",
                        "version": "1.0.0",
                        "description": "API Documentation generated from HAR file",
                    },
                    "paths": {},
                }

                # Create the converter and convert the file without specifying a target path
                converter = HarToOpenApi3Converter()
                result = converter.convert(tmp_file_path)

                # Verify the result
                assert result["openapi"] == "3.0.0"
                assert result["info"]["title"] == "API Documentation"
                assert result["info"]["version"] == "1.0.0"

                # Verify the mock was called with the right parameters
                mock_convert.assert_called_once()
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
