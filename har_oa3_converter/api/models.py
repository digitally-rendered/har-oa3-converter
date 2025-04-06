"""API data models."""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ConversionFormat(str, Enum):
    """Supported conversion formats."""
    
    # Import here to avoid circular imports
    from har_oa3_converter.converters.format_registry import get_available_formats
    
    # Get all available formats
    _formats = get_available_formats()
    
    # Define enum values statically based on available formats
    HAR = "har"
    OPENAPI3 = "openapi3"
    SWAGGER = "swagger"
    POSTMAN = "postman"
    HOPPSCOTCH = "hoppscotch"

class ConversionOptions(BaseModel):
    """Options for conversion API."""

    title: Optional[str] = Field(
        None, description="API title for OpenAPI/Swagger output"
    )
    version: Optional[str] = Field(
        None, description="API version for OpenAPI/Swagger output"
    )
    description: Optional[str] = Field(
        None, description="API description for OpenAPI/Swagger output"
    )
    servers: Optional[List[str]] = Field(
        None, description="Server URLs for OpenAPI/Swagger output"
    )
    base_path: Optional[str] = Field(None, description="Base path for API endpoints")
    skip_validation: bool = Field(
        False, description="Skip schema validation of input file"
    )


class ConversionResponse(BaseModel):
    """Response model for conversion API."""

    format: ConversionFormat = Field(..., description="Target format of the conversion")
    content_type: str = Field(..., description="Content type of the converted document")
    success: bool = Field(..., description="Whether the conversion was successful")
    error: Optional[str] = Field(None, description="Error message if conversion failed")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error detail message")


class FormatInfo(BaseModel):
    """Information about a conversion format."""

    name: str = Field(..., description="Format name")
    description: str = Field(..., description="Format description")
    content_types: List[str] = Field(
        ..., description="Supported content types for this format"
    )


class FormatResponse(BaseModel):
    """Response model for formats endpoint."""

    formats: List[FormatInfo] = Field(..., description="Available conversion formats")
