"""Module for JSON schema definitions."""

from har_oa3_converter.schemas.json_schemas import (
    HAR_SCHEMA,
    HOPPSCOTCH_SCHEMA,
    OPENAPI3_SCHEMA,
    POSTMAN_SCHEMA,
    SWAGGER_SCHEMA,
    get_schema,
)

__all__ = [
    "HAR_SCHEMA",
    "OPENAPI3_SCHEMA",
    "SWAGGER_SCHEMA",
    "POSTMAN_SCHEMA",
    "HOPPSCOTCH_SCHEMA",
    "get_schema",
]
