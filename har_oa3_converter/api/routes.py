"""API routes for conversion endpoints."""

import json
import tempfile
import yaml
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Header, Path, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse

from har_oa3_converter.utils.file_handler import FileHandler

from har_oa3_converter.api.models import (
    ConversionFormat,
    ConversionOptions,
    ConversionResponse,
    ErrorResponse,
    FormatInfo,
    FormatResponse,
)
from har_oa3_converter.converters.format_converter import (
    convert_file,
    get_available_formats,
    get_converter_for_formats,
)

router = APIRouter(tags=["conversion"])


def get_conversion_options(
    title: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    servers: List[str] = Form([]),
    base_path: Optional[str] = Form(None),
    skip_validation: bool = Form(False),
) -> ConversionOptions:
    """Get conversion options from form data.
    
    Args:
        title: API title
        version: API version
        description: API description
        servers: List of server URLs
        base_path: Base path for API endpoints
        
    Returns:
        Conversion options model
    """
    return ConversionOptions(
        title=title,
        version=version,
        description=description,
        servers=servers,
        base_path=base_path,
        skip_validation=skip_validation,
    )


@router.get(
    "/formats",
    summary="List available formats",
    description="Get a list of all available conversion formats.",
    response_model=FormatResponse,
    responses={
        200: {
            "description": "List of available formats",
            "content": {
                "application/json": {},
                "application/yaml": {},
            },
        },
        406: {
            "description": "Not Acceptable",
            "model": ErrorResponse,
        },
    },
)
async def list_formats(
    request: Request,
    accept: Optional[str] = Header(None, description="Accept header for response format"),
) -> Response:
    """List available conversion formats.
    
    Args:
        request: FastAPI request object
        accept: Accept header for response format
        
    Returns:
        Response containing available formats in the requested format
    """
    # Get the available formats
    available_formats = get_available_formats()
    
    # Create structured format information
    format_info = []
    for fmt in available_formats:
        # Add detailed information for each format
        content_types = []
        if fmt == "openapi3" or fmt == "swagger":
            content_types = ["application/json", "application/yaml"]
            description = f"OpenAPI {'3.0' if fmt == 'openapi3' else '2.0'} specification"
        elif fmt == "har":
            content_types = ["application/json"]
            description = "HTTP Archive (HAR) format"
        elif fmt == "postman":
            content_types = ["application/json"]
            description = "Postman Collection format"
        else:
            content_types = ["application/json"]
            description = f"{fmt.capitalize()} format"
        
        format_info.append(FormatInfo(
            name=fmt,
            description=description,
            content_types=content_types
        ))
    
    # Create the response object
    response_data = FormatResponse(formats=format_info)
    
    # Determine content type with proper priority hierarchy
    content_type = "application/json"  # Default
    
    # Check Accept header first
    request_accept = request.headers.get("accept", "")
    if request_accept:
        if "yaml" in request_accept.lower() or "yml" in request_accept.lower():
            content_type = "application/yaml"
    
    # Query parameter accept takes highest priority
    if accept:
        if "yaml" in accept.lower() or "yml" in accept.lower():
            content_type = "application/yaml"
        elif "json" in accept.lower():
            content_type = "application/json"
    
    # Handle YAML format if requested
    if content_type == "application/yaml":
        # Convert Pydantic model to dict, then to YAML for clean serialization
        response_dict = response_data.model_dump()
        # Now convert the dict to YAML
        yaml_content = yaml.dump(response_dict, default_flow_style=False, sort_keys=False)
        return Response(content=yaml_content, media_type="application/yaml")
    
    # Default JSON response
    return response_data


@router.post(
    "/convert/{target_format}",
    summary="Convert document to target format",
    description="Convert an uploaded document to the specified target format.",
    response_model=ConversionResponse,
    responses={
        200: {
            "content": {
                "application/json": {"example": {"format": "openapi3", "content_type": "application/yaml", "success": True}},
                "application/yaml": {},
                "application/x-yaml": {},
                "application/octet-stream": {}
            },
            "description": "Successful conversion"
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request"
        },
        415: {
            "model": ErrorResponse,
            "description": "Unsupported media type"
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation error"
        }
    }
)
async def convert_document(
    request: Request,  # Request is automatically injected, must come before params with defaults
    target_format: ConversionFormat, 
    file: UploadFile = File(...),
    options: ConversionOptions = Depends(get_conversion_options),
    source_format: Optional[str] = Query(None, description="Source format override (auto-detected if not provided)"),
    accept: Optional[str] = Query(None, description="Override Accept header for response format")
) -> Response:
    """Convert a document to the specified format.
    
    Args:
        target_format: Target format (openapi3, swagger, har)
        file: File to convert
        options: Conversion options
        source_format: Override source format (auto-detected if not provided)
        accept: Override Accept header for response format
        
    Returns:
        Converted document or error response
    """
    # Validate that file was uploaded
    if not file:
        raise HTTPException(
            status_code=400, 
            detail="No file uploaded"
        )
    
    # Check if conversion is supported
    target_format_str = target_format.value
    formats = get_available_formats()
    
    if target_format_str not in formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target format: {target_format_str}. Supported formats: {', '.join(formats)}"
        )
    
    # Convert input content_type to potential source format
    input_content_type = file.content_type or ""
    
    # Auto-detect source format if not provided
    if not source_format:
        # Check if it's a HAR file by filename or content type
        if file.filename.lower().endswith(".har") or "har" in input_content_type.lower():
            source_format = "har"
        elif "json" in input_content_type:
            # For JSON files, we'll try to determine if it's openapi3 or swagger during conversion
            source_format = "openapi3"
        elif "yaml" in input_content_type:
            # For YAML files, we'll try to determine if it's openapi3 or swagger during conversion
            source_format = "openapi3"
    
    # Save uploaded file to temporary location
    file_content = await file.read()
    
    # Make sure suffix is appropriate for the source format
    suffix = f".{source_format}" if source_format else ".tmp"
    if source_format == "har" and not suffix.endswith(".har"):
        suffix = ".har"
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        tmp_in.write(file_content)
        input_path = tmp_in.name
        
    # Reset file contents for potential reuse
    await file.seek(0)
    
    # Create a temporary file for output
    output_suffix = ".json" if target_format_str == "swagger" else ".yaml"
    with tempfile.NamedTemporaryFile(delete=False, suffix=output_suffix) as tmp_out:
        output_path = tmp_out.name
    
    # Convert options model to dict for converter
    conversion_options = options.model_dump(exclude_none=True)
    
    try:
        # Perform conversion
        # Determine if validation should be performed
        validate_schema = not conversion_options.pop('skip_validation', False)
        
        result = convert_file(
            input_path,
            output_path,
            source_format=source_format,
            target_format=target_format_str,
            validate_schema=validate_schema,
            **conversion_options
        )
        
        # Determine response content type with proper priority hierarchy
        # 1. Set default based on file extension
        if "json" in output_suffix:
            content_type = "application/json"
        else:
            content_type = "application/yaml"  # Use consistent YAML media type
        
        # 2. Override with Accept header if present
        request_accept = request.headers.get("accept", "")
        if request_accept:
            if "json" in request_accept.lower():
                content_type = "application/json"
            elif "yaml" in request_accept.lower() or "yml" in request_accept.lower():
                content_type = "application/yaml"
        
        # 3. Query parameter 'accept' has highest priority (overrides everything else)
        if accept:
            if "json" in accept.lower() or accept == "application/json":
                content_type = "application/json"
            elif "yaml" in accept.lower() or "yml" in accept.lower():
                content_type = "application/yaml"
        
        # Read the converted file and prepare the response
        with open(output_path, "r") as f:
            converted_content = f.read()
            
        # Process the content based on format
        if "application/json" in content_type:
            # Return JSON response
            if not isinstance(result, dict):
                # Load file using FileHandler if needed
                result = FileHandler.load(output_path)
        
            return Response(
                # Format as JSON with consistent formatting
                content=json.dumps(result, indent=2) if isinstance(result, dict) else converted_content,
                media_type="application/json"
            )
        elif "application/yaml" in content_type or "text/yaml" in content_type:
            # Return YAML response
            if output_suffix == ".json":
                # Convert JSON to YAML using FileHandler
                if not isinstance(result, dict):
                    result = FileHandler.load(output_path)
                # Use the imported yaml module (already imported at the top of the file)
                yaml_content = yaml.dump(result, default_flow_style=False, sort_keys=False)
            else:
                # Use the content directly if it's already in YAML format
                yaml_content = converted_content
        
            return Response(
                content=yaml_content,
                media_type="application/yaml"  # Use consistent YAML media type
            )
        else:
            # Return raw file content
            with open(output_path, "rb") as f:
                file_content = f.read()
        
            return Response(
                content=file_content,
                media_type="application/octet-stream"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Conversion failed: {str(e)}"
        )
