"""Tests for edge cases and boundary conditions to improve coverage."""

import json
import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app
from har_oa3_converter.api.models import ConversionFormat
from har_oa3_converter.converters.format_converter import FormatConverter
from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def edge_case_inputs():
    """Fixture providing various edge case inputs for testing."""
    return {
        "empty_object": "{}",
        "minimal_har": json.dumps({"log": {"entries": []}}),
        "malformed_har": json.dumps({"log": {"entries": [{"invalid": True}]}}),
        "special_chars": json.dumps(
            {"log": {"entries": [{"request": {"url": "https://example.com/!@#$%^&*"}}]}}
        ),
        "duplicate_urls": json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "request": {
                                "method": "GET",
                                "url": "https://example.com/api/users",
                            }
                        },
                        {
                            "request": {
                                "method": "POST",
                                "url": "https://example.com/api/users",
                            }
                        },
                        {
                            "request": {
                                "method": "GET",
                                "url": "https://example.com/api/users",
                            }
                        },
                    ]
                }
            }
        ),
    }


def test_minimal_input(client, edge_case_inputs):
    """Test API with minimal valid input (line 218)."""
    # Test with minimal HAR file
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={
            "file": ("test.har", edge_case_inputs["minimal_har"], "application/json")
        },
    )
    # The response should be successful (200) or a well-formed error (400)
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        # Should be an empty object since the HAR has no entries
        assert isinstance(data["paths"], dict)
    else:
        # If it's a 400 error, make sure it has a proper error message
        data = response.json()
        assert "detail" in data


def test_malformed_input(client, edge_case_inputs):
    """Test API with malformed input (lines 345-348)."""
    # Test with malformed HAR file
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={
            "file": ("test.har", edge_case_inputs["malformed_har"], "application/json")
        },
    )
    # Should return an error
    assert response.status_code != 200


def test_special_characters(client, edge_case_inputs):
    """Test handling of special characters in URLs (lines 275-276, 298-301)."""
    # Test with special characters in URL
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={
            "file": ("test.har", edge_case_inputs["special_chars"], "application/json")
        },
    )
    # The response should be successful (200) or a well-formed error (400)
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        # Check that the path was properly escaped/handled
        paths = data.get("paths", {})
        assert len(paths) > 0
    else:
        # If it's a 400 error, make sure it has a proper error message
        data = response.json()
        assert "detail" in data


def test_duplicate_entries(client, edge_case_inputs):
    """Test handling of duplicate URLs (line 606-610)."""
    # Test HAR with duplicate URLs but different methods
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={
            "file": ("test.har", edge_case_inputs["duplicate_urls"], "application/json")
        },
    )
    # The response should be successful (200) or a well-formed error (400)
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        # Check that both GET and POST methods were captured for the same path
        assert "/api/users" in data["paths"]
        methods = data["paths"]["/api/users"]
        assert "get" in methods
        assert "post" in methods
    else:
        # If it's a 400 error, make sure it has a proper error message
        data = response.json()
        assert "detail" in data


def test_converter_edge_cases(edge_case_inputs):
    """Test converters with edge case inputs (lines 653, 666)."""
    # Use a concrete subclass instead of the abstract FormatConverter
    har_converter = HarToOas3Converter()

    # Test with minimal HAR
    try:
        # Test with empty object to exercise error handling code
        har_converter.convert_from_string(edge_case_inputs["empty_object"])
    except Exception:
        # Expected error - continue with test
        pass

    # Test with minimal HAR
    result = har_converter.convert_from_string(edge_case_inputs["minimal_har"])
    assert "openapi" in result
    assert "paths" in result
    assert isinstance(result["paths"], dict)


def test_content_type_variants(client):
    """Test content type variants (line 330)."""
    # Test various content-type header formats
    har_data = {"log": {"entries": []}}

    # Test with standard content type
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={"file": ("test.har", json.dumps(har_data), "application/json")},
    )
    # The response should be successful (200) or a well-formed error (400)
    assert response.status_code in [200, 400]

    # Test with content type including charset
    response = client.post(
        f"/api/convert/{ConversionFormat.OPENAPI3.value}",
        files={
            "file": (
                "test.har",
                json.dumps(har_data),
                "application/json; charset=utf-8",
            )
        },
    )
    # The response should be successful (200) or a well-formed error (400)
    assert response.status_code in [200, 400]
