"""Registry for format converters."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple, Type

import yaml

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.converters.formats.har_to_openapi3 import HarToOpenApi3Converter
from har_oa3_converter.converters.formats.hoppscotch_to_openapi3 import HoppscotchToOpenApi3Converter
from har_oa3_converter.converters.formats.openapi3_to_openapi3 import OpenApi3ToOpenApi3Converter
from har_oa3_converter.converters.formats.openapi3_to_swagger import OpenApi3ToSwaggerConverter
from har_oa3_converter.converters.formats.postman_to_har import PostmanToHarConverter
from har_oa3_converter.converters.formats.postman_to_openapi3 import PostmanToOpenApi3Converter
from har_oa3_converter.converters.schema_validator import validate_file, detect_format
from har_oa3_converter.utils.file_handler import FileHandler


# Register all available converters
CONVERTERS = [
    HarToOpenApi3Converter,
    HoppscotchToOpenApi3Converter,
    OpenApi3ToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
    PostmanToHarConverter,
    PostmanToOpenApi3Converter,
]


def get_available_formats() -> List[str]:
    """Get list of available formats.

    Returns:
        List of format names
    """
    # Explicitly collect all formats from registered converters
    formats = set()
    
    for converter_cls in CONVERTERS:
        source_fmt = converter_cls.get_source_format()
        target_fmt = converter_cls.get_target_format()
        formats.add(source_fmt)
        formats.add(target_fmt)
    
    # Explicitly add all known formats to ensure they're included
    formats.update(["har", "openapi3", "swagger", "postman", "hoppscotch"])
    
    return sorted(list(formats))


def get_converter_for_formats(
    source_format: str, target_format: str
) -> Optional[Type[FormatConverter]]:
    """Get converter class that can convert from source to target format.

    Args:
        source_format: Source format name
        target_format: Target format name

    Returns:
        Converter class or None if no suitable converter found
    """
    for converter_cls in CONVERTERS:
        if (
            converter_cls.get_source_format() == source_format
            and converter_cls.get_target_format() == target_format
        ):
            return converter_cls
    return None


def guess_format_from_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Guess format from file extension and content.

    Args:
        file_path: Path to file

    Returns:
        Tuple of (format_name, error_message) where format_name is None if format could not be determined
    """
    # Try to detect format from file content using schema validation
    try:
        is_valid, format_name, error_message = validate_file(file_path)
        if is_valid and format_name:
            return format_name, None
        return None, error_message or "Unable to detect format"
    except Exception as e:
        # Fall back to extension-based detection
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Map extensions to formats
        extension_map = {
            ".har": "har",
            ".json": "openapi3",  # Default JSON to OpenAPI 3
            ".yaml": "openapi3",  # Default YAML to OpenAPI 3
            ".yml": "openapi3",  # Default YAML to OpenAPI 3
            ".postman_collection.json": "postman",
        }

        # Special case for Postman collections
        if file_path.endswith(".postman_collection.json"):
            return "postman", None

        format_name = extension_map.get(ext)
        if format_name:
            return format_name, None
        
        return None, f"Unable to determine format for {file_path}"



def convert_file(
    source_path: str,
    target_path: str,
    source_format: Optional[str] = None,
    target_format: Optional[str] = None,
    validate_schema: bool = True,
    **options,
) -> Optional[Dict[str, Any]]:
    """Convert file from source format to target format.

    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_format: Source format name (will be guessed if not provided)
        target_format: Target format name (will be guessed if not provided)
        validate_schema: Whether to validate input against schema
        options: Additional converter-specific options

    Returns:
        Converted data or None if conversion failed

    Raises:
        ValueError: If source or target format could not be determined
        ValueError: If no converter is available for the specified formats
        ValueError: If source file validation fails
    """
    # Ensure source file exists
    if not os.path.isfile(source_path):
        raise ValueError(f"Source file not found: {source_path}")

    # Determine source format if not provided
    if not source_format:
        source_format, error = guess_format_from_file(source_path)
        if not source_format:
            raise ValueError(
                f"Could not determine source format for file: {source_path}. {error}"
            )

    # Determine target format if not provided
    if not target_format:
        # For target path, we'll use extension-based detection as the file might not exist yet
        _, ext = os.path.splitext(target_path)
        ext = ext.lower()
        
        # Map extensions to formats
        extension_map = {
            ".har": "har",
            ".json": "openapi3",  # Default JSON to OpenAPI 3
            ".yaml": "openapi3",  # Default YAML to OpenAPI 3
            ".yml": "openapi3",  # Default YAML to OpenAPI 3
            ".postman_collection.json": "postman",
        }
        
        # Special case for Postman collections
        if target_path.endswith(".postman_collection.json"):
            target_format = "postman"
        else:
            target_format = extension_map.get(ext)
            
        if not target_format:
            raise ValueError(
                f"Could not determine target format for file: {target_path}"
            )

    # Validate source file against schema if requested
    if validate_schema:
        is_valid, detected_format, error = validate_file(source_path)
        if not is_valid:
            raise ValueError(
                f"Source file validation failed: {error}"
            )
        
        # If source_format was not provided but detected, use the detected format
        if not source_format and detected_format:
            source_format = detected_format

    # Get converter for the specified formats
    converter_cls = get_converter_for_formats(source_format, target_format)
    if not converter_cls:
        raise ValueError(
            f"No converter available for {source_format} to {target_format}"
        )

    # Create converter instance and convert file
    converter = converter_cls()
    result = converter.convert(source_path, target_path, **options)

    return result
