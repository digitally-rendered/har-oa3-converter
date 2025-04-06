"""Tests for the OpenAPI 3 to OpenAPI 3 converter."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
import yaml

from har_oa3_converter.converters.formats.openapi3_to_openapi3 import OpenApi3ToOpenApi3Converter


@pytest.fixture
def sample_openapi3_data():
    """Sample OpenAPI 3 data for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "users": {
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
                                }
                            }
                        }
                    }
                }
            }
        }
    }


class TestOpenApi3ToOpenApi3Converter:
    """Tests for the OpenAPI 3 to OpenAPI 3 converter."""
    
    def test_get_source_format(self):
        """Test the get_source_format class method."""
        assert OpenApi3ToOpenApi3Converter.get_source_format() == "openapi3"
    
    def test_get_target_format(self):
        """Test the get_target_format class method."""
        assert OpenApi3ToOpenApi3Converter.get_target_format() == "openapi3"
    
    def test_convert_json_to_json(self, sample_openapi3_data):
        """Test converting OpenAPI 3 JSON to OpenAPI 3 JSON."""
        # Create a temporary OpenAPI 3 JSON file
        tmp_file_path = tempfile.mktemp(suffix=".json")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(sample_openapi3_data, tmp_file)
        
        try:
            # Create a temporary output file
            out_file_path = tempfile.mktemp(suffix=".json")
            
            # Create the converter and convert the file
            converter = OpenApi3ToOpenApi3Converter()
            result = converter.convert(tmp_file_path, out_file_path)
            
            # Verify the result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Sample API"
            assert result["info"]["version"] == "1.0.0"
            assert result["paths"]["/users"]["get"]["summary"] == "Get users"
            
            # Verify the output file exists and contains the converted data
            assert os.path.exists(out_file_path)
            with open(out_file_path, "r") as f:
                output_data = json.load(f)
                assert output_data == sample_openapi3_data
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(out_file_path):
                os.unlink(out_file_path)
    
    def test_convert_yaml_to_yaml(self, sample_openapi3_data):
        """Test converting OpenAPI 3 YAML to OpenAPI 3 YAML."""
        # Create a temporary OpenAPI 3 YAML file
        tmp_file_path = tempfile.mktemp(suffix=".yaml")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            yaml.dump(sample_openapi3_data, tmp_file)
        
        try:
            # Create a temporary output file
            out_file_path = tempfile.mktemp(suffix=".yaml")
            
            # Create the converter and convert the file
            converter = OpenApi3ToOpenApi3Converter()
            result = converter.convert(tmp_file_path, out_file_path)
            
            # Verify the result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Sample API"
            assert result["info"]["version"] == "1.0.0"
            assert result["paths"]["/users"]["get"]["summary"] == "Get users"
            
            # Verify the output file exists and contains the converted data
            assert os.path.exists(out_file_path)
            with open(out_file_path, "r") as f:
                output_data = yaml.safe_load(f)
                assert output_data == sample_openapi3_data
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(out_file_path):
                os.unlink(out_file_path)
    
    def test_convert_yaml_to_json(self, sample_openapi3_data):
        """Test converting OpenAPI 3 YAML to OpenAPI 3 JSON."""
        # Create a temporary OpenAPI 3 YAML file
        tmp_file_path = tempfile.mktemp(suffix=".yaml")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            yaml.dump(sample_openapi3_data, tmp_file)
        
        try:
            # Create a temporary output file
            out_file_path = tempfile.mktemp(suffix=".json")
            
            # Create the converter and convert the file
            converter = OpenApi3ToOpenApi3Converter()
            result = converter.convert(tmp_file_path, out_file_path)
            
            # Verify the result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Sample API"
            assert result["info"]["version"] == "1.0.0"
            assert result["paths"]["/users"]["get"]["summary"] == "Get users"
            
            # Verify the output file exists and contains the converted data
            assert os.path.exists(out_file_path)
            with open(out_file_path, "r") as f:
                output_data = json.load(f)
                assert output_data == sample_openapi3_data
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(out_file_path):
                os.unlink(out_file_path)
    
    def test_convert_json_to_yaml(self, sample_openapi3_data):
        """Test converting OpenAPI 3 JSON to OpenAPI 3 YAML."""
        # Create a temporary OpenAPI 3 JSON file
        tmp_file_path = tempfile.mktemp(suffix=".json")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(sample_openapi3_data, tmp_file)
        
        try:
            # Create a temporary output file
            out_file_path = tempfile.mktemp(suffix=".yaml")
            
            # Create the converter and convert the file
            converter = OpenApi3ToOpenApi3Converter()
            result = converter.convert(tmp_file_path, out_file_path)
            
            # Verify the result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Sample API"
            assert result["info"]["version"] == "1.0.0"
            assert result["paths"]["/users"]["get"]["summary"] == "Get users"
            
            # Verify the output file exists and contains the converted data
            assert os.path.exists(out_file_path)
            with open(out_file_path, "r") as f:
                output_data = yaml.safe_load(f)
                assert output_data == sample_openapi3_data
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(out_file_path):
                os.unlink(out_file_path)
    
    def test_convert_without_target_path(self, sample_openapi3_data):
        """Test converting OpenAPI 3 without specifying a target path."""
        # Create a temporary OpenAPI 3 file
        tmp_file_path = tempfile.mktemp(suffix=".json")
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(sample_openapi3_data, tmp_file)
        
        try:
            # Create the converter and convert the file without specifying a target path
            converter = OpenApi3ToOpenApi3Converter()
            result = converter.convert(tmp_file_path)
            
            # Verify the result
            assert result["openapi"] == "3.0.0"
            assert result["info"]["title"] == "Sample API"
            assert result["info"]["version"] == "1.0.0"
            assert result["paths"]["/users"]["get"]["summary"] == "Get users"
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
