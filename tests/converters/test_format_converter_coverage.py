"""Tests to improve coverage of the format_converter.py module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.format_converter import (
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file,
    CONVERTERS,
    OpenApi3ToSwaggerConverter,
    HarToOpenApi3Converter,
    FORMAT_EXTENSIONS,
)


@pytest.fixture
def petstore_openapi3_path():
    """Path to the Petstore OpenAPI 3 spec."""
    return Path(__file__).parent.parent / "fixtures" / "petstore_openapi3.json"


@pytest.fixture
def petstore_openapi3(petstore_openapi3_path):
    """Load Petstore OpenAPI 3 spec as a dict."""
    with open(petstore_openapi3_path, "r") as f:
        return json.load(f)


class TestFormatConverterCoverage:
    """Tests specifically targeting coverage gaps in format_converter.py."""

    def test_server_url_parsing_in_openapi3_to_swagger(self, petstore_openapi3):
        """Test server URL parsing from OpenAPI 3 to Swagger."""
        # Create converter and convert
        converter = OpenApi3ToSwaggerConverter()
        result = converter._convert_openapi3_to_swagger2(petstore_openapi3)

        # Verify URL parsing was done correctly
        assert "host" in result
        assert result["host"] == "petstore.swagger.io"
        assert result["basePath"] == "/v2"
        assert "schemes" in result
        assert "https" in result["schemes"]

    def test_server_url_parsing_with_no_path(self):
        """Test server URL parsing when there's no path component."""
        # Create a test OpenAPI 3 spec with server URL having no path
        openapi3 = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {},
        }

        # Create converter and convert
        converter = OpenApi3ToSwaggerConverter()
        result = converter._convert_openapi3_to_swagger2(openapi3)

        # Verify URL parsing was done correctly for a URL without a path
        assert result["host"] == "api.example.com"
        assert result["basePath"] == "/"  # Default base path
        assert "https" in result["schemes"]

    def test_convert_with_yaml_output(self, petstore_openapi3_path):
        """Test converting with YAML output format."""
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_out:
            output_path = tmp_out.name

        try:
            # Convert from OpenAPI 3 JSON to Swagger YAML
            # Convert PosixPath to string to avoid attribute errors
            result = convert_file(
                str(petstore_openapi3_path),
                output_path,
                source_format="openapi3",
                target_format="swagger",
            )

            # Verify the result and file content
            assert result is not None
            assert os.path.exists(output_path)

            # Load the YAML output
            with open(output_path, "r") as f:
                content = yaml.safe_load(f)

            # Check Swagger conversion specifics
            assert "swagger" in content
            assert content["swagger"] == "2.0"
            assert "host" in content
            assert content["host"] == "petstore.swagger.io"
            assert content["basePath"] == "/v2"
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_convert_json_output_format(self, petstore_openapi3_path):
        """Test converting with explicit JSON output format."""
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_out:
            output_path = tmp_out.name

        try:
            # Convert from OpenAPI 3 to Swagger with JSON output
            # Convert PosixPath to string to avoid attribute errors
            result = convert_file(
                str(petstore_openapi3_path),
                output_path,
                source_format="openapi3",
                target_format="swagger",
            )

            # Verify the result and file content
            assert result is not None
            assert os.path.exists(output_path)

            # Load the JSON output
            with open(output_path, "r") as f:
                content = json.load(f)

            # Check Swagger conversion specifics
            assert "swagger" in content
            assert content["swagger"] == "2.0"
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_format_detection_from_file(self, petstore_openapi3_path):
        """Test auto-detection of the source format from file."""
        # Test format detection from file extension and content
        detected_format = guess_format_from_file(str(petstore_openapi3_path))
        assert detected_format == "openapi3"

        # Test detection when source format is not provided to convert_file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_out:
            output_path = tmp_out.name

        try:
            result = convert_file(
                str(petstore_openapi3_path),
                output_path,
                # No source_format provided, should auto-detect
                target_format="swagger",
            )
            assert result is not None
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_from_format_extensions(self):
        """Test the format extension mappings."""
        # Test that FORMAT_EXTENSIONS mapping is used correctly
        assert FORMAT_EXTENSIONS is not None
        assert "har" in FORMAT_EXTENSIONS
        assert ".har" in FORMAT_EXTENSIONS["har"]
        assert "openapi3" in FORMAT_EXTENSIONS
        assert ".yaml" in FORMAT_EXTENSIONS["openapi3"]
        assert "swagger" in FORMAT_EXTENSIONS
        assert ".json" in FORMAT_EXTENSIONS["swagger"]

        # Test converting raw dictionaries directly through convert_file
        # Create a simple test dict in OpenAPI 3 format
        openapi3 = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com/v1"}],
            "paths": {},
        }

        # Save to a temp file and convert using binary mode
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="wb", delete=False
        ) as tmp_in:
            tmp_in.write(json.dumps(openapi3).encode("utf-8"))
            tmp_in_path = tmp_in.name

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name

        try:
            # Write to the file and close it properly to ensure content is flushed
            tmp_in.close()

            # Test the convert_file function with source format detection
            result = convert_file(
                tmp_in_path,
                tmp_out_path,
                source_format="openapi3",
                target_format="swagger",
            )

            # Verify the result has been converted to Swagger
            assert result is not None
            assert "swagger" in result
            assert result["swagger"] == "2.0"
            # Check for host and basePath which are Swagger-specific properties
            assert "host" in result
            assert "basePath" in result
        finally:
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)

    def test_schema_conversion_in_openapi3_to_swagger(self):
        """Test schema conversion from OpenAPI 3 to Swagger."""
        # Create a test schema with different types and features
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "format": "int64"},
                "name": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "nested": {"$ref": "#/components/schemas/NestedType"},
            },
        }

        # Test schema conversion
        converter = OpenApi3ToSwaggerConverter()
        converted_schema = converter._convert_schema(schema)

        # Verify schema conversion
        assert converted_schema["type"] == "object"
        assert "properties" in converted_schema
        assert "id" in converted_schema["properties"]
        assert converted_schema["properties"]["id"]["type"] == "integer"

        # Test reference conversion
        ref_schema = {"$ref": "#/components/schemas/Pet"}
        converted_ref = converter._convert_schema_ref(ref_schema)
        assert converted_ref["$ref"] == "#/definitions/Pet"

    def test_converter_selection_edge_cases(self):
        """Test edge cases in converter selection."""
        # Test with invalid format names
        # Check that invalid formats return None rather than raising ValueError
        converter = get_converter_for_formats("unknown", "openapi3")
        assert converter is None

        # Test invalid target format
        converter = get_converter_for_formats("openapi3", "unknown")
        assert converter is None

        # Test self-conversion (same format)
        # This should return None as there's no converter that converts to the same format
        converter = get_converter_for_formats("openapi3", "openapi3")
        assert converter is None

        # Test valid converter selection
        converter = get_converter_for_formats("openapi3", "swagger")
        assert converter is not None
        assert converter == OpenApi3ToSwaggerConverter

        # Test all available formats
        formats = get_available_formats()
        assert "openapi3" in formats
        assert "swagger" in formats
        assert "har" in formats
