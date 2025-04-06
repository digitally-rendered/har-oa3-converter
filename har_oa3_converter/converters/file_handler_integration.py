"""Integration module for FileHandler with schemas and converters."""

from typing import Any, Dict

# Import schemas
from har_oa3_converter.converters.schema_validator import (
    HAR_SCHEMA,
    OPENAPI3_SCHEMA,
    POSTMAN_SCHEMA,
    SWAGGER_SCHEMA,
)

# Import FileHandler
from har_oa3_converter.utils.file_handler import FileHandler


def register_schemas() -> None:
    """Register all the supported schemas with the FileHandler."""
    # Register schemas with null checks to satisfy mypy
    if HAR_SCHEMA is not None:
        FileHandler.register_schema("har", HAR_SCHEMA)
    if OPENAPI3_SCHEMA is not None:
        FileHandler.register_schema("openapi3", OPENAPI3_SCHEMA)
    if SWAGGER_SCHEMA is not None:
        FileHandler.register_schema("swagger", SWAGGER_SCHEMA)
    if POSTMAN_SCHEMA is not None:
        FileHandler.register_schema("postman", POSTMAN_SCHEMA)


def load_file(file_path: str) -> Dict[str, Any]:
    """Load file content using FileHandler with error handling.

    Args:
        file_path: Path to file

    Returns:
        Loaded file content

    Raises:
        ValueError: If file could not be loaded
        FileNotFoundError: If file does not exist
    """
    return FileHandler.load(file_path)


def save_file(data: Dict[str, Any], file_path: str) -> None:
    """Save file content using FileHandler with error handling.

    Args:
        data: Data to save
        file_path: Path to save to

    Raises:
        ValueError: If file could not be saved
    """
    FileHandler.save(data, file_path)


def validate_with_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a registered schema.

    Args:
        data: Data to validate
        schema_name: Name of schema to validate against

    Returns:
        True if valid, False otherwise
    """
    return FileHandler.validate(data, schema_name)
