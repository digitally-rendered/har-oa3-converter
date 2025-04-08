"""Converter from HAR to OpenAPI 3."""

import json
import os
from typing import Any, Dict, Optional

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.har_to_oas3 import (
    HarToOas3Converter as OriginalConverter,
)
from har_oa3_converter.utils.file_handler import FileHandler


class HarToOpenApi3Converter(FormatConverter[Dict[str, Any], Dict[str, Any]]):
    """Converter from HAR to OpenAPI 3."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "har"

    @classmethod
    def get_target_format(cls) -> str:
        """Get the target format this converter produces.

        Returns:
            Target format name
        """
        return "openapi3"

    def convert_data(
        self, source_data: Dict[str, Any], **options: Any
    ) -> Dict[str, Any]:
        """Convert HAR data to OpenAPI 3.

        Args:
            har_data: HAR data as dictionary
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary

        Raises:
            ValueError: If the data is not a valid HAR format
        """

        # Validate input type
        if not isinstance(source_data, dict):
            raise ValueError("HAR data must be a dictionary")

        # Validate HAR structure
        if "log" not in source_data:
            raise ValueError("Invalid HAR data: missing 'log' key")

        # Create HAR to OAS3 converter
        converter = OriginalConverter()

        # Extract options
        title = options.get("title", "API Documentation")
        version = options.get("version", "1.0.0")
        description = options.get(
            "description", "API Documentation generated from HAR file"
        )
        servers = options.get("servers", [])

        # Set up converter options
        converter.info = {
            "title": title,
            "version": version,
            "description": description,
        }
        converter.servers = servers

        # Convert HAR to OpenAPI 3 using the convert method
        # First convert the HAR data to JSON string for the underlying converter
        har_json_str = json.dumps(source_data)

        # Use the original converter to generate OpenAPI 3 specification
        openapi3 = converter.convert_from_string(har_json_str)

        # The openapi3 should already be a dictionary, but let's ensure it
        if isinstance(openapi3, str):
            openapi3 = json.loads(openapi3)

        return openapi3
