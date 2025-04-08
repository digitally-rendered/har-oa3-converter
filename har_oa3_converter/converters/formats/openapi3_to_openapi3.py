"""Converter for OpenAPI 3 to OpenAPI 3 (format-to-format conversion)."""

import json
import os
import tempfile
from typing import Any, Dict, Optional

import yaml

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.utils.file_handler import FileHandler


class OpenApi3ToOpenApi3Converter(FormatConverter[Dict[str, Any], Dict[str, Any]]):
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

    def convert_data(
        self, source_data: Dict[str, Any], **options: Any
    ) -> Dict[str, Any]:
        """Convert OpenAPI 3 to OpenAPI 3 (format conversion only).

        Args:
            source_data: OpenAPI 3 data as dictionary
            options: Additional options

        Returns:
            OpenAPI 3 specification as dictionary
        """

        # Simply return the OpenAPI 3 data as is - this converter just performs format conversion
        # when used with file I/O, but directly passes through the data structure
        return source_data
