"""Converter from Hoppscotch Collection to OpenAPI 3."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.utils.file_handler import FileHandler


class HoppscotchToOpenApi3Converter(FormatConverter):
    """Converter from Hoppscotch Collection to OpenAPI 3."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "hoppscotch"

    @classmethod
    def get_target_format(cls) -> str:
        """Get the target format this converter produces.

        Returns:
            Target format name
        """
        return "openapi3"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert Hoppscotch Collection to OpenAPI 3.

        Args:
            source_path: Path to Hoppscotch Collection file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary

        Raises:
            ValueError: If the source file is not a valid Hoppscotch Collection
        """
        # Load the Hoppscotch Collection
        file_handler = FileHandler()
        hoppscotch_data = file_handler.load(source_path)

        # Validate it's a Hoppscotch Collection
        if not self._is_valid_hoppscotch_collection(hoppscotch_data):
            raise ValueError(
                f"The file {source_path} is not a valid Hoppscotch Collection"
            )

        # Convert to OpenAPI 3
        openapi3_data = self._convert_to_openapi3(hoppscotch_data, **options)

        # Save to file if target_path is provided
        if target_path:
            file_handler.save(openapi3_data, target_path)

        return openapi3_data

    def _is_valid_hoppscotch_collection(self, data: Dict[str, Any]) -> bool:
        """Check if the data is a valid Hoppscotch Collection.

        Args:
            data: The data to check

        Returns:
            True if the data is a valid Hoppscotch Collection, False otherwise
        """
        # Check if it has the basic structure of a Hoppscotch Collection
        if not isinstance(data, dict):
            return False

        # Check for version field
        if "v" not in data:
            return False

        # Check for name field
        if "name" not in data:
            return False

        # Check for folders and requests fields
        if "folders" not in data or "requests" not in data:
            return False

        return True

    def _convert_to_openapi3(
        self, hoppscotch_data: Dict[str, Any], **options
    ) -> Dict[str, Any]:
        """Convert Hoppscotch Collection to OpenAPI 3.

        Args:
            hoppscotch_data: Hoppscotch Collection data
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Initialize OpenAPI 3 structure
        title = options.get("title", hoppscotch_data.get("name", "API"))
        version = options.get("version", "1.0.0")
        description = options.get("description", "")

        openapi3 = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": description,
            },
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {},
            },
        }

        # Add servers if provided
        servers = options.get("servers")
        if servers:
            openapi3["servers"] = servers

        # Process collection auth
        self._process_collection_auth(hoppscotch_data, openapi3)

        # Process requests
        self._process_requests(hoppscotch_data, openapi3)

        # Process folders recursively
        for folder in hoppscotch_data.get("folders", []):
            self._process_folder(folder, openapi3, folder.get("name", ""))

        return openapi3

    def _process_collection_auth(
        self, collection: Dict[str, Any], openapi3: Dict[str, Any]
    ) -> None:
        """Process collection authentication and add to OpenAPI 3 security schemes.

        Args:
            collection: Hoppscotch Collection data
            openapi3: OpenAPI 3 specification
        """
        auth = collection.get("auth", {})
        auth_type = auth.get("authType")

        if not auth_type or auth_type == "none" or auth_type == "inherit":
            return

        if auth_type == "basic":
            openapi3["components"]["securitySchemes"]["basicAuth"] = {
                "type": "http",
                "scheme": "basic",
            }
        elif auth_type == "bearer":
            openapi3["components"]["securitySchemes"]["bearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
            }
        elif auth_type == "oauth-2":
            grant_type_info = auth.get("grantTypeInfo", {})
            grant_type = grant_type_info.get("grantType")

            flows = {}
            if grant_type == "AUTHORIZATION_CODE":
                flows["authorizationCode"] = {
                    "authorizationUrl": grant_type_info.get("authUrl", ""),
                    "tokenUrl": grant_type_info.get("tokenUrl", ""),
                    "scopes": self._parse_oauth2_scopes(
                        grant_type_info.get("scopes", "")
                    ),
                }
            elif grant_type == "CLIENT_CREDENTIALS":
                flows["clientCredentials"] = {
                    "tokenUrl": grant_type_info.get("tokenUrl", ""),
                    "scopes": self._parse_oauth2_scopes(
                        grant_type_info.get("scopes", "")
                    ),
                }
            elif grant_type == "PASSWORD":
                flows["password"] = {
                    "tokenUrl": grant_type_info.get("tokenUrl", ""),
                    "scopes": self._parse_oauth2_scopes(
                        grant_type_info.get("scopes", "")
                    ),
                }
            elif grant_type == "IMPLICIT":
                flows["implicit"] = {
                    "authorizationUrl": grant_type_info.get("authUrl", ""),
                    "scopes": self._parse_oauth2_scopes(
                        grant_type_info.get("scopes", "")
                    ),
                }

            openapi3["components"]["securitySchemes"]["oauth2"] = {
                "type": "oauth2",
                "flows": flows,
            }
        elif auth_type == "api-key":
            key = auth.get("key", "api_key")
            in_location = "header"
            if auth.get("addTo") == "QUERY_PARAMS":
                in_location = "query"

            openapi3["components"]["securitySchemes"][key] = {
                "type": "apiKey",
                "name": key,
                "in": in_location,
            }

    def _parse_oauth2_scopes(self, scopes_str: str) -> Dict[str, str]:
        """Parse OAuth2 scopes string into a dictionary.

        Args:
            scopes_str: Space-separated scopes string

        Returns:
            Dictionary of scopes
        """
        scopes: Dict[str, str] = {}
        if not scopes_str:
            return scopes

        for scope in scopes_str.split():
            scopes[scope] = ""

        return scopes

    def _process_requests(
        self, collection: Dict[str, Any], openapi3: Dict[str, Any], tag: str = ""
    ) -> None:
        """Process requests in the collection and add to OpenAPI 3 paths.

        Args:
            collection: Hoppscotch Collection data
            openapi3: OpenAPI 3 specification
            tag: Tag to add to the operations
        """
        for request in collection.get("requests", []):
            self._process_request(request, openapi3, tag)

    def _process_folder(
        self, folder: Dict[str, Any], openapi3: Dict[str, Any], parent_tag: str = ""
    ) -> None:
        """Process a folder in the collection recursively.

        Args:
            folder: Hoppscotch Collection folder data
            openapi3: OpenAPI 3 specification
            parent_tag: Parent tag to add to the operations
        """
        folder_name = folder.get("name", "")
        tag = folder_name
        if parent_tag:
            tag = f"{parent_tag}/{folder_name}"

        # Process requests in this folder
        self._process_requests(folder, openapi3, tag)

        # Process sub-folders recursively
        for subfolder in folder.get("folders", []):
            self._process_folder(subfolder, openapi3, tag)

    def _process_request(
        self, request: Dict[str, Any], openapi3: Dict[str, Any], tag: str = ""
    ) -> None:
        """Process a request and add to OpenAPI 3 paths.

        Args:
            request: Hoppscotch request data
            openapi3: OpenAPI 3 specification
            tag: Tag to add to the operation
        """
        method = request.get("method", "GET").lower()
        url = request.get("endpoint", "")
        name = request.get("name", "")

        # Skip if URL is empty
        if not url:
            return

        # Extract path parameters from URL
        path, path_params = self._extract_path_params(url)

        # Initialize path if it doesn't exist
        if path not in openapi3["paths"]:
            openapi3["paths"][path] = {}

        # Initialize operation
        operation = {
            "summary": name,
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                }
            },
        }

        # Add tags if provided
        if tag:
            operation["tags"] = [tag]

        # Add path parameters
        for param in path_params:
            operation["parameters"].append(
                {
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": {
                        "type": "string",
                    },
                }
            )

        # Add query parameters
        for param in request.get("params", []):
            # Ensure param is a dict before accessing get method
            if not isinstance(param, dict):
                continue

            if not param.get("key"):
                continue

            if not param.get("active", True):
                continue

            operation["parameters"].append(
                {
                    "name": param.get("key", ""),
                    "in": "query",
                    "required": param.get("required", False),
                    "schema": {
                        "type": "string",
                        "default": param.get("value", ""),
                    },
                }
            )

        # Add headers
        for header in request.get("headers", []):
            # Ensure header is a dict before accessing get method
            if not isinstance(header, dict):
                continue

            if not header.get("key"):
                continue

            if not header.get("active", True):
                continue

            operation["parameters"].append(
                {
                    "name": header.get("key", ""),
                    "in": "header",
                    "required": header.get("required", False),
                    "schema": {
                        "type": "string",
                        "default": header.get("value", ""),
                    },
                }
            )

        # Add request body
        body = request.get("body", {})
        body_type = body.get("contentType", "")

        if body and method in ["post", "put", "patch"]:
            request_body: Dict[str, Any] = {
                "content": {},
            }

            if body_type == "application/json":
                json_data = body.get("body", "")
                if isinstance(json_data, str) and json_data:
                    try:
                        # Try to parse as JSON to create a schema
                        json_obj = json.loads(json_data)
                        schema = self._generate_json_schema(json_obj)
                        request_body["content"]["application/json"] = {
                            "schema": schema,
                        }
                    except json.JSONDecodeError:
                        # If not valid JSON, use string
                        request_body["content"]["application/json"] = {
                            "schema": {
                                "type": "string",
                                "example": json_data,
                            },
                        }
            elif body_type == "multipart/form-data":
                form_data = {}
                for item in body.get("body", []):
                    if not item.get("key") or not item.get("active", True):
                        continue
                    form_data[item.get("key", "")] = {
                        "type": "string",
                        "example": item.get("value", ""),
                    }

                if form_data:
                    request_body["content"]["multipart/form-data"] = {
                        "schema": {
                            "type": "object",
                            "properties": form_data,
                        },
                    }
            elif body_type == "application/x-www-form-urlencoded":
                form_data = {}
                for item in body.get("body", []):
                    if not item.get("key") or not item.get("active", True):
                        continue
                    form_data[item.get("key", "")] = {
                        "type": "string",
                        "example": item.get("value", ""),
                    }

                if form_data:
                    request_body["content"]["application/x-www-form-urlencoded"] = {
                        "schema": {
                            "type": "object",
                            "properties": form_data,
                        },
                    }
            elif body_type == "text/plain":
                request_body["content"]["text/plain"] = {
                    "schema": {
                        "type": "string",
                        "example": body.get("body", ""),
                    },
                }
            elif body_type:
                # For other content types, use string
                request_body["content"][body_type] = {
                    "schema": {
                        "type": "string",
                        "example": body.get("body", ""),
                    },
                }

            if request_body["content"]:
                operation["requestBody"] = request_body

        # Process authentication
        self._process_request_auth(request, operation, openapi3)

        # Add operation to path
        openapi3["paths"][path][method] = operation

    def _extract_path_params(self, url: str) -> Tuple[str, List[str]]:
        """Extract path parameters from URL.

        Args:
            url: URL to extract path parameters from

        Returns:
            Tuple of (path, path_parameters)
        """
        # Remove query string if present
        if "?" in url:
            url = url.split("?")[0]

        # Parse URL to extract path
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        path = parsed_url.path

        # If path is empty but we have a netloc, use the netloc as the path
        # This handles cases where the URL doesn't have a path component
        if not path and parsed_url.netloc:
            path = "/"

        # Split path into segments
        segments = path.split("/")
        path_params = []

        # Process each segment
        for i, segment in enumerate(segments):
            # Check if segment is a path parameter (starts with : or {})
            if segment.startswith(":"):
                param_name = segment[1:]
                segments[i] = "{" + param_name + "}"
                path_params.append(param_name)
            elif segment.startswith("{") and segment.endswith("}"):
                param_name = segment[1:-1]
                path_params.append(param_name)

        # Reconstruct path
        path = "/".join(segments)

        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        return path, path_params

    def _process_request_auth(
        self,
        request: Dict[str, Any],
        operation: Dict[str, Any],
        openapi3: Dict[str, Any],
    ) -> None:
        """Process request authentication and add to operation.

        Args:
            request: Hoppscotch request data
            operation: OpenAPI 3 operation object
            openapi3: OpenAPI 3 specification
        """
        auth = request.get("auth", {})
        auth_type = auth.get("authType")

        if not auth_type or auth_type == "none" or not auth.get("authActive", False):
            return

        if auth_type == "inherit":
            # Inherit from collection, already processed
            return

        security: List[Dict[str, List[str]]] = []

        if auth_type == "basic":
            security_name = "basicAuth"
            if security_name not in openapi3["components"]["securitySchemes"]:
                openapi3["components"]["securitySchemes"][security_name] = {
                    "type": "http",
                    "scheme": "basic",
                }
            security.append({security_name: []})
        elif auth_type == "bearer":
            security_name = "bearerAuth"
            if security_name not in openapi3["components"]["securitySchemes"]:
                openapi3["components"]["securitySchemes"][security_name] = {
                    "type": "http",
                    "scheme": "bearer",
                }
            security.append({security_name: []})
        elif auth_type == "oauth-2":
            security_name = "oauth2"
            if security_name not in openapi3["components"]["securitySchemes"]:
                # Process OAuth2 configuration
                grant_type_info = auth.get("grantTypeInfo", {})
                grant_type = grant_type_info.get("grantType")

                flows = {}
                if grant_type == "AUTHORIZATION_CODE":
                    flows["authorizationCode"] = {
                        "authorizationUrl": grant_type_info.get("authUrl", ""),
                        "tokenUrl": grant_type_info.get("tokenUrl", ""),
                        "scopes": self._parse_oauth2_scopes(
                            grant_type_info.get("scopes", "")
                        ),
                    }
                elif grant_type == "CLIENT_CREDENTIALS":
                    flows["clientCredentials"] = {
                        "tokenUrl": grant_type_info.get("tokenUrl", ""),
                        "scopes": self._parse_oauth2_scopes(
                            grant_type_info.get("scopes", "")
                        ),
                    }
                elif grant_type == "PASSWORD":
                    flows["password"] = {
                        "tokenUrl": grant_type_info.get("tokenUrl", ""),
                        "scopes": self._parse_oauth2_scopes(
                            grant_type_info.get("scopes", "")
                        ),
                    }
                elif grant_type == "IMPLICIT":
                    flows["implicit"] = {
                        "authorizationUrl": grant_type_info.get("authUrl", ""),
                        "scopes": self._parse_oauth2_scopes(
                            grant_type_info.get("scopes", "")
                        ),
                    }

                openapi3["components"]["securitySchemes"][security_name] = {
                    "type": "oauth2",
                    "flows": flows,
                }
            security.append({security_name: []})
        elif auth_type == "api-key":
            key = auth.get("key", "api_key")
            security_name = key
            in_location = "header"
            if auth.get("addTo") == "QUERY_PARAMS":
                in_location = "query"

            if security_name not in openapi3["components"]["securitySchemes"]:
                openapi3["components"]["securitySchemes"][security_name] = {
                    "type": "apiKey",
                    "name": key,
                    "in": in_location,
                }
            security.append({security_name: []})

        if security:
            operation["security"] = security

    def _generate_json_schema(self, json_obj: Any) -> Dict[str, Any]:
        """Generate a JSON Schema from a JSON object.

        Args:
            json_obj: JSON object to generate schema from

        Returns:
            JSON Schema
        """
        if json_obj is None:
            return {"type": "null"}
        elif isinstance(json_obj, bool):
            return {"type": "boolean"}
        elif isinstance(json_obj, int):
            return {"type": "integer"}
        elif isinstance(json_obj, float):
            return {"type": "number"}
        elif isinstance(json_obj, str):
            return {"type": "string"}
        elif isinstance(json_obj, list):
            if not json_obj:
                return {"type": "array", "items": {}}
            # Use the first item as a sample
            return {
                "type": "array",
                "items": self._generate_json_schema(json_obj[0]),
            }
        elif isinstance(json_obj, dict):
            properties = {}
            for key, value in json_obj.items():
                properties[key] = self._generate_json_schema(value)
            return {
                "type": "object",
                "properties": properties,
            }
        else:
            return {"type": "string"}
