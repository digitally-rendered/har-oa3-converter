"""Tests for the format converter registry."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from har_oa3_converter.converters.format_registry import (
    CONVERTERS,
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file,
)
from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.formats.har_to_openapi3 import HarToOpenApi3Converter
from har_oa3_converter.converters.formats.hoppscotch_to_openapi3 import (
    HoppscotchToOpenApi3Converter,
)
from har_oa3_converter.converters.formats.openapi3_to_openapi3 import (
    OpenApi3ToOpenApi3Converter,
)


class TestFormatRegistry:
    """Tests for the format converter registry."""

    def test_get_available_formats(self):
        """Test getting available formats."""
        formats = get_available_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "har" in formats
        assert "openapi3" in formats
        assert "swagger" in formats
        assert "postman" in formats
        assert "hoppscotch" in formats

    def test_get_converter_for_formats(self):
        """Test getting converter for specific formats."""
        # Test valid format combinations
        converter_cls = get_converter_for_formats("har", "openapi3")
        assert converter_cls is not None
        assert issubclass(converter_cls, FormatConverter)
        assert converter_cls == HarToOpenApi3Converter

        converter_cls = get_converter_for_formats("openapi3", "openapi3")
        assert converter_cls is not None
        assert issubclass(converter_cls, FormatConverter)
        assert converter_cls == OpenApi3ToOpenApi3Converter

        converter_cls = get_converter_for_formats("hoppscotch", "openapi3")
        assert converter_cls is not None
        assert issubclass(converter_cls, FormatConverter)
        assert converter_cls == HoppscotchToOpenApi3Converter

        # Test invalid format combination
        converter_cls = get_converter_for_formats(
            "invalid_format", "another_invalid_format"
        )
        assert converter_cls is None

    def test_guess_format_from_file(self):
        """Test guessing format from file extension and content."""
        # Test with HAR file
        with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
            tmp_file.write(b'{"log": {"version": "1.2", "entries": []}}')
            tmp_file.flush()
            har_path = tmp_file.name

        # Test with OpenAPI 3 JSON file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_file.write(
                b'{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}}'
            )
            tmp_file.flush()
            openapi3_json_path = tmp_file.name

        # Test with OpenAPI 3 YAML file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
            tmp_file.write(
                b'openapi: "3.0.0"\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}'
            )
            tmp_file.flush()
            openapi3_yaml_path = tmp_file.name

        # Test with Postman collection file
        with tempfile.NamedTemporaryFile(
            suffix=".postman_collection.json", delete=False
        ) as tmp_file:
            tmp_file.write(
                b'{"info": {"name": "Test Collection", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}, "item": []}'
            )
            tmp_file.flush()
            postman_path = tmp_file.name

        try:
            # Test format detection
            with patch(
                "har_oa3_converter.converters.schema_validator.detect_format"
            ) as mock_detect:
                # First test with schema detection working
                mock_detect.side_effect = lambda path: {
                    har_path: "har",
                    openapi3_json_path: "openapi3",
                    openapi3_yaml_path: "openapi3",
                    postman_path: "postman",
                }.get(path)

                format_name, error = guess_format_from_file(har_path)
                assert format_name == "har"
                assert error is None

                format_name, error = guess_format_from_file(openapi3_json_path)
                assert format_name == "openapi3"
                assert error is None

                format_name, error = guess_format_from_file(openapi3_yaml_path)
                assert format_name == "openapi3"
                assert error is None

                format_name, error = guess_format_from_file(postman_path)
                assert format_name == "postman"
                assert error is None

                # Then test fallback to extension-based detection when validation fails
                mock_detect.side_effect = Exception("Validation error")

                format_name, error = guess_format_from_file(har_path)
                assert format_name == "har"
                assert error is None

                format_name, error = guess_format_from_file(openapi3_json_path)
                assert format_name == "openapi3"
                assert error is None

                format_name, error = guess_format_from_file(openapi3_yaml_path)
                assert format_name == "openapi3"
                assert error is None

                format_name, error = guess_format_from_file(postman_path)
                assert format_name == "postman"
                assert error is None
        finally:
            # Clean up temporary files
            for path in [
                har_path,
                openapi3_json_path,
                openapi3_yaml_path,
                postman_path,
            ]:
                if os.path.exists(path):
                    os.unlink(path)

    @patch("har_oa3_converter.converters.format_registry.validate_file")
    @patch("har_oa3_converter.converters.format_registry.get_converter_for_formats")
    def test_convert_file(self, mock_get_converter, mock_validate):
        """Test converting a file from one format to another."""
        # Set up mocks
        mock_validate.return_value = (True, "har", None)
        mock_get_converter.return_value = HarToOpenApi3Converter

        # Create a temporary HAR file
        with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
            tmp_file.write(
                b'{"log": {"version": "1.2", "creator": {"name": "Test", "version": "1.0"}, "entries": []}}'
            )
            tmp_file.flush()
            source_path = tmp_file.name

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            target_path = tmp_file.name

        try:
            # Mock the converter's convert method
            with patch.object(HarToOpenApi3Converter, "convert") as mock_convert:
                mock_convert.return_value = {
                    "openapi": "3.0.0",
                    "info": {"title": "API Documentation", "version": "1.0.0"},
                    "paths": {},
                }

                # Test with explicit formats
                result = convert_file(
                    source_path,
                    target_path,
                    source_format="har",
                    target_format="openapi3",
                    title="Custom Title",
                )

                # Verify result
                assert result is not None
                assert result["openapi"] == "3.0.0"

                # Verify the mocks were called correctly
                mock_validate.assert_called_once()
                mock_get_converter.assert_called_once_with("har", "openapi3")
                mock_convert.assert_called_once()

                # Check the arguments passed to convert
                args, kwargs = mock_convert.call_args
                assert kwargs.get("title") == "Custom Title"
        finally:
            # Clean up temporary files
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)

    @patch("har_oa3_converter.converters.format_registry.guess_format_from_file")
    @patch("har_oa3_converter.converters.format_registry.validate_file")
    @patch("har_oa3_converter.converters.format_registry.get_converter_for_formats")
    def test_convert_file_with_auto_format_detection(
        self, mock_get_converter, mock_validate, mock_guess
    ):
        """Test converting a file with automatic format detection."""
        # Set up mocks
        mock_guess.return_value = ("har", None)
        mock_validate.return_value = (True, "har", None)
        mock_get_converter.return_value = HarToOpenApi3Converter

        # Create a temporary HAR file
        with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
            tmp_file.write(
                b'{"log": {"version": "1.2", "creator": {"name": "Test", "version": "1.0"}, "entries": []}}'
            )
            tmp_file.flush()
            source_path = tmp_file.name

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            target_path = tmp_file.name

        try:
            # Mock the converter's convert method
            with patch.object(HarToOpenApi3Converter, "convert") as mock_convert:
                mock_convert.return_value = {
                    "openapi": "3.0.0",
                    "info": {"title": "API Documentation", "version": "1.0.0"},
                    "paths": {},
                }

                # Test with auto-detected formats
                result = convert_file(source_path, target_path)

                # Verify result
                assert result is not None
                assert result["openapi"] == "3.0.0"

                # Verify the mocks were called correctly
                mock_guess.assert_called_once_with(source_path)
                mock_validate.assert_called_once()
                mock_get_converter.assert_called_once_with("har", "openapi3")
                mock_convert.assert_called_once()
        finally:
            # Clean up temporary files
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)

    @patch("har_oa3_converter.converters.format_registry.validate_file")
    def test_convert_file_validation_failure(self, mock_validate):
        """Test handling validation failure during conversion."""
        # Set up mock to fail validation
        error_message = "Invalid HAR format"
        mock_validate.return_value = (False, None, error_message)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
            tmp_file.write(b'{"invalid": "content"}')
            tmp_file.flush()
            source_path = tmp_file.name

        try:
            # Test validation failure
            with pytest.raises(ValueError) as excinfo:
                convert_file(
                    source_path,
                    "output.json",
                    source_format="har",
                    target_format="openapi3",
                )

            # Get the actual error message
            error_str = str(excinfo.value)

            # Verify the error message contains the expected text
            assert (
                "Source file validation failed" in error_str
            ), f"Expected 'Source file validation failed' in '{error_str}'"

            # Verify the mock was called
            mock_validate.assert_called_once()
        finally:
            # Clean up temporary file
            if os.path.exists(source_path):
                os.unlink(source_path)

    @patch("har_oa3_converter.converters.format_registry.validate_file")
    @patch("har_oa3_converter.converters.format_registry.get_converter_for_formats")
    def test_convert_file_no_converter(self, mock_get_converter, mock_validate):
        """Test handling no available converter."""
        # Set up mocks
        mock_validate.return_value = (True, "text", None)
        mock_get_converter.return_value = None  # No converter available

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"Some text content")
            tmp_file.flush()
            source_path = tmp_file.name

        try:
            # Test no converter available
            with pytest.raises(ValueError) as excinfo:
                convert_file(
                    source_path,
                    "output.json",
                    source_format="text",
                    target_format="unknown_format",
                )

            # Verify the error message
            error_str = str(excinfo.value)
            assert (
                "No converter available for text to unknown_format" in error_str
            ), f"Expected 'No converter available' message in '{error_str}'"

            # Verify the mocks were called
            mock_validate.assert_called_once()
            mock_get_converter.assert_called_once_with("text", "unknown_format")
        finally:
            # Clean up temporary file
            if os.path.exists(source_path):
                os.unlink(source_path)
