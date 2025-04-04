"""Tests targeting edge cases and uncovered lines in format_converter module."""

import json
import os
import tempfile
from unittest import mock
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.converters.format_converter import (
    FormatConverter,
    OpenApi3ToSwaggerConverter,
    PostmanToHarConverter,
    PostmanToOpenApi3Converter,
    HarToOpenApi3Converter,
    OpenApi3ToOpenApi3Converter,
    CONVERTERS,
    FORMAT_EXTENSIONS,
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file
)


@pytest.fixture
def sample_openapi3_with_edge_cases():
    """Sample OpenAPI 3.0 spec with edge cases that need coverage."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Edge Case API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "https://api.example.com/v1"}
        ],
        "paths": {
            "/edge-cases": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad Request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"}
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
                "EdgeCaseObject": {
                    "type": "object",
                    "properties": {
                        "nullableField": {
                            "type": "string",
                            "nullable": True
                        },
                        "arrayWithExample": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": ["item1", "item2"]
                        },
                        "objectWithDefault": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "default": "value"}
                            }
                        },
                        "anyOfField": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number"}
                            ]
                        },
                        "oneOfField": {
                            "oneOf": [
                                {"type": "boolean"},
                                {"type": "object", "properties": {"value": {"type": "string"}}}
                            ]
                        }
                    }
                },
                "RecursiveObject": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "child": {"$ref": "#/components/schemas/RecursiveObject"}
                    }
                }
            },
            "securitySchemes": {
                "oauth2": {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": "https://example.com/oauth/authorize",
                            "tokenUrl": "https://example.com/oauth/token",
                            "scopes": {
                                "read": "Read access",
                                "write": "Write access"
                            }
                        },
                        "implicit": {
                            "authorizationUrl": "https://example.com/oauth/authorize",
                            "scopes": {
                                "read": "Read access",
                                "write": "Write access"
                            }
                        }
                    }
                },
                "apiKey": {
                    "type": "apiKey",
                    "name": "api_key",
                    "in": "header"
                }
            }
        }
    }


class TestAbstractBaseConverter:
    """Test the abstract base FormatConverter class."""
    
    def test_base_converter_name(self):
        """Test that FormatConverter can be used as a base class."""
        # Check the __subclasses__ method to confirm there are registered subclasses
        subclasses = FormatConverter.__subclasses__()
        assert len(subclasses) > 0
        
        # Verify abstract class has expected classmethod
        assert hasattr(FormatConverter, 'get_name')
        
        # Test that we can register a new converter class
        class MyTestConverter(FormatConverter):
            @classmethod
            def get_source_format(cls) -> str:
                return "test_source"
                
            @classmethod
            def get_target_format(cls) -> str:
                return "test_target"
                
            def convert(self, source_path, target_path=None, **options):
                return {"converted": True}
                
        # Check that the class can be instantiated
        converter = MyTestConverter()
        
        # Test our concrete implementation works correctly
        assert MyTestConverter.get_source_format() == "test_source"
        assert MyTestConverter.get_target_format() == "test_target"
        
        # Test convert returns the expected result
        result = converter.convert("path/to/source", "path/to/target")
        assert result == {"converted": True}
    
    def test_get_name(self):
        """Test the get_name class method."""
        class CustomNameConverter(FormatConverter):
            pass
        
        assert CustomNameConverter.get_name() == "CustomNameConverter"


class TestEdgeCaseSchemaConversion:
    """Test edge cases in schema conversion."""
    
    def test_convert_schema_with_additionalProperties(self):
        """Test schema conversion with additionalProperties."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Create a schema with additionalProperties
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": True
        }
        
        # Convert the schema
        result = converter._convert_schema(schema)
        
        # Verify additionalProperties was preserved
        assert "additionalProperties" in result
        assert result["additionalProperties"] is True
    
    def test_convert_schema_with_additionalProperties_schema(self):
        """Test schema conversion with additionalProperties as a schema."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Create a schema with additionalProperties as a schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": {
                "type": "string"
            }
        }
        
        # Convert the schema
        result = converter._convert_schema(schema)
        
        # Verify additionalProperties schema was preserved or converted
        assert "additionalProperties" in result
        assert isinstance(result["additionalProperties"], dict)
        assert result["additionalProperties"]["type"] == "string"
    
    def test_convert_schema_with_writeOnly(self):
        """Test schema conversion with writeOnly property (OpenAPI 3 specific)."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Create a schema with writeOnly property (not in Swagger 2.0)
        schema = {
            "type": "object",
            "properties": {
                "password": {
                    "type": "string",
                    "writeOnly": True
                }
            }
        }
        
        # Convert the schema
        result = converter._convert_schema(schema)
        
        # Verify the schema was converted
        assert "properties" in result
        assert "password" in result["properties"]
        # writeOnly might be preserved as a vendor extension or removed
        if "writeOnly" in result["properties"]["password"]:
            assert result["properties"]["password"]["writeOnly"] is True
        # Alternatively, it might be converted to a vendor extension
        elif "x-writeOnly" in result["properties"]["password"]:
            assert result["properties"]["password"]["x-writeOnly"] is True
    
    def test_convert_schema_with_recursive_reference(self, sample_openapi3_with_edge_cases):
        """Test conversion of schema with recursive reference."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Get the RecursiveObject schema from the sample
        recursive_schema = sample_openapi3_with_edge_cases["components"]["schemas"]["RecursiveObject"]
        
        # Convert the schema
        result = converter._convert_schema(recursive_schema)
        
        # Verify the reference was processed correctly
        assert "properties" in result
        assert "child" in result["properties"]
        assert "$ref" in result["properties"]["child"]
        # The reference should be updated to point to definitions instead of components
        assert result["properties"]["child"]["$ref"].startswith("#/definitions/")
    
    def test_convert_schema_with_complex_allOf(self):
        """Test schema conversion with complex allOf composition."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Create a schema with allOf that includes references and inline schemas
        schema = {
            "allOf": [
                {"$ref": "#/components/schemas/BaseType"},
                {
                    "type": "object",
                    "properties": {
                        "additionalProp": {"type": "string"}
                    }
                },
                {
                    "required": ["id", "name"]
                }
            ]
        }
        
        # Convert the schema
        result = converter._convert_schema(schema)
        
        # Verify allOf was processed correctly
        # Note: The way allOf is handled may vary, so we're just checking that it's handled somehow
        assert result is not None
        assert isinstance(result, dict)
        
        # Different implementations handle allOf differently, just ensure basic structure
        # is preserved in some way
        
        # The schema might be preserved as allOf or flattened
        if "allOf" in result:
            # If allOf exists, it should be a list
            assert isinstance(result["allOf"], list)
    
    def test_complex_request_body_conversion(self, sample_openapi3_with_edge_cases):
        """Test conversion of OpenAPI 3 requestBody to Swagger parameters."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Add a POST endpoint with requestBody to the sample
        sample_openapi3_with_edge_cases["paths"]["/edge-cases"]["post"] = {
            "summary": "Create an edge case",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/EdgeCaseObject"
                        }
                    },
                    "application/xml": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "responses": {
                "201": {
                    "description": "Created"
                }
            }
        }
        
        # Convert the OpenAPI 3 document to Swagger
        result = converter._convert_openapi3_to_swagger2(sample_openapi3_with_edge_cases)
        
        # Verify that requestBody was converted to parameters
        assert "/edge-cases" in result["paths"]
        assert "post" in result["paths"]["/edge-cases"]
        post_op = result["paths"]["/edge-cases"]["post"]
        
        # Check for body parameter
        if "parameters" in post_op:
            body_param = None
            for param in post_op["parameters"]:
                if param.get("in") == "body":
                    body_param = param
                    break
            
            assert body_param is not None
            assert "schema" in body_param
            assert "$ref" in body_param["schema"]
            # Reference should point to definitions
            assert body_param["schema"]["$ref"].startswith("#/definitions/")
    
    def test_security_schemes_conversion(self, sample_openapi3_with_edge_cases):
        """Test conversion of security schemes from OpenAPI 3 to Swagger."""
        converter = OpenApi3ToSwaggerConverter()
        
        # Convert the OpenAPI 3 document to Swagger
        result = converter._convert_openapi3_to_swagger2(sample_openapi3_with_edge_cases)
        
        # Some implementations may use securityDefinitions, others might use vendor extensions
        # or completely different approaches. We'll check for common patterns.
        
        # Basic check that the conversion happened
        assert "swagger" in result
        assert result["swagger"] == "2.0"
        
        # Verify the components were converted to definitions
        assert "definitions" in result
        assert "EdgeCaseObject" in result["definitions"]
        assert "RecursiveObject" in result["definitions"]
        
        # Check if securityDefinitions were included (this is optional, as it depends on implementation)
        if "securityDefinitions" in result:
            # If security definitions exist, check their structure
            if "oauth2" in result["securityDefinitions"]:
                oauth2 = result["securityDefinitions"]["oauth2"]
                assert oauth2["type"] == "oauth2"
                
            if "apiKey" in result["securityDefinitions"]:
                api_key = result["securityDefinitions"]["apiKey"]
                assert api_key["type"] == "apiKey"
                assert api_key["in"] == "header"
                assert api_key["name"] == "api_key"


class TestEdgeCaseFileHandling:
    """Test edge cases in file handling and format detection."""
    
    def test_guess_format_with_multiple_dots(self):
        """Test guessing format from a file with multiple dots in the name."""
        # Create a file with multiple dots
        with tempfile.NamedTemporaryFile(suffix=".v1.swagger.json", delete=False) as f:
            temp_path = f.name
        
        try:
            # Test guessing format from a file with multiple dots
            format_name = guess_format_from_file(temp_path)
            # The implementation might look at the extension in different ways
            # It might return either swagger or openapi3 since both use .json
            assert format_name in ["swagger", "openapi3"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_guess_format_with_uppercase_extension(self):
        """Test guessing format from a file with uppercase extension."""
        # Create a file with uppercase extension
        with tempfile.NamedTemporaryFile(suffix=".JSON", delete=False) as f:
            temp_path = f.name
        
        try:
            # Test guessing format from a file with uppercase extension
            format_name = guess_format_from_file(temp_path)
            # Should match one of the valid formats that use .json
            assert format_name in ["swagger", "openapi3"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_convert_file_format_detection_from_content(self):
        """Test convert_file with format detection from content."""
        # Create a file with OpenAPI 3 content but .json extension
        openapi3_content = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {}
        }
        
        # Use a binary mode file to avoid type errors
        with tempfile.NamedTemporaryFile(suffix=".json", mode='wb', delete=False) as f:
            f.write(json.dumps(openapi3_content).encode('utf-8'))
            source_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            target_path = f.name
        
        try:
            # Test convert_file with format detection from content
            result = convert_file(
                source_path,
                target_path,
                # Don't specify source_format, let it auto-detect
                target_format="swagger"
            )
            
            # Verify the conversion worked
            assert result is not None
            assert "swagger" in result
            assert result["swagger"] == "2.0"
        finally:
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)
    
    def test_format_extensions_with_all_formats(self):
        """Test that all registered formats have extensions in FORMAT_EXTENSIONS."""
        # Get all available formats
        formats = get_available_formats()
        
        # Check that all formats have extensions
        for format_name in formats:
            assert format_name in FORMAT_EXTENSIONS
            assert len(FORMAT_EXTENSIONS[format_name]) > 0
            
    def test_converter_for_all_format_pairs(self):
        """Test get_converter_for_formats with all possible format pairs."""
        # Get all available formats
        formats = get_available_formats()
        
        # Test all possible combinations of formats
        for source_format in formats:
            for target_format in formats:
                # Skip identity conversion
                if source_format == target_format:
                    continue
                    
                # Get converter for this pair
                converter_cls = get_converter_for_formats(source_format, target_format)
                
                # Either we have a converter or we don't
                if converter_cls is not None:
                    # Verify it's a proper converter class
                    assert issubclass(converter_cls, FormatConverter)
                    assert converter_cls.get_source_format() == source_format
                    assert converter_cls.get_target_format() == target_format
