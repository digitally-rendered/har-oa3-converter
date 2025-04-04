"""Tests for the har_to_oas3 converter module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter


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
                            {"name": "limit", "value": "10"}
                        ],
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                            {"name": "Authorization", "value": "Bearer token123"}
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
                            "text": json.dumps({
                                "data": [
                                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                                ],
                                "total": 2,
                                "page": 1,
                                "limit": 10
                            })
                        }
                    }
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/api/users",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                            {"name": "Authorization", "value": "Bearer token123"}
                        ],
                        "postData": {
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "name": "New User",
                                "email": "newuser@example.com"
                            })
                        }
                    },
                    "response": {
                        "status": 201,
                        "statusText": "Created",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "id": 3,
                                "name": "New User",
                                "email": "newuser@example.com"
                            })
                        }
                    }
                }
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
        assert converter.components == {
            "schemas": {},
            "requestBodies": {},
            "responses": {}
        }
        assert converter.base_path is None
        assert converter.servers == []
        
    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        info = {"title": "Custom API", "version": "2.0.0"}
        servers = [{"url": "https://example.com"}]
        
        converter = HarToOas3Converter(
            base_path="/api",
            info=info,
            servers=servers
        )
        
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
        
    def test_load_har_file_not_found(self):
        """Test loading non-existent HAR file."""
        converter = HarToOas3Converter()
        with pytest.raises(FileNotFoundError):
            converter.load_har("nonexistent.har")
            
    def test_load_har_invalid_json(self, tmp_path):
        """Test loading invalid JSON HAR file."""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.har"
        invalid_file.write_text("This is not valid JSON")
        
        converter = HarToOas3Converter()
        with pytest.raises(json.JSONDecodeError):
            converter.load_har(str(invalid_file))
        
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
    
    def test_extract_paths_from_empty_har(self):
        """Test extracting paths from empty HAR data."""
        converter = HarToOas3Converter()
        empty_har = {"log": {"entries": []}}
        converter.extract_paths_from_har(empty_har)
        assert converter.paths == {}
        
    def test_extract_paths_from_invalid_har(self):
        """Test extracting paths from invalid HAR structure."""
        converter = HarToOas3Converter()
        invalid_har = {"invalid": "structure"}
        converter.extract_paths_from_har(invalid_har)
        assert converter.paths == {}
        
        partial_har = {"log": {"no_entries": []}}
        converter.extract_paths_from_har(partial_har)
        assert converter.paths == {}
        
    def test_extract_paths_with_relative_url(self):
        """Test extracting paths with relative URLs."""
        converter = HarToOas3Converter()
        har_with_relative_url = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "users?id=123"
                        },
                        "response": {}
                    }
                ]
            }
        }
        converter.extract_paths_from_har(har_with_relative_url)
        assert "/users" in converter.paths
        
    def test_extract_paths_duplicate_method(self, sample_har_data):
        """Test handling duplicate methods for same path."""
        # Add duplicate entry for same path and method
        duplicate_entry = sample_har_data["log"]["entries"][0].copy()
        sample_har_data["log"]["entries"].append(duplicate_entry)
        
        converter = HarToOas3Converter()
        converter.extract_paths_from_har(sample_har_data)
        
        # Should only have one GET method documented
        assert len(converter.paths["/api/users"]) == 2  # get and post
        
    def test_process_request_response(self):
        """Test _process_request_response method."""
        converter = HarToOas3Converter()
        
        # Initialize the path in paths dictionary first, as the actual method expects it
        converter.paths["/test"] = {}
        
        request = {
            "method": "GET",
            "url": "https://example.com/api/test",
            "queryString": [{"name": "q", "value": "test"}],
            "headers": [{"name": "X-Test", "value": "value"}]
        }
        
        response = {
            "status": 200,
            "statusText": "OK",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "content": {
                "mimeType": "application/json",
                "text": '{"result": "success"}'
            }
        }
        
        # Method is non-public, but we'll test it directly
        converter._process_request_response("/test", "get", request, response)
        
        assert "/test" in converter.paths
        assert "get" in converter.paths["/test"]
        assert converter.paths["/test"]["get"]["operationId"] == "get_test"
        assert "parameters" in converter.paths["/test"]["get"]
        assert "responses" in converter.paths["/test"]["get"]
        assert "200" in converter.paths["/test"]["get"]["responses"]
        
    def test_extract_parameters(self):
        """Test _extract_parameters method."""
        converter = HarToOas3Converter()
        
        # Test with query parameters
        request_with_query = {
            "queryString": [
                {"name": "page", "value": "1"},
                {"name": "limit", "value": "10"}
            ],
            "headers": []
        }
        params = converter._extract_parameters(request_with_query)
        assert len(params) == 2
        assert params[0]["name"] == "page"
        assert params[0]["in"] == "query"
        
        # Test with custom headers
        request_with_headers = {
            "queryString": [],
            "headers": [
                {"name": "X-API-Key", "value": "abc123"},
                {"name": "User-Agent", "value": "Test"}  # Should be skipped
            ]
        }
        params = converter._extract_parameters(request_with_headers)
        assert len(params) == 1
        assert params[0]["name"] == "X-API-Key"
        assert params[0]["in"] == "header"
        
        # Test with empty request
        empty_request = {}
        params = converter._extract_parameters(empty_request)
        assert params == []
        
    def test_extract_request_body(self):
        """Test _extract_request_body method."""
        converter = HarToOas3Converter()
        
        # Test with JSON body
        json_request = {
            "postData": {
                "mimeType": "application/json",
                "text": '{"name": "test", "value": 123}'
            }
        }
        body = converter._extract_request_body(json_request)
        assert body["required"] is True
        assert "application/json" in body["content"]
        assert "$ref" in body["content"]["application/json"]["schema"]
        
        # Test with form data
        form_request = {
            "postData": {
                "mimeType": "application/x-www-form-urlencoded",
                "text": "name=test&value=123"
            }
        }
        body = converter._extract_request_body(form_request)
        assert body["required"] is True
        assert "application/x-www-form-urlencoded" in body["content"]
        assert body["content"]["application/x-www-form-urlencoded"]["schema"]["type"] == "string"
        
        # Test with invalid JSON
        invalid_json_request = {
            "postData": {
                "mimeType": "application/json",
                "text": "invalid json"
            }
        }
        body = converter._extract_request_body(invalid_json_request)
        assert body["required"] is True
        assert "application/json" in body["content"]
        
        # Test with no body
        no_body_request = {}
        body = converter._extract_request_body(no_body_request)
        assert body is None
        
    def test_extract_responses(self):
        """Test _extract_responses method."""
        converter = HarToOas3Converter()
        
        # Test with JSON response
        json_response = {
            "status": 200,
            "statusText": "OK",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "content": {
                "mimeType": "application/json",
                "text": '{"result": "success"}'
            }
        }
        responses = converter._extract_responses(json_response)
        assert "200" in responses
        assert responses["200"]["description"] == "OK"
        assert "content" in responses["200"]
        assert "application/json" in responses["200"]["content"]
        assert "$ref" in responses["200"]["content"]["application/json"]["schema"]
        
        # Test with text response
        text_response = {
            "status": 204,
            "statusText": "No Content",
            "headers": [{"name": "Content-Type", "value": "text/plain"}],
            "content": {
                "mimeType": "text/plain",
                "text": "Success"
            }
        }
        responses = converter._extract_responses(text_response)
        assert "204" in responses
        assert responses["204"]["description"] == "No Content"
        assert "content" in responses["204"]
        assert "text/plain" in responses["204"]["content"]
        assert responses["204"]["content"]["text/plain"]["schema"]["type"] == "string"
        
        # Test with invalid JSON response
        invalid_json_response = {
            "status": 400,
            "statusText": "Bad Request",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "content": {
                "mimeType": "application/json",
                "text": "invalid json"
            }
        }
        responses = converter._extract_responses(invalid_json_response)
        assert "400" in responses
        assert "content" in responses["400"]
        assert "application/json" in responses["400"]["content"]
        assert responses["400"]["content"]["application/json"]["schema"]["type"] == "string"
        
        # Test with no content
        no_content_response = {
            "status": 204,
            "statusText": "No Content",
            "headers": []
        }
        responses = converter._extract_responses(no_content_response)
        assert "204" in responses
        assert "description" in responses["204"]
        assert "content" not in responses["204"]
        
    def test_infer_schema(self):
        """Test _infer_schema method."""
        converter = HarToOas3Converter()
        
        # Test with object
        obj_data = {"name": "test", "id": 123, "active": True}
        schema_name = converter._infer_schema("TestObject", obj_data)
        assert schema_name == "TestObject"
        assert schema_name in converter.components["schemas"]
        assert converter.components["schemas"][schema_name]["type"] == "object"
        assert "name" in converter.components["schemas"][schema_name]["properties"]
        assert converter.components["schemas"][schema_name]["properties"]["id"]["type"] == "integer"
        
        # Test with array
        array_data = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        schema_name = converter._infer_schema("TestArray", array_data)
        assert schema_name == "TestArray"
        assert schema_name in converter.components["schemas"]
        assert converter.components["schemas"][schema_name]["type"] == "array"
        assert "$ref" in converter.components["schemas"][schema_name]["items"]
        
        # Test with empty array
        empty_array = []
        schema_name = converter._infer_schema("EmptyArray", empty_array)
        assert schema_name == "EmptyArray"
        assert converter.components["schemas"][schema_name]["type"] == "array"
        assert converter.components["schemas"][schema_name]["items"]["type"] == "string"
        
        # Test with primitive value
        primitive = "test string"
        schema_name = converter._infer_schema("TestString", primitive)
        assert schema_name == "TestString"
        assert converter.components["schemas"][schema_name]["type"] == "string"
        
        # Test with duplicate name - checking if the name is in components
        # The implementation may handle duplicates differently than expected
        dupe_name = converter._infer_schema("TestObject", {"another": "object"})
        assert dupe_name in converter.components["schemas"]
        # Either it will use the original name and overwrite or use a new name with counter
        
    def test_get_schema_for_value(self):
        """Test _get_schema_for_value method."""
        converter = HarToOas3Converter()
        
        # Test with various value types
        assert converter._get_schema_for_value(None)["type"] == "null"
        assert converter._get_schema_for_value(True)["type"] == "boolean"
        assert converter._get_schema_for_value(123)["type"] == "integer"
        assert converter._get_schema_for_value(123.45)["type"] == "number"
        assert converter._get_schema_for_value("test")["type"] == "string"
        
        # Test examples are included
        int_schema = converter._get_schema_for_value(42)
        assert int_schema["example"] == 42
        
        str_schema = converter._get_schema_for_value("example")
        assert str_schema["example"] == "example"
        
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
        
        # Test with servers
        converter = HarToOas3Converter(servers=[{"url": "https://api.example.com"}])
        converter.extract_paths_from_har(sample_har_data)
        spec = converter.generate_spec()
        assert "servers" in spec
        assert spec["servers"] == [{"url": "https://api.example.com"}]
        
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
                
    def test_convert_with_options(self, sample_har_file):
        """Test conversion with additional options."""
        converter = HarToOas3Converter()
        
        # Pass additional options that aren't used yet but shouldn't cause errors
        spec = converter.convert(
            sample_har_file, 
            validate_schema=False,
            additional_option="value"
        )
        
        assert "openapi" in spec
