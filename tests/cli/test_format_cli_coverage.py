"""Tests to improve coverage of the format_cli module."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from har_oa3_converter.format_cli import main as format_cli_main


def test_format_detection_failure():
    """Test handling when format detection fails."""
    # Create a file with ambiguous format (not easily detectable)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as input_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_file:
        input_file.write(b"This is not a valid format")
        input_path = input_file.name
        output_path = output_file.name
    
    try:
        # Test source format detection failure
        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            # Mock guess_format_from_file to return None (detection failure)
            with mock.patch("har_oa3_converter.format_cli.guess_format_from_file", return_value=None):
                result = format_cli_main([input_path, output_path])
                # Should fail because format can't be detected
                assert result == 1
                
        # Test target format detection failure
        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            # Mock guess_format_from_file to return a value for source but None for target
            with mock.patch("har_oa3_converter.format_cli.guess_format_from_file", side_effect=["openapi3", None]):
                result = format_cli_main([input_path, output_path])
                # Should fail because target format can't be detected
                assert result == 1
    finally:
        # Cleanup
        for path in [input_path, output_path]:
            if Path(path).exists():
                os.unlink(path)


def test_unsupported_conversion():
    """Test handling when the requested conversion is not supported."""
    # Create valid files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as input_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as output_file:
        input_file.write(b"{}")
        input_path = input_file.name
        output_path = output_file.name
    
    try:
        # Test with unsupported conversion
        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            # Mock get_converter_for_formats to return None (no available converter)
            with mock.patch("har_oa3_converter.format_cli.get_converter_for_formats", return_value=None):
                # Mock guess_format_from_file to return formats
                with mock.patch("har_oa3_converter.format_cli.guess_format_from_file", side_effect=["format1", "format2"]):
                    result = format_cli_main([input_path, output_path])
                    # Should fail because no converter is available
                    assert result == 1
    finally:
        # Cleanup
        for path in [input_path, output_path]:
            if Path(path).exists():
                os.unlink(path)


def test_conversion_options():
    """Test that conversion options are correctly passed to the converter."""
    # Create valid files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as input_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as output_file:
        input_file.write(b"{\"log\": {\"version\": \"1.2\", \"creator\": {\"name\": \"test\"}, \"entries\": []}}")
        input_path = input_file.name
        output_path = output_file.name
    
    try:
        # Test with custom options
        with mock.patch("sys.stdout"):
            # Mock convert_file to verify options
            with mock.patch("har_oa3_converter.format_cli.convert_file") as mock_convert:
                # Use actual format detection but mock the conversion
                args = [
                    input_path, 
                    output_path,
                    "--title", "Custom Title", 
                    "--version", "2.0.0", 
                    "--description", "Custom description", 
                    "--server", "https://api.example.com", 
                    "--base-path", "/api/v1"
                ]
                result = format_cli_main(args)
                
                # Should succeed
                assert result == 0
                
                # Verify all options were passed correctly
                args, kwargs = mock_convert.call_args
                # In the actual implementation, convert_file is called with:
                # input_path, output_path, source_format, target_format, **options
                assert "title" in kwargs and kwargs["title"] == "Custom Title"
                assert "version" in kwargs and kwargs["version"] == "2.0.0"
                assert "description" in kwargs and kwargs["description"] == "Custom description"
                assert "servers" in kwargs and kwargs["servers"] == ["https://api.example.com"]
                assert "base_path" in kwargs and kwargs["base_path"] == "/api/v1"
    finally:
        # Cleanup
        for path in [input_path, output_path]:
            if Path(path).exists():
                os.unlink(path)


def test_conversion_error_handling():
    """Test handling of errors during conversion."""
    # Create valid files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as input_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as output_file:
        input_file.write(b"{\"log\": {\"version\": \"1.2\", \"creator\": {\"name\": \"test\"}, \"entries\": []}}")
        input_path = input_file.name
        output_path = output_file.name
    
    try:
        # Test error during conversion
        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            # Mock convert_file to raise an exception
            with mock.patch("har_oa3_converter.format_cli.convert_file", 
                          side_effect=Exception("Conversion error")):
                result = format_cli_main([input_path, output_path])
                # Should return error code
                assert result == 1
    finally:
        # Cleanup
        for path in [input_path, output_path]:
            if Path(path).exists():
                os.unlink(path)
