"""Tests for API models."""

import pytest
from pydantic import ValidationError

from har_oa3_converter.api.models import (
    ConversionFormat,
    ConversionOptions,
    ConversionResponse,
    ErrorResponse
)


class TestConversionFormat:
    """Test the ConversionFormat enum."""

    def test_conversion_format_values(self):
        """Test that enum values are correct."""
        assert ConversionFormat.HAR == "har"
        assert ConversionFormat.OPENAPI3 == "openapi3"
        assert ConversionFormat.SWAGGER == "swagger"

    def test_conversion_format_creation(self):
        """Test creating ConversionFormat from string."""
        assert ConversionFormat("har") == ConversionFormat.HAR
        assert ConversionFormat("openapi3") == ConversionFormat.OPENAPI3
        assert ConversionFormat("swagger") == ConversionFormat.SWAGGER

        # Test invalid value
        with pytest.raises(ValueError):
            ConversionFormat("invalid")


class TestConversionOptions:
    """Test the ConversionOptions model."""

    def test_conversion_options_defaults(self):
        """Test default values for ConversionOptions."""
        options = ConversionOptions()
        assert options.title is None
        assert options.version is None
        assert options.description is None
        assert options.servers is None
        assert options.base_path is None
        assert options.skip_validation is False

    def test_conversion_options_values(self):
        """Test setting values for ConversionOptions."""
        options = ConversionOptions(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            servers=["https://api.example.com"],
            base_path="/api",
            skip_validation=True
        )
        
        assert options.title == "Test API"
        assert options.version == "1.0.0"
        assert options.description == "Test API Description"
        assert options.servers == ["https://api.example.com"]
        assert options.base_path == "/api"
        assert options.skip_validation is True

    def test_conversion_options_dict(self):
        """Test converting ConversionOptions to dictionary."""
        options = ConversionOptions(
            title="Test API",
            version="1.0.0"
        )
        
        options_dict = options.model_dump()
        assert options_dict["title"] == "Test API"
        assert options_dict["version"] == "1.0.0"
        assert options_dict["skip_validation"] is False


class TestConversionResponse:
    """Test the ConversionResponse model."""

    def test_conversion_response_required_fields(self):
        """Test that required fields must be provided."""
        # All required fields provided
        response = ConversionResponse(
            format=ConversionFormat.HAR,
            content_type="application/json",
            success=True
        )
        assert response.format == ConversionFormat.HAR
        assert response.content_type == "application/json"
        assert response.success is True
        assert response.error is None

        # Missing required fields
        with pytest.raises(ValidationError):
            ConversionResponse(format=ConversionFormat.HAR, success=True)
        
        with pytest.raises(ValidationError):
            ConversionResponse(content_type="application/json", success=True)

    def test_conversion_response_with_error(self):
        """Test ConversionResponse with error."""
        response = ConversionResponse(
            format=ConversionFormat.HAR,
            content_type="application/json",
            success=False,
            error="Conversion failed"
        )
        
        assert response.success is False
        assert response.error == "Conversion failed"


class TestErrorResponse:
    """Test the ErrorResponse model."""

    def test_error_response(self):
        """Test creating an ErrorResponse."""
        error = ErrorResponse(detail="An error occurred")
        assert error.detail == "An error occurred"

    def test_error_response_missing_detail(self):
        """Test that detail is required."""
        with pytest.raises(ValidationError):
            ErrorResponse()
