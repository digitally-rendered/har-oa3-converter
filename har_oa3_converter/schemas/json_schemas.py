"""Central repository for all JSON Schema definitions used in the application.

API endpoints will use these schema documents to interpret parameter objects.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# HAR Schema (HTTP Archive format)
HAR_SCHEMA = {
    "type": "object",
    "required": ["log"],
    "properties": {
        "log": {
            "type": "object",
            "required": ["version", "entries"],
            "properties": {
                "version": {"type": "string"},
                "creator": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                    },
                },
                "entries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "request": {
                                "type": "object",
                                "required": ["method", "url"],
                                "properties": {
                                    "method": {"type": "string"},
                                    "url": {"type": "string"},
                                    "headers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "value"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "value": {"type": "string"},
                                            },
                                        },
                                    },
                                    "queryString": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "value"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "value": {"type": "string"},
                                            },
                                        },
                                    },
                                    "postData": {
                                        "type": "object",
                                        "properties": {
                                            "mimeType": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                    },
                                },
                            },
                            "response": {
                                "type": "object",
                                "required": ["status"],
                                "properties": {
                                    "status": {"type": "integer"},
                                    "statusText": {"type": "string"},
                                    "headers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "value"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "value": {"type": "string"},
                                            },
                                        },
                                    },
                                    "content": {
                                        "type": "object",
                                        "properties": {
                                            "mimeType": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
    },
}

# OpenAPI 3.0 Schema (simplified version)
OPENAPI3_SCHEMA = {
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string"},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "paths": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "operationId": {"type": "string"},
                        "parameters": {"type": "array", "items": {"type": "object"}},
                        "requestBody": {"type": "object"},
                        "responses": {"type": "object"},
                    },
                },
            },
        },
        "components": {"type": "object"},
        "servers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
    },
}

# Swagger 2.0 Schema (simplified version)
SWAGGER_SCHEMA = {
    "type": "object",
    "required": ["swagger", "info", "paths"],
    "properties": {
        "swagger": {"type": "string"},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "basePath": {"type": "string"},
        "paths": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "operationId": {"type": "string"},
                        "parameters": {"type": "array", "items": {"type": "object"}},
                        "responses": {"type": "object"},
                    },
                },
            },
        },
        "definitions": {"type": "object"},
        "host": {"type": "string"},
        "schemes": {"type": "array", "items": {"type": "string"}},
    },
}

# Postman Collection Schema (simplified version)
POSTMAN_SCHEMA = {
    "type": "object",
    "required": ["info", "item"],
    "properties": {
        "info": {
            "type": "object",
            "required": ["_postman_id", "name", "schema"],
            "properties": {
                "_postman_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "schema": {"type": "string"},
            },
        },
        "item": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["name", "request"],
                        "properties": {
                            "name": {"type": "string"},
                            "request": {
                                "type": "object",
                                "properties": {
                                    "method": {"type": "string"},
                                    "url": {
                                        "oneOf": [
                                            {"type": "string"},
                                            {"type": "object"},
                                        ]
                                    },
                                    "header": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                    },
                                    "body": {"type": "object"},
                                },
                            },
                            "response": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                    {
                        "type": "object",
                        "required": ["name", "item"],
                        "properties": {
                            "name": {"type": "string"},
                            "item": {"type": "array"},
                        },
                    },
                ]
            },
        },
    },
}


# Hoppscotch Schema (loaded from file)
def load_hoppscotch_schema() -> Dict[str, Any]:
    """Load the Hoppscotch schema from the JSON file.

    Returns:
        Hoppscotch schema definition
    """
    schema_path = Path(__file__).parent / "hoppscotch_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load the Hoppscotch schema
try:
    HOPPSCOTCH_SCHEMA = load_hoppscotch_schema()
except Exception as e:
    print(f"Warning: Failed to load Hoppscotch schema: {e}")
    HOPPSCOTCH_SCHEMA = {
        "type": "object",
        "required": ["v", "name", "folders", "requests"],
        "properties": {
            "v": {"type": ["integer", "string"]},
            "name": {"type": "string"},
            "folders": {"type": "array"},
            "requests": {"type": "array"},
        },
    }


def get_schema(schema_name: str) -> Optional[Dict[str, Any]]:
    """Get schema by name.

    Args:
        schema_name: Name of schema to get

    Returns:
        Schema definition or None if not found
    """
    schemas = {
        "har": HAR_SCHEMA,
        "openapi3": OPENAPI3_SCHEMA,
        "swagger": SWAGGER_SCHEMA,
        "postman": POSTMAN_SCHEMA,
        "hoppscotch": HOPPSCOTCH_SCHEMA,
    }
    return schemas.get(schema_name)
