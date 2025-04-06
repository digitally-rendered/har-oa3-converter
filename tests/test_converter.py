"""Tests for the converter module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converter import HarToOas3Converter


@pytest.fixture
def sample_har_data():
    """Sample HAR data for testing."""
    return {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "queryString": [
                            {"name": "page", "value": "1"},
                            {"name": "limit", "value": "10"},
                        ],
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                            {"name": "Authorization", "value": "Bearer token123"},
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
                                {
                                    "data": [
                                        {
                                            "id": 1,
                                            "name": "John Doe",
                                            "email": "john@example.com",
                                        },
                                        {
                                            "id": 2,
                                            "name": "Jane Smith",
                                            "email": "jane@example.com",
                                        },
                                    ],
                                    "total": 2,
                                    "page": 1,
                                    "limit": 10,
                                }
                            ),
                        },
                    },
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/api/users",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                            {"name": "Authorization", "value": "Bearer token123"},
                        ],
                        "postData": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {"name": "New User", "email": "newuser@example.com"}
                            ),
                        },
                    },
                    "response": {
                        "status": 201,
                        "statusText": "Created",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {
                                    "id": 3,
                                    "name": "New User",
                                    "email": "newuser@example.com",
                                }
                            ),
                        },
                    },
                },
            ]
        }
    }


@pytest.fixture
def sample_har_file(sample_har_data):
    """Create a temporary HAR file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_har_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestHarToOas3Converter:
    """Test class for HarToOas3Converter."""

    def test_init(self):
        """Test initialization with default parameters."""
        converter = HarToOas3Converter()
        assert converter.info["title"] == "API generated from HAR"
        assert converter.info["version"] == "1.0.0"
        assert converter.paths == {}

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        info = {"title": "Custom API", "version": "2.0.0"}
        servers = [{"url": "https://example.com"}]

        converter = HarToOas3Converter(base_path="/api", info=info, servers=servers)

        assert converter.info == info
        assert converter.servers == servers
        assert converter.base_path == "/api"

    def test_load_har(self, sample_har_file):
        """Test loading HAR file."""
        converter = HarToOas3Converter()
        har_data = converter.load_har(sample_har_file)

        assert "log" in har_data
        assert "entries" in har_data["log"]
        assert len(har_data["log"]["entries"]) == 2

    def test_extract_paths_from_har(self, sample_har_data):
        """Test extracting paths from HAR data."""
        converter = HarToOas3Converter()
        converter.extract_paths_from_har(sample_har_data)

        assert "/api/users" in converter.paths
        assert "get" in converter.paths["/api/users"]
        assert "post" in converter.paths["/api/users"]

        # Verify GET path details
        get_path = converter.paths["/api/users"]["get"]
        assert get_path["operationId"] == "get_api_users"
        assert "parameters" in get_path
        assert "responses" in get_path
        assert "200" in get_path["responses"]

        # Verify POST path details
        post_path = converter.paths["/api/users"]["post"]
        assert post_path["operationId"] == "post_api_users"
        assert "requestBody" in post_path
        assert "responses" in post_path
        assert "201" in post_path["responses"]

    def test_generate_spec(self, sample_har_data):
        """Test generating OpenAPI spec."""
        converter = HarToOas3Converter()
        converter.extract_paths_from_har(sample_har_data)
        spec = converter.generate_spec()

        assert spec["openapi"] == "3.0.0"
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        assert "/api/users" in spec["paths"]

    def test_convert(self, sample_har_file):
        """Test full conversion process."""
        converter = HarToOas3Converter()

        # Convert without output file
        spec = converter.convert(sample_har_file)
        assert "openapi" in spec
        assert "paths" in spec

        # Convert with output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            spec = converter.convert(sample_har_file, output_path)

            # Verify file was created
            assert Path(output_path).exists()

            # Verify file content
            with open(output_path, "r", encoding="utf-8") as f:
                saved_spec = json.load(f)
                assert saved_spec == spec

        finally:
            # Cleanup
            if Path(output_path).exists():
                os.unlink(output_path)
