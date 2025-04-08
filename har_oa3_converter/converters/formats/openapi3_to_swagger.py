"""Converter from OpenAPI 3 to Swagger 2 (OpenAPI 2)."""

import json
import os
from typing import Any, Dict, List, Optional

import yaml

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.utils.file_handler import FileHandler


class OpenApi3ToSwaggerConverter(FormatConverter[Dict[str, Any], Dict[str, Any]]):
    """Converter from OpenAPI 3 to Swagger 2 (OpenAPI 2)."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "openapi3"

    @classmethod
    def get_target_format(cls) -> str:
        """Get the target format this converter produces.

        Returns:
            Target format name
        """
        return "swagger"

    def convert_data(
        self, source_data: Dict[str, Any], **options: Any
    ) -> Dict[str, Any]:
        """Convert OpenAPI 3 to Swagger 2.

        Args:
            source_data: OpenAPI 3 data as dictionary
            options: Additional options

        Returns:
            Swagger specification as dictionary
        """
        # Convert OpenAPI 3 to Swagger 2
        swagger = self._convert_openapi3_to_swagger2(source_data)

        # Return the converted data
        return swagger

    def _convert_openapi3_to_swagger2(self, openapi3: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI 3 specification to Swagger 2.

        This is a simplified conversion for demonstration purposes.
        A complete converter would handle many more details.

        Args:
            openapi3: OpenAPI 3 specification

        Returns:
            Swagger 2 specification
        """
        # Create base Swagger 2 structure
        swagger = {
            "swagger": "2.0",
            "info": openapi3.get("info", {"title": "API", "version": "1.0.0"}),
            "paths": {},
            "definitions": {},
        }

        # Convert servers to host, basePath, schemes
        servers = openapi3.get("servers", [])
        if servers and isinstance(servers, list) and len(servers) > 0:
            server_url = servers[0].get("url", "")
            if server_url:
                # Extract scheme, host, and basePath from server URL
                import urllib.parse

                parsed_url = urllib.parse.urlparse(server_url)
                swagger["host"] = parsed_url.netloc
                swagger["basePath"] = parsed_url.path or "/"
                swagger["schemes"] = (
                    [parsed_url.scheme] if parsed_url.scheme else ["https"]
                )

        # Convert paths
        paths = openapi3.get("paths", {})
        for path, path_item in paths.items():
            swagger["paths"][path] = {}

            # Process each HTTP method
            for method, operation in path_item.items():
                if method in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "options",
                    "head",
                    "patch",
                ]:
                    # Convert operation
                    swagger_operation = {
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "operationId": operation.get("operationId", ""),
                        "tags": operation.get("tags", []),
                        "parameters": [],
                        "responses": {},
                    }

                    # Convert parameters
                    parameters = operation.get("parameters", [])
                    for param in parameters:
                        swagger_param = {
                            "name": param.get("name", ""),
                            "in": param.get("in", ""),
                            "description": param.get("description", ""),
                            "required": param.get("required", False),
                        }

                        # Convert schema to type, format
                        if "schema" in param:
                            schema = param["schema"]
                            if "$ref" in schema:
                                swagger_param["schema"] = self._convert_schema_ref(
                                    schema
                                )
                            else:
                                swagger_param["type"] = schema.get("type", "string")
                                if "format" in schema:
                                    swagger_param["format"] = schema["format"]

                        swagger_operation["parameters"].append(swagger_param)

                    # Convert requestBody to parameter
                    if "requestBody" in operation:
                        request_body = operation["requestBody"]
                        content = request_body.get("content", {})

                        # Handle application/json content type
                        if "application/json" in content:
                            json_content = content["application/json"]
                            if "schema" in json_content:
                                body_param = {
                                    "name": "body",
                                    "in": "body",
                                    "required": request_body.get("required", False),
                                    "schema": self._convert_schema(
                                        json_content["schema"]
                                    ),
                                }
                                swagger_operation["parameters"].append(body_param)

                    # Convert responses
                    responses = operation.get("responses", {})
                    for status_code, response in responses.items():
                        swagger_response = {
                            "description": response.get("description", ""),
                        }

                        # Convert response schema
                        if "content" in response:
                            content = response["content"]
                            if "application/json" in content:
                                json_content = content["application/json"]
                                if "schema" in json_content:
                                    swagger_response["schema"] = self._convert_schema(
                                        json_content["schema"]
                                    )

                        swagger_operation["responses"][status_code] = swagger_response

                    # Add operation to path
                    swagger["paths"][path][method] = swagger_operation

        # Convert components/schemas to definitions
        components = openapi3.get("components", {})
        schemas = components.get("schemas", {})
        for schema_name, schema in schemas.items():
            swagger["definitions"][schema_name] = self._convert_schema(schema)

        return swagger

    def _convert_schema_ref(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema references from OpenAPI 3 format to Swagger 2.

        Args:
            schema: Schema object possibly containing references

        Returns:
            Converted schema
        """
        if "$ref" in schema:
            ref = schema["$ref"]
            # Convert #/components/schemas/ to #/definitions/
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.replace("#/components/schemas/", "")
                return {"$ref": f"#/definitions/{schema_name}"}
        return schema

    def _convert_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema object from OpenAPI 3 format to Swagger 2.

        Args:
            schema: Schema object

        Returns:
            Converted schema
        """
        if not schema:
            return {}

        result = {}

        # Handle $ref
        if "$ref" in schema:
            return self._convert_schema_ref(schema)

        # Copy basic properties
        for prop in [
            "type",
            "format",
            "title",
            "description",
            "default",
            "multipleOf",
            "maximum",
            "exclusiveMaximum",
            "minimum",
            "exclusiveMinimum",
            "maxLength",
            "minLength",
            "pattern",
            "maxItems",
            "minItems",
            "uniqueItems",
            "maxProperties",
            "minProperties",
            "required",
            "enum",
        ]:
            if prop in schema:
                result[prop] = schema[prop]

        # Handle array items
        if "items" in schema and schema.get("type") == "array":
            result["items"] = self._convert_schema(schema["items"])

        # Handle properties for objects
        if "properties" in schema and schema.get("type") == "object":
            result["properties"] = {}
            for prop_name, prop_schema in schema["properties"].items():
                result["properties"][prop_name] = self._convert_schema(prop_schema)

        # Handle allOf, oneOf, anyOf
        if "allOf" in schema:
            # In Swagger 2, we can use allOf
            result["allOf"] = [self._convert_schema(s) for s in schema["allOf"]]
        elif "oneOf" in schema or "anyOf" in schema:
            # Swagger 2 doesn't support oneOf or anyOf directly
            # For simplicity, we'll just use the first schema as a fallback
            schemas_list = schema.get("oneOf", schema.get("anyOf", []))
            if schemas_list and len(schemas_list) > 0:
                first_schema = schemas_list[0]
                for prop_name, prop_value in self._convert_schema(first_schema).items():
                    result[prop_name] = prop_value

        return result
