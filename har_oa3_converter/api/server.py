"""FastAPI server for API format conversion."""

import argparse
import sys
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from har_oa3_converter import __version__
from har_oa3_converter.api.routes import router as conversion_router

# Create FastAPI application
app = FastAPI(
    title="HAR to OpenAPI Converter API",
    description="API for converting between HAR, OpenAPI 3, and Swagger formats",
    version=__version__,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversion_router, prefix="/api")


# Add exception handlers
@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
    """Handle TimeoutError exceptions.

    Args:
        request: FastAPI request
        exc: TimeoutError exception

    Returns:
        JSON response with 408 status code
    """
    return JSONResponse(
        status_code=408, content={"detail": f"Operation timed out: {str(exc)}"}
    )


@app.exception_handler(MemoryError)
async def memory_exception_handler(request: Request, exc: MemoryError):
    """Handle MemoryError exceptions.

    Args:
        request: FastAPI request
        exc: MemoryError exception

    Returns:
        JSON response with 413 status code
    """
    return JSONResponse(
        status_code=413,
        content={"detail": f"Memory error - file too large: {str(exc)}"},
    )


def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Fix OpenAPI version to 3.0.3 for Schemathesis compatibility
    # FastAPI uses 3.1.0 by default which isn't fully supported by Schemathesis
    openapi_schema["openapi"] = "3.0.3"

    # Add servers to OpenAPI schema
    openapi_schema["servers"] = [{"url": "/"}]

    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "conversion",
            "description": "API format conversion operations",
        }
    ]

    # Make sure schema validation uses JSON_SCHEMA documents
    for path in openapi_schema.get("paths", {}).values():
        for operation in path.values():
            if "requestBody" in operation and "content" in operation["requestBody"]:
                # Ensure schema validation is enabled
                for content_type in operation["requestBody"]["content"].values():
                    if "schema" in content_type:
                        content_type["schema"]["x-json-schema-validation"] = True

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Properly override the openapi method
# Use setattr to avoid the 'Cannot assign to a method' error
setattr(app, "openapi", lambda: custom_openapi())


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Start the HAR to OpenAPI converter API server"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind server to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind server to (default: 8000)"
    )

    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the API server.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        Exit code
    """
    parsed_args = parse_args(args)

    print(f"Starting HAR to OpenAPI Converter API server v{__version__}")
    print(f"Server running at http://{parsed_args.host}:{parsed_args.port}")
    print("Press Ctrl+C to stop")

    try:
        uvicorn.run(
            "har_oa3_converter.api.server:app",
            host=parsed_args.host,
            port=parsed_args.port,
            reload=parsed_args.reload,
        )
        return 0
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
