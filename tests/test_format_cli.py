"""Tests for the format CLI module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.format_cli import parse_args, main


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
                        "queryString": [],
                        "headers": []
                    },
                    "response": {
                        "status": 200,
                        "headers": [],
                        "content": {
                            "mimeType": "application/json",
                            "text": "{\"data\": []}"
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


@pytest.fixture
def sample_openapi_file():
    """Create a sample OpenAPI file for testing."""
    sample_data = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/api/users": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "array",
                                                "items": {}
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
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name
    
    yield file_path
    
    # Cleanup
    os.unlink(file_path)


class TestFormatCli:
    """Test class for format CLI module."""
    
    def test_parse_args_minimal(self):
        """Test parsing arguments with minimal options."""
        args = parse_args(["input.json", "output.yaml"])
        
        assert args.input == "input.json"
        assert args.output == "output.yaml"
        assert args.from_format is None
        assert args.to_format is None
        assert args.title == "API Specification"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated by format-converter"
        assert hasattr(args, "servers")
        assert isinstance(args.servers, list)
    
    def test_parse_args_full(self):
        """Test parsing arguments with all options."""
        args = parse_args([
            "input.json", 
            "output.yaml", 
            "--from-format", "openapi3",
            "--to-format", "swagger",
            "--title", "Test API",
            "--version", "1.0.0",
            "--description", "Test Description",
            "--server", "https://api.example.com",
            "--base-path", "/api"
        ])
        
        assert args.input == "input.json"
        assert args.output == "output.yaml"
        assert args.from_format == "openapi3"
        assert args.to_format == "swagger"
        assert args.title == "Test API"
        assert args.version == "1.0.0"
        assert args.description == "Test Description"
        assert args.servers == ["https://api.example.com"]
        assert args.base_path == "/api"
    
    def test_main_har_to_openapi(self, sample_har_file):
        """Test converting HAR to OpenAPI using main function."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()
        
        try:
            # Run main with explicit formats
            exit_code = main([
                sample_har_file,
                output_file.name,
                "--from-format", "har",
                "--to-format", "openapi3"
            ])
            
            # Check exit code
            assert exit_code == 0
            
            # Check that output file was created
            assert os.path.exists(output_file.name)
            
            # Check that output is valid OpenAPI 3
            with open(output_file.name, "r") as f:
                data = json.load(f)
                
            assert "openapi" in data
            assert data["openapi"] == "3.0.0"
            assert "paths" in data
            assert "/api/users" in data["paths"]
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_main_openapi_to_swagger(self, sample_openapi_file):
        """Test converting OpenAPI to Swagger using main function."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()
        
        try:
            # Run main with explicit formats
            exit_code = main([
                sample_openapi_file,
                output_file.name,
                "--from-format", "openapi3",
                "--to-format", "swagger"
            ])
            
            # Check exit code
            assert exit_code == 0
            
            # Check that output file was created
            assert os.path.exists(output_file.name)
            
            # Check that output is valid Swagger
            with open(output_file.name, "r") as f:
                data = json.load(f)
                
            assert "swagger" in data
            assert data["swagger"] == "2.0"
            assert "paths" in data
            assert "/api/users" in data["paths"]
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_main_with_auto_detection(self, sample_har_file):
        """Test main function with format auto-detection."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()
        
        try:
            # Run main without explicit formats
            exit_code = main([
                sample_har_file,
                output_file.name
            ])
            
            # Check exit code
            assert exit_code == 0
            
            # Check that output file was created
            assert os.path.exists(output_file.name)
            
            # Load output file
            with open(output_file.name, "r") as f:
                content = f.read()
                
            # Should be valid JSON
            data = json.loads(content)
            assert data is not None
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_main_with_yaml_output(self, sample_har_file):
        """Test main function with YAML output."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        output_file.close()
        
        try:
            # Run main with YAML output
            exit_code = main([
                sample_har_file,
                output_file.name,
                "--from-format", "har",
                "--to-format", "openapi3"
            ])
            
            # Check exit code
            assert exit_code == 0
            
            # Check that output file was created
            assert os.path.exists(output_file.name)
            
            # Load output file
            with open(output_file.name, "r") as f:
                data = yaml.safe_load(f)
                
            # Check that it's valid OpenAPI
            assert "openapi" in data
            assert data["openapi"] == "3.0.0"
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_main_with_metadata(self, sample_har_file):
        """Test main function with metadata options."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()
        
        try:
            # Run main with metadata options
            exit_code = main([
                sample_har_file,
                output_file.name,
                "--from-format", "har",
                "--to-format", "openapi3",
                "--title", "Custom API",
                "--version", "2.0.0",
                "--description", "Custom description"
            ])
            
            # Check exit code
            assert exit_code == 0
            
            # Check that output file was created with custom metadata
            with open(output_file.name, "r") as f:
                data = json.load(f)
                
            assert data["info"]["title"] == "Custom API"
            assert data["info"]["version"] == "2.0.0"
            assert data["info"]["description"] == "Custom description"
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_main_with_list_formats(self):
        """Test main function with --list-formats option."""
        # Run main with --list-formats
        # Note: input and output arguments are required even with --list-formats
        exit_code = main(["input.json", "output.json", "--list-formats"])
        
        # Should return success exit code
        assert exit_code == 0
    
    def test_main_error_invalid_input(self):
        """Test main function with invalid input file."""
        # Create a temporary invalid file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(b"invalid content")
            invalid_file = f.name
        
        try:
            # Run main with invalid file
            exit_code = main([invalid_file, "output.json"])
            
            # Should return non-zero exit code for error
            assert exit_code != 0
        finally:
            # Cleanup
            os.unlink(invalid_file)
    
    def test_main_error_nonexistent_input(self):
        """Test main function with nonexistent input file."""
        # Run main with nonexistent file
        exit_code = main(["nonexistent.json", "output.json"])
        
        # Should return non-zero exit code for error
        assert exit_code != 0
    
    def test_main_error_unsupported_conversion(self, sample_har_file):
        """Test main function with unsupported conversion."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()
        
        try:
            # Run main with invalid conversion (har to har)
            exit_code = main([
                sample_har_file,
                output_file.name,
                "--from-format", "har",
                "--to-format", "har"
            ])
            
            # Should return non-zero exit code for error
            assert exit_code != 0
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
