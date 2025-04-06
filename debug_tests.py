#!/usr/bin/env python
"""Debug script for fixing test failures."""

import json
import os
import sys
from pathlib import Path

import yaml

from har_oa3_converter.converters.format_converter import convert_file
from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter
from har_oa3_converter.converters.schema_validator import validate_file


def debug_yaml_file(file_path):
    """Debug YAML file loading issues."""
    print(f"\nTesting file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(
        f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'}"
    )

    # Try to read the file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"File content (first 100 chars): {content[:100]}")
    except Exception as e:
        print(f"Error reading file: {e}")

    # Try both JSON and YAML parsing
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print("Successfully parsed as JSON")
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                print(f"Successfully parsed as YAML: {type(data)}")
                print(
                    f"YAML content keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}"
                )
            except Exception as e:
                print(f"YAML parsing error: {e}")
    except Exception as e:
        print(f"General error: {e}")

    # Try schema validation
    try:
        is_valid, format_name, error = validate_file(file_path)
        print(
            f"Schema validation: valid={is_valid}, format={format_name}, error={error}"
        )
    except Exception as e:
        print(f"Validation error: {e}")


def debug_test_cli():
    """Debug the CLI test issues."""
    import tempfile

    from tests.cli.test_har_to_oas_cli import TestHarToOasCli

    # Create a test HAR file
    print("\nCreating test HAR file...")
    test_class = TestHarToOasCli()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har", mode="w") as f:
        har_data = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Debug Tests", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "https://example.com/api/resource",
                            "headers": [],
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"id": 1, "name": "Test"}',
                            },
                        },
                    }
                ],
            }
        }
        json.dump(har_data, f)
        har_path = f.name

    print(f"Created test HAR file at: {har_path}")

    # Test with the HarToOas3Converter directly
    try:
        print("\nTesting HarToOas3Converter directly...")
        converter = HarToOas3Converter()
        # Try with and without validate_schema
        result_without = converter.convert(har_path)
        print("Convert without validate_schema: Success!")

        # This will likely fail until we fix the converter
        try:
            result_with = converter.convert(har_path, validate_schema=True)
            print("Convert with validate_schema: Success!")
        except Exception as e:
            print(f"Convert with validate_schema failed: {e}")
    except Exception as e:
        print(f"Converter test failed: {e}")

    # Test the convert_file function
    try:
        print("\nTesting convert_file function...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
            output_path = f.name

        result = convert_file(
            har_path,
            output_path,
            source_format="har",
            target_format="openapi3",
            validate_schema=True,
            title="Test API",
        )
        print("convert_file Success!")
        print(f"Output file exists: {os.path.exists(output_path)}")

        # Check output file content
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"Output content (first 100 chars): {content[:100]}")

        # Clean up
        os.unlink(output_path)
    except Exception as e:
        print(f"convert_file test failed: {e}")

    # Clean up
    os.unlink(har_path)


if __name__ == "__main__":
    print("\n===== HAR-OA3-Converter Test Debug Tool =====\n")

    # If a file path is specified, debug that file
    if len(sys.argv) > 1:
        debug_yaml_file(sys.argv[1])
    else:
        # Run general debug tests
        debug_test_cli()
