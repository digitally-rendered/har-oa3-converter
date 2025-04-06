"""Converter from HAR to OpenAPI 3."""

import json
import os
from typing import Any, Dict, Optional

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter as OriginalConverter
from har_oa3_converter.utils.file_handler import FileHandler


class HarToOpenApi3Converter(FormatConverter):
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

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert HAR to OpenAPI 3.

        Args:
            source_path: Path to HAR file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Read HAR file using FileHandler to handle different formats properly
        file_handler = FileHandler()
        har_data = file_handler.load(source_path)

        # Create HAR to OAS3 converter
        converter = OriginalConverter()

        # Extract options
        title = options.get("title", "API Documentation")
        version = options.get("version", "1.0.0")
        description = options.get("description", "API Documentation generated from HAR file")
        servers = options.get("servers", [])

        # Set up converter options
        converter.info = {
            "title": title,
            "version": version,
            "description": description
        }
        converter.servers = servers
        
        # Convert HAR to OpenAPI 3 using the convert method
        openapi3 = converter.convert_from_string(json.dumps(har_data))

        # Write to target file if specified
        if target_path:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            # Use FileHandler to save the file in the appropriate format
            file_handler.save(openapi3, target_path)

        return openapi3
