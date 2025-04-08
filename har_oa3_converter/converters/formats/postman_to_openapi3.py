"""Converter from Postman Collection to OpenAPI 3."""

import json
import os
from typing import Any, Dict, Optional

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.formats.har_to_openapi3 import HarToOpenApi3Converter
from har_oa3_converter.converters.formats.postman_to_har import PostmanToHarConverter


class PostmanToOpenApi3Converter(FormatConverter[Dict[str, Any], Dict[str, Any]]):
    """Converter from Postman Collection to OpenAPI 3."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "postman"

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
        """Convert Postman Collection data to OpenAPI 3.

        Args:
            postman_data: Postman Collection data as dictionary
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary

        Raises:
            ValueError: If the data is not a valid Postman Collection format
        """

        # Validate input type
        if not isinstance(source_data, dict):
            raise ValueError("Postman data must be a dictionary")

        # Validate Postman Collection structure
        if "info" not in source_data or "item" not in source_data:
            raise ValueError("Invalid Postman Collection format: missing required keys")

        # Step 1: Convert Postman to HAR
        postman_to_har = PostmanToHarConverter()
        har_data = postman_to_har.convert_data(source_data)

        # Step 2: Convert HAR to OpenAPI 3
        har_to_openapi3 = HarToOpenApi3Converter()
        openapi3 = har_to_openapi3.convert_data(har_data, **options)

        return openapi3
