"""Schema validation for different API specification formats."""

import os
from typing import Dict, Any, Tuple, Optional

from jsonschema import validate, ValidationError

from har_oa3_converter.utils.file_handler import FileHandler
from har_oa3_converter.schemas import (
    HAR_SCHEMA,
    OPENAPI3_SCHEMA,
    SWAGGER_SCHEMA,
    POSTMAN_SCHEMA,
    get_schema,
)

# Define the formats we support for validation
SUPPORTED_FORMATS = ["har", "openapi3", "swagger", "postman"]


def validate_format(
    data: Dict[str, Any], format_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate data against a format schema.

    Args:
        data: Data to validate
        format_name: Format name (har, openapi3, swagger, postman)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Get schema from centralized repository
    schema = get_schema(format_name)
    if not schema:
        return False, f"Unknown format: {format_name}"

    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message}"


def detect_format(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to detect the format of the given data.

    Args:
        data: Data to detect format for

    Returns:
        Tuple of (format_name, error_message)
    """
    # Try each supported format
    for format_name in SUPPORTED_FORMATS:
        is_valid, error = validate_format(data, format_name)
        if is_valid:
            return format_name, None

    # Format not detected
    return None, "Unable to detect format"


def validate_file(file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate a file against all known schemas and detect its format.

    Args:
        file_path: Path to file to validate

    Returns:
        Tuple of (is_valid, format_name, error_message)

    Raises:
        FileNotFoundError: If the file does not exist
    """
    # Check if file exists first
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Use the FileHandler to load the file content
        data = FileHandler.load(file_path)
    except ValueError as e:
        return False, None, str(e)
    except Exception as e:
        return False, None, f"Error loading file: {str(e)}"

    # Try to detect format
    format_name, error = detect_format(data)
    if not format_name:
        return False, None, error

    # Validate against detected format schema
    is_valid, error = validate_format(data, format_name)
    return is_valid, format_name, error
