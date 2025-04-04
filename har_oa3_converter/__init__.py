"""HAR to OpenAPI 3 Converter.

This module provides tools to convert HAR (HTTP Archive) files to OpenAPI 3 specification
and other API specification formats.

Modules:
    - converters: Core conversion functionality
    - cli: Command-line interfaces
    - api: FastAPI-based web server
"""

__version__ = "0.1.0"

# Import main components for easier access
from har_oa3_converter.converters import (
    HarToOas3Converter,
    convert_file,
    get_available_formats,
)

__all__ = [
    "HarToOas3Converter",
    "convert_file",
    "get_available_formats",
]
