"""Fixed Schemathesis tests for API schema validation."""

import json
import tempfile
import os

import pytest
import schemathesis
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app, custom_openapi
from har_oa3_converter.api.models import ConversionFormat

# Import our manually crafted schema that's compatible with Schemathesis
from tests.api.schemathesis_schema import SCHEMA

# Create a TestClient
@pytest.fixture(scope="module")
def client():
    return TestClient(app)

# Create test HAR file for manual testing
@pytest.fixture(scope="module")
def sample_har_file():
    """Create a sample HAR file for testing."""
    sample_data = {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "Browser DevTools",
                "version": "1.0"
            },
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ]
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps({"data": [{"id": 1, "name": "Test User"}]})
                        }
                    }
                }
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name
    
    yield file_path
    os.unlink(file_path)


# Create Schemathesis schema for API testing
# We use our custom schema that's compatible with Schemathesis (OpenAPI 3.0.3)
schema = schemathesis.from_dict(SCHEMA, base_url="http://testserver")


# Test the GET /api/formats endpoint using Schemathesis
@schema.parametrize()
def test_api_formats_endpoint(case):
    """Test that the formats endpoint conforms to our schema."""
    # Only test the GET /api/formats endpoint
    if case.path != "/api/formats" or case.method.lower() != "get":
        pytest.skip("This test only applies to GET /api/formats")
        
    # Make the request to our app
    response = case.call_asgi(app)
    
    # Check response status and content
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "openapi3" in data  # Verify expected format is available
    assert "har" in data       # Verify expected format is available
    
    # Let Schemathesis validate that the response matches our schema
    case.validate_response(response)


# Test the conversion endpoint manually (not using Schemathesis parametrize
# because file upload testing is complex with Schemathesis)
def test_api_convert_endpoint(client, sample_har_file):
    """Test the conversion endpoint using standard pytest."""
    target_format = ConversionFormat.OPENAPI3.value
    
    with open(sample_har_file, "rb") as f:
        files = {"file": ("test.har", f, "application/json")}
        data = {"title": "Test API", "version": "1.0.0"}
        
        response = client.post(
            f"/api/convert/{target_format}",
            files=files,
            data=data
        )
    
    assert response.status_code == 200
    result = response.json()
    
    # Validate the response structure conforms to OpenAPI 3
    assert "openapi" in result
    assert result["openapi"].startswith("3.")  # Should be OpenAPI 3.x
    assert "info" in result
    assert result["info"]["title"] == "Test API"  # Title should match what we sent
    assert "paths" in result  # Should have paths


# Test Accept header content negotiation
def test_api_accept_header_handling(client, sample_har_file):
    """Test that the API handles Accept headers properly for content negotiation."""
    target_format = ConversionFormat.OPENAPI3.value
    
    # Test different Accept headers
    formats_to_test = [
        ("application/json", "application/json"),
        ("application/yaml", "application/yaml")
    ]
    
    for accept_header, expected_content_type in formats_to_test:
        with open(sample_har_file, "rb") as f:
            files = {"file": ("test.har", f, "application/json")}
            headers = {"Accept": accept_header}
            
            response = client.post(
                f"/api/convert/{target_format}",
                files=files,
                headers=headers,
                data={"title": "Test API"}
            )
        
        assert response.status_code == 200
        
        # Check that the correct content type was returned based on Accept header
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        assert content_type == expected_content_type.lower(), f"Expected {expected_content_type}, got {content_type}"


# Test custom options
def test_api_custom_options(client, sample_har_file):
    """Test that custom options are properly applied during conversion."""
    target_format = ConversionFormat.OPENAPI3.value
    custom_title = "Custom API Title"
    custom_version = "2.0.0"
    custom_description = "This is a custom API description"
    
    with open(sample_har_file, "rb") as f:
        files = {"file": ("test.har", f, "application/json")}
        data = {
            "title": custom_title,
            "version": custom_version,
            "description": custom_description,
            "servers": "https://api.example.com"
        }
        
        response = client.post(
            f"/api/convert/{target_format}",
            files=files,
            data=data
        )
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify custom options were applied
    assert result["info"]["title"] == custom_title
    assert result["info"]["version"] == custom_version
    assert result["info"]["description"] == custom_description
