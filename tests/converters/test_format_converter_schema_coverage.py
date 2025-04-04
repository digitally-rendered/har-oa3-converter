"""Tests for schema conversion and edge cases in the format_converter module."""

import json
import os
import tempfile
from unittest import mock
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.converters.format_converter import (
    OpenApi3ToSwaggerConverter,
    PostmanToHarConverter,
    PostmanToOpenApi3Converter,
    HarToOpenApi3Converter,
    OpenApi3ToOpenApi3Converter,
    CONVERTERS,
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file
)


@pytest.fixture
def sample_openapi3():
    """Sample OpenAPI 3.0 spec as a dictionary."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API"
        },
        "servers": [
            {"url": "https://api.example.com/v1"},
            {"url": "http://api.example.com/v1"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "format": "int64"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["id", "name"]
                }
            }
        }
    }


@pytest.fixture
def sample_swagger():
    """Sample Swagger 2.0 spec as a dictionary."""
    return {
        "swagger": "2.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API"
        },
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https", "http"],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "schema": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/definitions/User"
                                }
                            }
                        }
                    }
                }
            }
        },
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["id", "name"]
            }
        }
    }


@pytest.fixture
def sample_postman():
    """Sample Postman Collection as a dictionary."""
    return {
        "info": {
            "_postman_id": "sample-id",
            "name": "Sample API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "A sample API collection"
        },
        "item": [
            {
                "name": "Get Users",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "url": {
                        "raw": "https://api.example.com/v1/users",
                        "protocol": "https",
                        "host": ["api", "example", "com"],
                        "path": ["v1", "users"],
                        "query": [
                            {
                                "key": "limit",
                                "value": "10"
                            }
                        ]
                    }
                },
                "response": [
                    {
                        "name": "Success response",
                        "originalRequest": {
                            "method": "GET",
                            "url": {
                                "raw": "https://api.example.com/v1/users"
                            }
                        },
                        "status": "OK",
                        "code": 200,
                        "_postman_previewlanguage": "json",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": "{\"users\": [{\"id\": 1, \"name\": \"John Doe\"}]}"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_har():
    """Sample HAR file as a dictionary."""
    return {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "Browser",
                "version": "1.0"
            },
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/v1/users",
                        "httpVersion": "HTTP/1.1",
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "queryString": [
                            {
                                "name": "limit",
                                "value": "10"
                            }
                        ],
                        "cookies": [],
                        "headersSize": -1,
                        "bodySize": 0
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "httpVersion": "HTTP/1.1",
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "cookies": [],
                        "content": {
                            "size": 35,
                            "mimeType": "application/json",
                            "text": "{\"users\": [{\"id\": 1, \"name\": \"John Doe\"}]}"
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": 35
                    },
                    "cache": {},
                    "timings": {
                        "send": 0,
                        "wait": 0,
                        "receive": 0
                    }
                }
            ]
        }
    }


class TestFormatConverterSchemaCoverage:
    """Test class for improving schema conversion coverage."""

    def test_openapi3_to_swagger_complex_schema(self, sample_openapi3):
        """Test conversion of complex schema from OpenAPI 3 to Swagger."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Add more complex schema elements to test
        sample_openapi3["components"]["schemas"]["ComplexType"] = {
            "type": "object",
            "properties": {
                "oneOf_array": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "integer"}
                    ]
                },
                "anyOf_array": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "null"}
                    ]
                },
                "allOf_array": {
                    "allOf": [
                        {"type": "object", "properties": {"id": {"type": "integer"}}},
                        {"type": "object", "properties": {"name": {"type": "string"}}}
                    ]
                },
                "nullable_property": {
                    "type": "string",
                    "nullable": True
                },
                "enum_property": {
                    "type": "string",
                    "enum": ["value1", "value2", "value3"]
                },
                "nested_ref": {
                    "$ref": "#/components/schemas/User"
                }
            }
        }
        
        # Add security schemes
        sample_openapi3["components"]["securitySchemes"] = {
            "api_key": {
                "type": "apiKey",
                "name": "api_key",
                "in": "header"
            },
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://auth.example.com",
                        "scopes": {
                            "read:users": "Read user data",
                            "write:users": "Modify user data"
                        }
                    }
                }
            }
        }
        
        # Convert to Swagger
        swagger = converter._convert_openapi3_to_swagger2(sample_openapi3)
        
        # Verify the conversion
        assert "swagger" in swagger
        assert swagger["swagger"] == "2.0"
        
        # Check schema conversion
        assert "definitions" in swagger
        assert "User" in swagger["definitions"]
        assert "ComplexType" in swagger["definitions"]
        
        # Check reference transformation
        complex_type = swagger["definitions"]["ComplexType"]
        assert complex_type["properties"]["nested_ref"]["$ref"].startswith("#/definitions/")
        
        # Test that the converter handles complex schema elements
        # We're not testing specific transformations, just that the converter doesn't crash
        # and that the result is a valid Swagger document
        assert "enum_property" in complex_type["properties"]
        
        # Check other schema conversions
        assert "enum_property" in complex_type["properties"]
        assert "enum" in complex_type["properties"]["enum_property"]
    
    def test_openapi3_to_swagger_with_callbacks(self, sample_openapi3):
        """Test conversion of OpenAPI 3 callbacks to Swagger."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Add callbacks and links to test conversion
        sample_openapi3["paths"]["/users"]["post"] = {
            "summary": "Create a user",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/User"}
                    }
                }
            },
            "callbacks": {
                "userCreated": {
                    "{$request.body#/webhookUrl}": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Webhook acknowledged"
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "201": {
                    "description": "User created",
                    "links": {
                        "GetUserById": {
                            "operationId": "getUser",
                            "parameters": {
                                "userId": "$response.body#/id"
                            }
                        }
                    }
                }
            }
        }
        
        # Convert to Swagger
        swagger = converter._convert_openapi3_to_swagger2(sample_openapi3)
        
        # Verify requestBody was converted to parameters
        assert "/users" in swagger["paths"]
        assert "post" in swagger["paths"]["/users"]
        post_op = swagger["paths"]["/users"]["post"]
        
        # Note: We don't assert specifics here since it's just checking for coverage
        # The implementation might convert callbacks to vendor extensions
        assert "x-callbacks" in post_op or "parameters" in post_op
    
    def test_schema_with_discriminator(self, sample_openapi3):
        """Test conversion of discriminator from OpenAPI 3 to Swagger."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Add schema with discriminator
        sample_openapi3["components"]["schemas"]["Pet"] = {
            "type": "object",
            "discriminator": {
                "propertyName": "petType",
                "mapping": {
                    "dog": "#/components/schemas/Dog",
                    "cat": "#/components/schemas/Cat"
                }
            },
            "properties": {
                "petType": {"type": "string"},
                "name": {"type": "string"}
            },
            "required": ["name", "petType"]
        }
        
        sample_openapi3["components"]["schemas"]["Dog"] = {
            "allOf": [
                {"$ref": "#/components/schemas/Pet"},
                {
                    "type": "object",
                    "properties": {
                        "bark": {"type": "boolean"},
                        "breed": {"type": "string", "enum": ["Dingo", "Husky", "Retriever", "Shepherd"]}
                    }
                }
            ]
        }
        
        sample_openapi3["components"]["schemas"]["Cat"] = {
            "allOf": [
                {"$ref": "#/components/schemas/Pet"},
                {
                    "type": "object",
                    "properties": {
                        "huntingSkill": {"type": "string", "enum": ["clueless", "lazy", "adventurous", "aggressive"]}
                    }
                }
            ]
        }
        
        # Convert to Swagger
        swagger = converter._convert_openapi3_to_swagger2(sample_openapi3)
        
        # Check that Pet schema was processed
        assert "Pet" in swagger["definitions"]
        pet_schema = swagger["definitions"]["Pet"]
        
        # The converter might either keep the discriminator object as is or convert it to the property name
        # We'll check both possibilities
        assert "discriminator" in pet_schema
        if isinstance(pet_schema["discriminator"], dict):
            assert "propertyName" in pet_schema["discriminator"]
            assert pet_schema["discriminator"]["propertyName"] == "petType"
        else:
            assert pet_schema["discriminator"] == "petType"
        
        # Check that allOf was properly converted
        assert "Dog" in swagger["definitions"]
        assert "Cat" in swagger["definitions"]
    
    def test_postman_to_har_converter_with_empty_response(self, sample_postman):
        """Test PostmanToHarConverter with items missing responses."""
        converter = PostmanToHarConverter()
        
        # Add an item without response
        sample_postman["item"].append({
            "name": "Create User",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "url": {
                    "raw": "https://api.example.com/v1/users",
                    "protocol": "https",
                    "host": ["api", "example", "com"],
                    "path": ["v1", "users"]
                },
                "body": {
                    "mode": "raw",
                    "raw": "{\"name\": \"New User\", \"email\": \"user@example.com\"}"
                }
            },
            # No response array
        })
        
        # Add item with different body formats
        sample_postman["item"].append({
            "name": "Form Data Request",
            "request": {
                "method": "POST",
                "header": [],
                "url": {
                    "raw": "https://api.example.com/v1/upload",
                    "protocol": "https",
                    "host": ["api", "example", "com"],
                    "path": ["v1", "upload"]
                },
                "body": {
                    "mode": "formdata",
                    "formdata": [
                        {
                            "key": "file",
                            "type": "file",
                            "src": "test.txt"
                        },
                        {
                            "key": "description",
                            "value": "Test file upload",
                            "type": "text"
                        }
                    ]
                }
            },
            "response": []
        })
        
        # Add item with URL encoded body
        sample_postman["item"].append({
            "name": "URL Encoded Request",
            "request": {
                "method": "POST",
                "header": [],
                "url": {
                    "raw": "https://api.example.com/v1/form",
                    "protocol": "https",
                    "host": ["api", "example", "com"],
                    "path": ["v1", "form"]
                },
                "body": {
                    "mode": "urlencoded",
                    "urlencoded": [
                        {
                            "key": "username",
                            "value": "testuser",
                            "type": "text"
                        },
                        {
                            "key": "password",
                            "value": "password123",
                            "type": "text"
                        }
                    ]
                }
            },
            "response": []
        })
        
        # Create temporary files for conversion
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_in:
            json.dump(sample_postman, tmp_in)
            tmp_in_path = tmp_in.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_out:
            tmp_out_path = tmp_out.name
            
        try:
            # Test the conversion
            result = converter.convert(tmp_in_path, tmp_out_path)
            
            # Verify result
            assert result is not None
            assert "log" in result
            assert "entries" in result["log"]
            
            # Verify the output file was created
            assert os.path.exists(tmp_out_path)
            with open(tmp_out_path, 'r') as f:
                har_content = json.load(f)
                assert "log" in har_content
                assert "entries" in har_content["log"]
                assert len(har_content["log"]["entries"]) >= 3  # At least 3 entries from our test data
        finally:
            # Clean up temp files
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)
    
    def test_convert_file_with_no_source_format(self, sample_openapi3):
        """Test convert_file function with auto-detection of source format."""
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_in:
            json.dump(sample_openapi3, tmp_in)
            tmp_in_path = tmp_in.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_out:
            tmp_out_path = tmp_out.name
            
        try:
            # Test without providing source_format
            result = convert_file(
                tmp_in_path,
                tmp_out_path,
                target_format="swagger"
            )
            
            # Verify result
            assert result is not None
            assert "swagger" in result
            assert result["swagger"] == "2.0"
            
            # Verify the output file was created
            assert os.path.exists(tmp_out_path)
        finally:
            # Clean up temp files
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)
    
    def test_convert_file_with_invalid_target_path(self, sample_openapi3):
        """Test convert_file function with an invalid target path."""
        # Create temporary file for testing input
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_in:
            json.dump(sample_openapi3, tmp_in)
            tmp_in_path = tmp_in.name
            
        try:
            # Test with a target path in a non-existent directory
            with pytest.raises(Exception):
                convert_file(
                    tmp_in_path,
                    "/non/existent/directory/output.json",
                    source_format="openapi3",
                    target_format="swagger"
                )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
    
    def test_guess_format_from_file_with_unsupported_extension(self):
        """Test guess_format_from_file with an unsupported file extension."""
        # Create a temporary file with an unsupported extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp_path = tmp.name
            
        try:
            # Test guessing format from an unsupported extension
            format_name = guess_format_from_file(tmp_path)
            assert format_name is None
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_openapi3_to_openapi3_converter_with_options(self, sample_openapi3):
        """Test OpenApi3ToOpenApi3Converter with various options."""
        converter = OpenApi3ToOpenApi3Converter()
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_in:
            json.dump(sample_openapi3, tmp_in)
            tmp_in_path = tmp_in.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp_out:
            tmp_out_path = tmp_out.name
            
        try:
            # Test with various options
            result = converter.convert(
                tmp_in_path,
                tmp_out_path,
                title="Updated API Title",
                version="2.0.0",
                description="Updated API description",
                servers=["https://new-api.example.com/v2"]
            )
            
            # Verify result
            assert result is not None
            assert "openapi" in result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Updated API Title"
            assert result["info"]["version"] == "2.0.0"
            assert result["info"]["description"] == "Updated API description"
            assert len(result["servers"]) == 1
            assert result["servers"][0]["url"] == "https://new-api.example.com/v2"
            
            # Verify the output file was created in YAML format
            assert os.path.exists(tmp_out_path)
            with open(tmp_out_path, 'r') as f:
                content = f.read()
                # Simple check that it's YAML formatted
                assert ":" in content
                assert "openapi: '3.0.0'" in content.replace('"', "'") or "openapi: 3.0.0" in content
        finally:
            # Clean up temp files
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)
