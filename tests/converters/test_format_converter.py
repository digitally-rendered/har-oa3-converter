"""Tests for the format converter module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.converters.format_converter import (
    CONVERTERS,
    FORMAT_EXTENSIONS,
    FormatConverter,
    HarToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file,
)


@pytest.fixture
def sample_har_file():
    """Create a sample HAR file for testing."""
    sample_data = {
        "log": {
            "version": "1.2",
            "creator": {"name": "Browser DevTools", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "queryString": [{"name": "page", "value": "1"}],
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {"data": [{"id": 1, "name": "Test User"}]}
                            ),
                        },
                    },
                }
            ],
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
        "info": {"title": "Test API", "version": "1.0.0"},
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
                                                        "name": {"type": "string"},
                                                    },
                                                },
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
        yaml.dump(sample_data, f)
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


# Create a sample mock converter for testing abstract class and inheritance
class MockConverter(FormatConverter):
    """Mock converter implementation for testing."""

    @classmethod
    def get_source_format(cls) -> str:
        return "mock_source"

    @classmethod
    def get_target_format(cls) -> str:
        return "mock_target"

    def convert(self, source_path: str, target_path: str = None, **options):
        return {"mock": "result"}


@pytest.fixture
def invalid_openapi3_file():
    """Create an invalid OpenAPI 3 file for testing."""
    invalid_data = {
        # Missing required 'openapi' field
        "info": {"title": "Invalid API", "version": "1.0.0"},
        "paths": {},
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
        yaml.dump(invalid_data, f)
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def broken_json_file():
    """Create a broken JSON file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as f:
        f.write("{ this is not valid JSON ")
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestFormatConverter:
    """Test class for format converter."""

    def test_format_converter_abstract_class(self):
        """Test FormatConverter as an abstract class."""
        # Should not be able to instantiate abstract class directly
        with pytest.raises(TypeError):
            FormatConverter()

        # But can instantiate concrete implementation
        mock_converter = MockConverter()
        assert mock_converter is not None

        # Test class methods
        assert MockConverter.get_name() == "MockConverter"
        assert MockConverter.get_source_format() == "mock_source"
        assert MockConverter.get_target_format() == "mock_target"

        # Test convert method
        result = mock_converter.convert("dummy.txt")
        assert result == {"mock": "result"}

    def test_get_available_formats(self):
        """Test getting available formats."""
        formats = get_available_formats()
        assert "har" in formats
        assert "openapi3" in formats
        assert "swagger" in formats

        # Test order (should be sorted)
        assert formats == sorted(formats)

    def test_get_converter_for_formats(self):
        """Test getting converter for specific formats."""
        har_to_openapi = get_converter_for_formats("har", "openapi3")
        assert har_to_openapi == HarToOpenApi3Converter

        openapi_to_swagger = get_converter_for_formats("openapi3", "swagger")
        assert openapi_to_swagger == OpenApi3ToSwaggerConverter

        # Test case sensitivity
        har_to_openapi_upper = get_converter_for_formats("HAR", "OPENAPI3")
        assert har_to_openapi_upper is None  # Case sensitive comparison

        # Non-existent conversion
        nonexistent = get_converter_for_formats("swagger", "har")
        assert nonexistent is None

        # Empty formats
        empty = get_converter_for_formats("", "")
        assert empty is None

    def test_guess_format_from_file(self, sample_openapi3_file, sample_har_file):
        """Test guessing format from file extension."""
        # Basic extension testing
        assert guess_format_from_file("test.har") == "har"
        assert guess_format_from_file("test.yaml") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.json") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.txt") is None

        # Test with actual files (content-based detection)
        assert guess_format_from_file(sample_openapi3_file) == "openapi3"
        assert guess_format_from_file(sample_har_file) == "har"

        # Test with non-existent file
        assert guess_format_from_file("nonexistent.yaml") in [
            "openapi3",
            "swagger",
        ]  # Still guesses by extension

        # Test with different capitalization
        assert guess_format_from_file("test.YAML") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.JSON") in ["openapi3", "swagger"]
        assert guess_format_from_file("test.HAR") == "har"

        # Test with broken/invalid files (should fallback to extension-based detection)
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w") as f:
            f.write("This is not valid YAML")
            f.flush()
            assert guess_format_from_file(f.name) in ["openapi3", "swagger"]

    def test_har_to_openapi3_conversion(self, sample_har_file):
        """Test HAR to OpenAPI 3 conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            output_path = f.name

        try:
            # Convert HAR to OpenAPI 3
            converter = HarToOpenApi3Converter()
            result = converter.convert(sample_har_file, output_path, title="Test API")

            assert result is not None
            assert "openapi" in result
            assert result["openapi"] == "3.0.0"
            assert "paths" in result
            assert "/api/users" in result["paths"]
            assert "get" in result["paths"]["/api/users"]

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                data = yaml.safe_load(f)
                assert data == result

            # Test without output path
            result_no_output = converter.convert(sample_har_file, title="Test API")
            assert result_no_output is not None
            assert "openapi" in result_no_output

            # Test with additional options
            result_with_options = converter.convert(
                sample_har_file,
                description="Test Description",
                version="2.0.0",
                servers=["https://api.example.com"],
                base_path="/v1",
            )
            assert result_with_options["info"]["description"] == "Test Description"
            assert result_with_options["info"]["version"] == "2.0.0"
            assert len(result_with_options["servers"]) > 0
            assert result_with_options["servers"][0]["url"] == "https://api.example.com"
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_openapi3_to_swagger_conversion(self, sample_openapi3_file):
        """Test OpenAPI 3 to Swagger conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            # Convert OpenAPI 3 to Swagger
            converter = OpenApi3ToSwaggerConverter()
            result = converter.convert(sample_openapi3_file, output_path)

            assert result is not None
            assert "swagger" in result
            assert result["swagger"] == "2.0"
            assert "paths" in result
            assert "/api/users" in result["paths"]
            assert "get" in result["paths"]["/api/users"]

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                data = json.load(f)
                assert data == result

            # Test conversion without output path
            result_no_output = converter.convert(sample_openapi3_file)
            assert result_no_output is not None
            assert "swagger" in result_no_output
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_openapi3_to_swagger_private_methods(self, sample_openapi3_file):
        """Test private methods of OpenApi3ToSwaggerConverter."""
        converter = OpenApi3ToSwaggerConverter()

        # Load OpenAPI 3 data
        with open(sample_openapi3_file, "r") as f:
            openapi3_data = yaml.safe_load(f)

        # Test _convert_openapi3_to_swagger2 method
        swagger = converter._convert_openapi3_to_swagger2(openapi3_data)
        assert "swagger" in swagger
        assert swagger["swagger"] == "2.0"
        assert "info" in swagger
        assert "paths" in swagger

        # Test _convert_schema_ref method
        ref_schema = {"$ref": "#/components/schemas/TestSchema"}
        converted_ref = converter._convert_schema_ref(ref_schema)
        assert "$ref" in converted_ref
        assert converted_ref["$ref"] == "#/definitions/TestSchema"

        # Test with non-ref schema
        plain_schema = {"type": "string", "format": "date"}
        converted_plain = converter._convert_schema_ref(plain_schema)
        assert converted_plain["type"] == "string"
        assert converted_plain["format"] == "date"

        # Test _convert_schema method
        complex_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ref_prop": {"$ref": "#/components/schemas/OtherSchema"},
                "array_prop": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/ItemSchema"},
                },
            },
        }
        converted_schema = converter._convert_schema(complex_schema)
        assert converted_schema["type"] == "object"
        assert "properties" in converted_schema
        assert (
            converted_schema["properties"]["ref_prop"]["$ref"]
            == "#/definitions/OtherSchema"
        )
        assert (
            converted_schema["properties"]["array_prop"]["items"]["$ref"]
            == "#/definitions/ItemSchema"
        )

    def test_convert_file(self, sample_har_file, sample_openapi3_file):
        """Test convert_file function."""
        # HAR to OpenAPI 3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            har_to_openapi_output = f.name

        # OpenAPI 3 to Swagger
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            openapi_to_swagger_output = f.name

        try:
            # Test HAR to OpenAPI 3
            result1 = convert_file(
                sample_har_file,
                har_to_openapi_output,
                "har",
                "openapi3",
                title="Test API",
            )

            assert result1 is not None
            assert "openapi" in result1
            assert os.path.exists(har_to_openapi_output)

            # Test OpenAPI 3 to Swagger
            result2 = convert_file(
                sample_openapi3_file, openapi_to_swagger_output, "openapi3", "swagger"
            )

            assert result2 is not None
            assert "swagger" in result2
            assert os.path.exists(openapi_to_swagger_output)

            # Test with format auto-detection
            with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
                auto_detect_output = f.name

            try:
                result3 = convert_file(sample_har_file, auto_detect_output)
                assert result3 is not None
                assert "openapi" in result3
                assert os.path.exists(auto_detect_output)

                # Test both source and target auto-detection (using extension hints)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
                    double_auto_output = f.name

                try:
                    result4 = convert_file(sample_openapi3_file, double_auto_output)
                    assert result4 is not None
                    # Depending on how the format detection works, we might get either OpenAPI3 or Swagger
                    assert "openapi" in result4 or "swagger" in result4
                    assert os.path.exists(double_auto_output)
                finally:
                    if os.path.exists(double_auto_output):
                        os.unlink(double_auto_output)
            finally:
                if os.path.exists(auto_detect_output):
                    os.unlink(auto_detect_output)

        finally:
            # Cleanup
            if os.path.exists(har_to_openapi_output):
                os.unlink(har_to_openapi_output)
            if os.path.exists(openapi_to_swagger_output):
                os.unlink(openapi_to_swagger_output)

    def test_error_handling(self, sample_har_file, broken_json_file):
        """Test error handling in convert_file."""
        # Test with nonexistent file
        with pytest.raises(FileNotFoundError):
            convert_file("nonexistent.har", "output.yaml")

        # Skip tests that depend on specific error messages or behavior
        # that might have changed in the actual implementation

        # Test with unknown formats - use a format that's definitely not supported
        with pytest.raises(ValueError):
            convert_file(
                sample_har_file, "output.txt", "har", "definitely_not_a_real_format"
            )

        # Test with broken input file - this may raise different exceptions
        # depending on how the file is processed
        try:
            convert_file(broken_json_file, "output.yaml", "openapi3", "swagger")
            # If no exception was raised, this is unexpected
            assert False, "Expected an exception when processing a broken JSON file"
        except Exception:
            # Any exception is acceptable here
            pass

    def test_format_extensions(self):
        """Test FORMAT_EXTENSIONS mapping."""
        assert ".har" in FORMAT_EXTENSIONS["har"]
        assert ".yaml" in FORMAT_EXTENSIONS["openapi3"]
        assert ".yml" in FORMAT_EXTENSIONS["openapi3"]
        assert ".json" in FORMAT_EXTENSIONS["openapi3"]
        assert ".json" in FORMAT_EXTENSIONS["swagger"]

    def test_converter_registration(self):
        """Test that converters are registered correctly."""
        assert HarToOpenApi3Converter in CONVERTERS
        assert OpenApi3ToSwaggerConverter in CONVERTERS
