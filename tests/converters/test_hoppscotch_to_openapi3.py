"""Tests for the Hoppscotch to OpenAPI 3 converter."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converters.format_registry import convert_file
from har_oa3_converter.converters.formats.hoppscotch_to_openapi3 import (
    HoppscotchToOpenApi3Converter,
)


@pytest.fixture
def sample_hoppscotch_collection():
    """Create a sample Hoppscotch collection for testing."""
    return {
        "v": 6,
        "name": "Sample API",
        "folders": [
            {
                "v": 6,
                "name": "Users",
                "folders": [],
                "requests": [
                    {
                        "v": "11",
                        "endpoint": "https://api.example.com/users/{id}",
                        "name": "Get User",
                        "method": "GET",
                        "params": [
                            {"key": "include", "value": "details", "active": True}
                        ],
                        "headers": [
                            {
                                "key": "Accept",
                                "value": "application/json",
                                "active": True,
                            }
                        ],
                        "auth": {
                            "authType": "bearer",
                            "authActive": True,
                            "token": "{{token}}",
                        },
                        "body": {"contentType": "", "body": ""},
                    }
                ],
                "auth": {"authType": "inherit", "authActive": True},
                "headers": [],
            }
        ],
        "requests": [
            {
                "v": "11",
                "endpoint": "https://api.example.com/login",
                "name": "Login",
                "method": "POST",
                "params": [],
                "headers": [
                    {"key": "Content-Type", "value": "application/json", "active": True}
                ],
                "auth": {"authType": "none", "authActive": False},
                "body": {
                    "contentType": "application/json",
                    "body": '{\n  "username": "user1",\n  "password": "password123"\n}',
                },
            }
        ],
        "auth": {"authType": "bearer", "authActive": True, "token": "{{token}}"},
        "headers": [{"key": "User-Agent", "value": "Hoppscotch", "active": True}],
    }


def test_hoppscotch_to_openapi3_converter_init():
    """Test that the converter can be initialized."""
    converter = HoppscotchToOpenApi3Converter()
    assert converter.get_source_format() == "hoppscotch"
    assert converter.get_target_format() == "openapi3"


def test_hoppscotch_to_openapi3_converter_convert(sample_hoppscotch_collection):
    """Test that the converter can convert a Hoppscotch collection to OpenAPI 3."""
    # Create temporary files for source and target
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False
    ) as source_file, tempfile.NamedTemporaryFile(
        suffix=".json", delete=False
    ) as target_file:
        source_path = source_file.name
        target_path = target_file.name

    try:
        # Write the sample Hoppscotch collection to the source file
        with open(source_path, "w") as f:
            json.dump(sample_hoppscotch_collection, f)

        # Convert the file
        converter = HoppscotchToOpenApi3Converter()
        result = converter.convert(source_path, target_path)

        # Check that the result is a dictionary
        assert isinstance(result, dict)

        # Check that the result has the expected OpenAPI 3 structure
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result
        assert "components" in result

        # Check that the info section has the expected values
        assert result["info"]["title"] == "Sample API"
        assert result["info"]["version"] == "1.0.0"

        # Check that the paths section has the expected endpoints
        assert "/users/{id}" in result["paths"]
        assert "/login" in result["paths"]

        # Check that the paths have the expected methods
        assert "get" in result["paths"]["/users/{id}"]
        assert "post" in result["paths"]["/login"]

        # Check that the security schemes are defined
        assert "securitySchemes" in result["components"]
        assert "bearerAuth" in result["components"]["securitySchemes"]

        # Check that the target file was created and contains valid JSON
        with open(target_path, "r") as f:
            target_data = json.load(f)
            assert target_data == result

    finally:
        # Clean up temporary files
        for path in [source_path, target_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_format_registry_integration():
    """Test that the converter is properly registered in the format registry."""
    # Create temporary files for source and target
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False
    ) as source_file, tempfile.NamedTemporaryFile(
        suffix=".json", delete=False
    ) as target_file:
        source_path = source_file.name
        target_path = target_file.name

    try:
        # Write a minimal Hoppscotch collection to the source file
        minimal_collection = {
            "v": 6,
            "name": "Minimal API",
            "folders": [],
            "requests": [
                {
                    "v": "11",
                    "endpoint": "https://api.example.com/test",
                    "name": "Test Endpoint",
                    "method": "GET",
                    "params": [],
                    "headers": [],
                    "auth": {"authType": "none", "authActive": False},
                    "body": {"contentType": "", "body": ""},
                }
            ],
            "auth": {"authType": "none", "authActive": False},
            "headers": [],
        }

        with open(source_path, "w") as f:
            json.dump(minimal_collection, f)

        # Convert using the format registry
        result = convert_file(
            source_path,
            target_path,
            source_format="hoppscotch",
            target_format="openapi3",
        )

        # Check that the result is a dictionary with OpenAPI 3 structure
        assert isinstance(result, dict)
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result
        assert "/test" in result["paths"]

    finally:
        # Clean up temporary files
        for path in [source_path, target_path]:
            if os.path.exists(path):
                os.unlink(path)
