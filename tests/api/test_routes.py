"""Tests for the API module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
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
                        "queryString": [
                            {"name": "page", "value": "1"}
                        ],
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
    
    # Cleanup
    os.unlink(file_path)


class TestApiRoutes:
    """Test class for API routes."""
    
    def test_list_formats(self, client):
        """Test the /api/formats endpoint."""
        response = client.get("/api/formats")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert "har" in response.json()
        assert "openapi3" in response.json()
        assert "swagger" in response.json()
    
    def test_convert_har_to_openapi3(self, client, sample_har_file):
        """Test converting HAR to OpenAPI 3."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        response = client.post(
            "/api/convert/openapi3",
            files={"file": ("test.har", file_content, "application/json")},
            data={
                "title": "Test API",
                "version": "1.0.0",
                "description": "Test description",
                "servers": ["https://api.example.com"],
                "base_path": "/api",
                "skip_validation": "false"
            },
            headers={"Accept": "application/json"}
        )
        
        # Print the error message if the test fails
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "openapi" in data
        assert data["openapi"] == "3.0.0"
        assert "info" in data
        assert data["info"]["title"] == "Test API"
        assert "paths" in data
        assert "/api/users" in data["paths"]
    
    def test_convert_har_to_swagger(self, client, sample_har_file):
        """Test converting HAR to Swagger 2."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        # First convert to OpenAPI 3
        openapi_response = client.post(
            "/api/convert/openapi3",
            files={"file": ("test.har", file_content, "application/json")},
            headers={"Accept": "application/json"}
        )
        
        assert openapi_response.status_code == 200
        openapi_content = openapi_response.json()
        
        # Create temporary OpenAPI 3 file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(json.dumps(openapi_content).encode("utf-8"))
            openapi_file = f.name
        
        try:
            # Now convert OpenAPI 3 to Swagger
            with open(openapi_file, "rb") as f:
                openapi_content = f.read()
                
            swagger_response = client.post(
                "/api/convert/swagger",
                files={"file": ("test.json", openapi_content, "application/json")},
                headers={"Accept": "application/json"}
            )
            
            # Print the error message if the test fails
            if swagger_response.status_code != 200:
                print(f"Swagger conversion error: {swagger_response.text}")
                
            assert swagger_response.status_code == 200
            assert swagger_response.headers["content-type"] == "application/json"
            
            data = swagger_response.json()
            assert "swagger" in data
            assert data["swagger"] == "2.0"
            assert "info" in data
            assert "paths" in data
            assert "/api/users" in data["paths"]
        finally:
            # Cleanup
            os.unlink(openapi_file)
    
    def test_convert_with_yaml_response(self, client, sample_har_file):
        """Test converting with YAML response."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        response = client.post(
            "/api/convert/openapi3",
            files={"file": ("test.har", file_content, "application/json")},
            headers={"Accept": "application/yaml"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/yaml"
        
        # Check that response is valid YAML
        data = yaml.safe_load(response.content)
        assert "openapi" in data
        assert data["openapi"] == "3.0.0"
        assert "paths" in data
        assert "/api/users" in data["paths"]
    
    def test_convert_with_accept_query_param(self, client, sample_har_file):
        """Test converting with accept as query parameter."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        response = client.post(
            "/api/convert/openapi3?accept=application/yaml",
            files={"file": ("test.har", file_content, "application/json")},
            # No Accept header, using query param instead
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/yaml"
        
        # Check that response is valid YAML
        data = yaml.safe_load(response.content)
        assert "openapi" in data
    
    def test_convert_with_source_format_override(self, client, sample_har_file):
        """Test converting with explicit source format."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        response = client.post(
            "/api/convert/openapi3?source_format=har",
            files={"file": ("test.json", file_content, "application/json")},
            # Note we're not using .har extension, but explicitly telling it's HAR format
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
    
    def test_convert_error_invalid_file(self, client):
        """Test error response with invalid file."""
        response = client.post(
            "/api/convert/openapi3",
            files={"file": ("test.txt", b"invalid content", "text/plain")},
        )
        
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Conversion failed" in response.json()["detail"]
    
    def test_convert_error_no_file(self, client):
        """Test error response when no file is provided."""
        response = client.post("/api/convert/openapi3")
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_convert_error_invalid_target_format(self, client, sample_har_file):
        """Test error response with invalid target format."""
        # This should fail because the path parameter will be rejected
        response = client.post("/api/convert/invalid_format")
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_convert_error_invalid_source_format(self, client):
        """Test error response with invalid source format."""
        # Create an empty JSON file that will be detected as an invalid format
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(b"{}")
            file_path = f.name
            
        try:
            with open(file_path, "rb") as f:
                response = client.post(
                    "/api/convert/openapi3",
                    files={"file": ("empty.json", f.read(), "application/json")},
                )
                
            assert response.status_code == 400
            assert "detail" in response.json()
            assert "Conversion failed" in response.json()["detail"]
        finally:
            os.unlink(file_path)
    
    def test_convert_with_skip_validation(self, client, sample_har_file):
        """Test conversion with skip_validation option."""
        with open(sample_har_file, "rb") as f:
            file_content = f.read()
            
        response = client.post(
            "/api/convert/openapi3",
            files={"file": ("test.har", file_content, "application/json")},
            data={"skip_validation": "true"},
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
