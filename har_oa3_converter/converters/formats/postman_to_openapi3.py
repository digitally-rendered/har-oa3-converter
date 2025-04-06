"""Converter from Postman Collection to OpenAPI 3."""

import json
import os
from typing import Any, Dict, Optional

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.formats.postman_to_har import PostmanToHarConverter
from har_oa3_converter.converters.formats.har_to_openapi3 import HarToOpenApi3Converter


class PostmanToOpenApi3Converter(FormatConverter):
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

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert Postman Collection to OpenAPI 3.

        Args:
            source_path: Path to Postman Collection file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Create a temporary file for the intermediate HAR format
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_har_path = tmp_file.name

        try:
            # Step 1: Convert Postman to HAR
            postman_to_har = PostmanToHarConverter()
            har_data = postman_to_har.convert(source_path, tmp_har_path)

            # Step 2: Convert HAR to OpenAPI 3
            har_to_openapi3 = HarToOpenApi3Converter()
            openapi3 = har_to_openapi3.convert(tmp_har_path, target_path, **options)
            
            # If target_path is specified, the file has already been written by har_to_openapi3.convert()

            return openapi3
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_har_path):
                os.unlink(tmp_har_path)
