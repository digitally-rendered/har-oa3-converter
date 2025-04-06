"""Schema validation for different API specification formats."""

import os
from typing import Any, Dict, Optional, Tuple

from jsonschema import ValidationError, validate

from har_oa3_converter.schemas import get_schema
from har_oa3_converter.utils.file_handler import FileHandler

# Define the formats we support for validation
SUPPORTED_FORMATS = ["har", "openapi3", "swagger", "postman", "hoppscotch"]

# Schema constants used by other modules
HAR_SCHEMA = get_schema("har")
OPENAPI3_SCHEMA = get_schema("openapi3")
SWAGGER_SCHEMA = get_schema("swagger")
POSTMAN_SCHEMA = get_schema("postman")
HOPPSCOTCH_SCHEMA = get_schema("hoppscotch")


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
        is_valid, _ = validate_format(data, format_name)
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


def validate_schema_object(
    data: Dict[str, Any], schema_name: str, timeout: int = 30
) -> Tuple[bool, Optional[str]]:
    """Validate a data object against a JSON schema with timeout.

    Args:
        data: Data to validate
        schema_name: Name of the schema to validate against
        timeout: Timeout in seconds for validation

    Returns:
        Tuple of (is_valid, error_message)

    Raises:
        TimeoutError: If validation takes longer than the timeout
    """
    # Get schema
    schema = get_schema(schema_name)
    if not schema:
        return False, f"Unknown schema: {schema_name}"

    # Add a basic timeout check for complex validations
    # This is simplified; in a real application, you might use multiprocessing
    # or threading with a real timeout mechanism
    import time

    start_time = time.time()

    try:
        validate(instance=data, schema=schema)
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(
                f"Schema validation took {elapsed:.2f}s, which exceeds the {timeout}s timeout"
            )
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message}"
    except Exception as e:
        return False, f"Error during validation: {str(e)}"
