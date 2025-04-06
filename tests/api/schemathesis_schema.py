"""Generate a clean OpenAPI 3.0.3 schema for Schemathesis testing.

This module creates a compatible schema specifically formatted for Schemathesis.
"""

import copy
from typing import Any, Dict

# Base schema compatible with Schemathesis
SCHEMA = {
    "openapi": "3.0.3",
    "info": {
        "title": "HAR to OpenAPI 3 Converter API",
        "version": "0.1.0",
        "description": "API for converting between different API specification formats",
    },
    "paths": {
        "/api/formats": {
            "get": {
                "summary": "Get available formats",
                "description": "Returns a list of all available formats for conversion.",
                "operationId": "get_formats",
                "responses": {
                    "200": {
                        "description": "List of available formats",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "formats": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "description": {"type": "string"},
                                                    "content_types": {
                                                        "type": "array",
                                                        "items": {"type": "string"},
                                                    },
                                                },
                                                "required": ["name"],
                                            },
                                        }
                                    },
                                    "required": ["formats"],
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/convert/{target_format}": {
            "post": {
                "summary": "Convert document to target format",
                "description": "Convert an uploaded document to the specified target format.",
                "operationId": "convert_document",
                "parameters": [
                    {
                        "name": "target_format",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": ["openapi3", "har", "swagger"],
                        },
                        "description": "Target format to convert to",
                    },
                    {
                        "name": "source_format",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "nullable": True},
                        "description": "Source format override (auto-detected if not provided)",
                    },
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "File to convert",
                                    },
                                    "title": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "Title for the converted document",
                                    },
                                    "version": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "Version for the converted document",
                                    },
                                    "description": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "Description for the converted document",
                                    },
                                    "servers": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Server URLs for the converted document",
                                    },
                                    "base_path": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "Base path for the converted document",
                                    },
                                    "skip_validation": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Skip validation of the converted document",
                                    },
                                },
                                "required": ["file"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful conversion",
                        "content": {
                            "application/json": {"schema": {"type": "object"}},
                            "application/yaml": {"schema": {"type": "object"}},
                        },
                    },
                    "400": {
                        "description": "Invalid input",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"detail": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "422": {
                        "description": "Validation error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "loc": {
                                                        "type": "array",
                                                        "items": {
                                                            "oneOf": [
                                                                {"type": "string"},
                                                                {"type": "integer"},
                                                            ]
                                                        },
                                                    },
                                                    "msg": {"type": "string"},
                                                    "type": {"type": "string"},
                                                },
                                            },
                                        }
                                    },
                                }
                            }
                        },
                    },
                },
            }
        },
    },
    "components": {"schemas": {}},
}
