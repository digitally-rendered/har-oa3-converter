"""Converter for OpenAPI 3 to OpenAPI 3 (format-to-format conversion)."""

import json
import os
import tempfile
from typing import Any, Dict, Optional

import yaml

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.utils.file_handler import FileHandler


class OpenApi3ToOpenApi3Converter(FormatConverter):
    """Converter for OpenAPI 3 to OpenAPI 3 (format-to-format conversion)."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "openapi3"

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
        """Convert OpenAPI 3 to OpenAPI 3 (format conversion only).

        Args:
            source_path: Path to OpenAPI 3 file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Read OpenAPI 3 file using FileHandler to handle different formats properly
        file_handler = FileHandler()
        openapi3 = file_handler.load(source_path)

        # Write to target file if specified
        if target_path:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            
            # Use FileHandler to save the file in the appropriate format
            file_handler.save(openapi3, target_path)

        return openapi3
