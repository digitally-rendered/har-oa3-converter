"""Tests for the CLI modules of HAR to OpenAPI 3 converter."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from har_oa3_converter.cli import main as cli_main, parse_args as cli_parse_args
from har_oa3_converter.cli.har_to_oas_cli import main as har_cli_main, parse_args as har_cli_parse_args
from har_oa3_converter.cli.format_cli import main as format_cli_main, parse_args as format_cli_parse_args


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


@pytest.fixture
def sample_openapi3_file():
    """Create a sample OpenAPI 3 file for testing."""
    sample_data = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "Get users",
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
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
        yaml.dump(sample_data, f)
        file_path = f.name
    
    yield file_path
    
    # Cleanup
    os.unlink(file_path)


class TestMainCli:
    """Test the main CLI module."""
    
    def test_main_json_decode_error(self):
        """Test handling of JSON decode errors in main CLI module."""
        # Create an invalid JSON file that will trigger JSONDecodeError
        with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
            f.write(b"This is not valid JSON {broken")
            invalid_file_path = f.name
        
        try:
            # Mock stderr to avoid printing error messages during test
            with mock.patch("sys.stderr"):
                result = cli_main([invalid_file_path, "-o", "output.yaml"])
                # Verify error handling with correct exit code
                assert result == 1
        finally:
            # Cleanup
            if Path(invalid_file_path).exists():
                os.unlink(invalid_file_path)
    
    def test_parse_args(self):
        """Test argument parsing for main CLI."""
        # Test with minimal arguments
        args = cli_parse_args(["input.har"])
        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.json is False
        assert args.title == "API generated from HAR"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated from HAR file"
        assert args.servers == []
        
        # Test with all arguments
        args = cli_parse_args([
            "input.har",
            "-o", "output.json",
            "--json",
            "--title", "Custom API",
            "--version", "2.0.0",
            "--description", "Custom description",
            "--server", "https://api1.example.com",
            "--server", "https://api2.example.com",
        ])
        assert args.input == "input.har"
        assert args.output == "output.json"
        assert args.json is True
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"
        assert args.servers == ["https://api1.example.com", "https://api2.example.com"]
    
    def test_main_success(self, sample_har_file):
        """Test successful execution of main CLI."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run with mock to capture output
            with mock.patch("sys.stdout") as mock_stdout:
                result = cli_main([sample_har_file, "-o", output_path])
                
                # Check result
                assert result == 0
                assert Path(output_path).exists()
                assert mock_stdout.write.call_count > 0
                
                # Check output file content
                with open(output_path, "r") as f:
                    content = yaml.safe_load(f)
                    assert "openapi" in content
                    assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
                
    def test_main_json_output(self, sample_har_file):
        """Test main CLI with JSON output."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run with JSON output
            result = cli_main([sample_har_file, "-o", output_path, "--json"])
            
            # Check result
            assert result == 0
            assert Path(output_path).exists()
            
            # Check output file content
            with open(output_path, "r") as f:
                content = json.load(f)
                assert "openapi" in content
                assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
                
    def test_main_nonexistent_input(self):
        """Test main CLI with nonexistent input file."""
        with mock.patch("sys.stderr"):
            result = cli_main(["nonexistent.har", "-o", "output.yaml"])
            assert result == 1
            
    def test_main_error_handling(self):
        """Test error handling in main CLI."""
        # Create an invalid HAR file
        with tempfile.NamedTemporaryFile(suffix=".har", delete=False, mode="w") as temp_file:
            temp_file.write("This is not valid JSON")
            invalid_har_path = temp_file.name
            
        try:
            # Run with invalid input
            with mock.patch("sys.stderr"):
                result = cli_main([invalid_har_path, "-o", "output.yaml"])
                assert result == 1
        finally:
            os.unlink(invalid_har_path)


class TestHarToOasCli:
    """Test the har_to_oas_cli module."""
    
    def test_har_cli_json_decode_error(self):
        """Test handling of JSON decode errors in HAR to OAS CLI module."""
        # Create an invalid JSON file that will trigger JSONDecodeError
        with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
            f.write(b"{ Invalid HAR JSON")
            invalid_file_path = f.name
        
        try:
            # Mock stderr to avoid printing error messages during test
            with mock.patch("sys.stderr"):
                result = har_cli_main([invalid_file_path, "-o", "output.yaml"])
                # Verify error handling with correct exit code
                assert result == 1
        finally:
            # Cleanup
            if Path(invalid_file_path).exists():
                os.unlink(invalid_file_path)
    
    def test_parse_args(self):
        """Test argument parsing for HAR to OAS CLI."""
        # Test with minimal arguments
        args = har_cli_parse_args(["input.har"])
        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.json is False
        assert args.title == "API generated from HAR"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated from HAR file"
        assert args.servers == []
        
        # Test with all arguments
        args = har_cli_parse_args([
            "input.har",
            "-o", "output.json",
            "--json",
            "--title", "Custom API",
            "--version", "2.0.0",
            "--description", "Custom description",
            "--server", "https://api1.example.com",
            "--server", "https://api2.example.com",
        ])
        assert args.input == "input.har"
        assert args.output == "output.json"
        assert args.json is True
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"
        assert args.servers == ["https://api1.example.com", "https://api2.example.com"]
    
    def test_har_cli_main_success(self, sample_har_file):
        """Test successful execution of HAR to OAS CLI."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run with mock to capture output
            with mock.patch("sys.stdout") as mock_stdout:
                result = har_cli_main([sample_har_file, "-o", output_path])
                
                # Check result
                assert result == 0
                assert Path(output_path).exists()
                assert mock_stdout.write.call_count > 0
                
                # Check output file content
                with open(output_path, "r") as f:
                    content = yaml.safe_load(f)
                    assert "openapi" in content
                    assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
    
    def test_har_cli_error_handling(self):
        """Test error handling in HAR to OAS CLI."""
        with mock.patch("sys.stderr"):
            result = har_cli_main(["nonexistent.har", "-o", "output.yaml"])
            assert result == 1


class TestFormatCli:
    """Test the format_cli module."""
    
    def test_format_cli_json_decode_error(self):
        """Test handling of JSON decode errors in format CLI module."""
        # Create an invalid JSON file that will trigger JSONDecodeError
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(b"{ \"broken\":: 'json' }")
            invalid_file_path = f.name
        
        try:
            # Test with explicit format to avoid auto-detection failures
            with mock.patch("sys.stderr"):
                result = format_cli_main([
                    invalid_file_path, 
                    "output.yaml",
                    "--from-format", "openapi3",
                    "--to-format", "swagger"
                ])
                # Verify error handling with correct exit code
                assert result == 1
        finally:
            # Cleanup
            if Path(invalid_file_path).exists():
                os.unlink(invalid_file_path)
    
    def test_format_cli_parse_args(self):
        """Test argument parsing for format CLI."""
        # Test with minimal arguments
        args = format_cli_parse_args(["input.har", "output.yaml"])
        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.from_format is None
        assert args.to_format is None
        assert args.title == "API Specification"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated by format-converter"
        assert args.servers == []
        
        # Test with format specification
        args = format_cli_parse_args([
            "input.json", 
            "output.yaml",
            "--from-format", "openapi3",
            "--to-format", "swagger"
        ])
        assert args.input == "input.json"
        assert args.output == "output.yaml"
        assert args.from_format == "openapi3"
        assert args.to_format == "swagger"
        
        # Test with all arguments
        args = format_cli_parse_args([
            "input.har",
            "output.json",
            "--from-format", "har",
            "--to-format", "openapi3",
            "--title", "Custom API",
            "--version", "2.0.0",
            "--description", "Custom description",
            "--server", "https://api1.example.com",
            "--server", "https://api2.example.com",
        ])
        assert args.input == "input.har"
        assert args.output == "output.json"
        assert args.from_format == "har"
        assert args.to_format == "openapi3"
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"
        assert args.servers == ["https://api1.example.com", "https://api2.example.com"]
    
    def test_format_cli_main_success(self, sample_har_file, sample_openapi3_file):
        """Test successful execution of format CLI."""
        # Test HAR to OpenAPI 3 conversion
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run with mock to capture output
            with mock.patch("sys.stdout") as mock_stdout:
                result = format_cli_main([
                    sample_har_file, 
                    output_path,
                    "--from-format", "har",
                    "--to-format", "openapi3"
                ])
                
                # Check result
                assert result == 0
                assert Path(output_path).exists()
                assert mock_stdout.write.call_count > 0
                
                # Check output file content
                with open(output_path, "r") as f:
                    content = yaml.safe_load(f)
                    assert "openapi" in content
                    assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
                
        # Test OpenAPI 3 to Swagger conversion
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run with mock to capture output
            with mock.patch("sys.stdout") as mock_stdout:
                result = format_cli_main([
                    sample_openapi3_file, 
                    output_path,
                    "--from-format", "openapi3",
                    "--to-format", "swagger"
                ])
                
                # Check result
                assert result == 0
                assert Path(output_path).exists()
                
                # Check output file content
                with open(output_path, "r") as f:
                    content = json.load(f)
                    assert "swagger" in content
                    assert content["swagger"] == "2.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
    
    def test_format_cli_auto_detection(self, sample_har_file):
        """Test format auto-detection in format CLI."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            output_path = temp_file.name
            
        try:
            # Run without specifying formats (rely on auto-detection)
            with mock.patch("sys.stdout"):
                result = format_cli_main([sample_har_file, output_path])
                
                # Check result
                assert result == 0
                assert Path(output_path).exists()
                
                # Check output file content
                with open(output_path, "r") as f:
                    content = yaml.safe_load(f)
                    assert "openapi" in content
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
    
    def test_format_cli_error_handling(self):
        """Test error handling in format CLI."""
        # Test with nonexistent input file
        with mock.patch("sys.stderr"):
            result = format_cli_main(["nonexistent.har", "output.yaml"])
            assert result == 1
            
        # Test with incompatible formats
        with mock.patch("sys.stderr"):
            result = format_cli_main([
                "input.json", 
                "output.yaml", 
                "--from-format", "swagger", 
                "--to-format", "har"
            ])
            assert result == 1
            
    def test_format_cli_list_formats(self):
        """Test listing available formats in format CLI."""
        # The actual implementation requires input/output even with --list-formats
        # Create dummy files to satisfy the argument parser
        with tempfile.NamedTemporaryFile(suffix=".txt") as dummy_input, \
             tempfile.NamedTemporaryFile(suffix=".txt") as dummy_output:
            with mock.patch("sys.stdout") as mock_stdout:
                result = format_cli_main([
                    dummy_input.name,
                    dummy_output.name,
                    "--list-formats"
                ])
                assert result == 0
                assert mock_stdout.write.call_count > 0
