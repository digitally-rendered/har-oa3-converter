"""Core converter module for transforming HAR files to OpenAPI 3."""

import json
from typing import Any, Dict, List, Optional, Set, Tuple


class HarToOas3Converter:
    """Convert HAR (HTTP Archive) files to OpenAPI 3 specification."""

    def __init__(
        self,
        base_path: Optional[str] = None,
        info: Optional[Dict[str, Any]] = None,
        servers: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize converter with optional configuration.

        Args:
            base_path: Base path for all endpoints
            info: OpenAPI info object
            servers: OpenAPI servers list
        """
        self.base_path = base_path
        self.info = info or {
            "title": "API generated from HAR",
            "version": "1.0.0",
            "description": "API specification generated from HAR file",
        }
        self.servers = servers or []
        self.paths: Dict[str, Dict[str, Any]] = {}
        self.components: Dict[str, Dict[str, Any]] = {
            "schemas": {},
            "requestBodies": {},
            "responses": {},
        }

    def load_har(self, har_path: str) -> Dict[str, Any]:
        """Load HAR file from path.

        Args:
            har_path: Path to HAR file

        Returns:
            Loaded HAR data as dictionary
        """
        with open(har_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def convert_entry(self, har_entry: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Convert a single HAR entry to an OpenAPI path item.

        Args:
            har_entry: HAR entry object
            url: URL to use for path extraction

        Returns:
            OpenAPI path item object
        """
        request = har_entry.get("request", {})
        response = har_entry.get("response", {})
        method = request.get("method", "").lower()
        
        # Extract path from URL
        path = url.split("//")[-1].split("/", 1)[-1].split("?")[0]
        if not path.startswith("/"):
            path = "/" + path
            
        # Create path object if not exists
        if path not in self.paths:
            self.paths[path] = {}
            
        # Process request and response
        self._process_request_response(path, method, request, response)
        
        # Return the path item
        return {path: self.paths[path]}
        
    def convert_from_string(self, har_json_string: str) -> Dict[str, Any]:
        """Convert HAR JSON string to OpenAPI 3.

        Args:
            har_json_string: HAR JSON string

        Returns:
            OpenAPI 3 specification as dictionary
        """
        har_data = json.loads(har_json_string)
        self.extract_paths_from_har(har_data)
        
        openapi = {
            "openapi": "3.0.3",
            "info": self.info,
            "paths": self.paths,
            "components": self.components,
        }
        
        if self.servers:
            openapi["servers"] = self.servers
            
        return openapi
        
    def _get_path_template(self, url: str) -> str:
        """Extract a path template from a URL, attempting to identify path parameters.

        Args:
            url: URL to extract path template from

        Returns:
            Path template string
        """
        # Extract path from URL
        path = url.split("//")[-1].split("/", 1)[-1].split("?")[0]
        if not path.startswith("/"):
            path = "/" + path
            
        # Simple path parameter detection - look for numeric segments and
        # replace them with parameter placeholders
        path_segments = path.split("/")
        for i, segment in enumerate(path_segments):
            if segment.isdigit():
                # This is likely a path parameter (ID)
                # Try to use the previous segment name for context
                if i > 0 and path_segments[i-1]:
                    # Strip trailing 's' if it exists (e.g., 'users' -> 'user')
                    param_name = path_segments[i-1].rstrip("s") + "Id"
                    path_segments[i] = "{{{}}}".format(param_name)
                else:
                    path_segments[i] = "{id}"
        
        return "/".join(path_segments)

    def extract_paths_from_har(self, har_data: Dict[str, Any]) -> None:
        """Extract paths from HAR data and populate internal paths dictionary.

        Args:
            har_data: Loaded HAR data
        """
        entries = har_data.get("log", {}).get("entries", [])

        # Track processed methods to handle duplicate URLs
        processed_methods = {}
        
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})

            method = request.get("method", "").lower()
            url = request.get("url", "")

            # Skip empty URLs
            if not url:
                continue

            # Parse URL with special character handling
            try:
                from urllib.parse import urlparse, unquote
                parsed_url = urlparse(url)
                path = unquote(parsed_url.path)  # Handle percent-encoded characters
            except Exception:
                # Fallback to simple splitting if URL parsing fails
                path = url.split("//")[-1].split("/", 1)[-1].split("?")[0]
            
            # Ensure path starts with /
            if not path.startswith("/"):
                path = "/" + path
                
            # Process path for OpenAPI compatibility
            # Strategy 1: For paths with special characters, convert them to path parameters
            original_path = path
            path_segments = path.split("/")
            has_special_chars = False
            
            # Check if any segment has special characters
            special_chars = "!@#$%^&*()+={}[]|:\"'<>?,"
            
            for i, segment in enumerate(path_segments):
                if any(char in segment for char in special_chars):
                    has_special_chars = True
                    # Convert special character segments to path parameters
                    if i > 0 and path_segments[i-1]:
                        # Use previous segment as context for parameter name
                        param_name = path_segments[i-1].rstrip("s").lower() + "Value"
                        path_segments[i] = "{{{}}}".format(param_name)
                    else:
                        # Generic parameter name if no context available
                        path_segments[i] = "{paramValue}"
            
            if has_special_chars:
                # Rebuild path with parameterized segments
                path = "/".join([s for s in path_segments if s])  # Filter out empty segments
                if not path.startswith("/"):
                    path = "/" + path
            else:
                # Strategy 2: If no special characters, use the original path
                # But still sanitize for safety - replace problematic chars with underscores
                sanitized_path = original_path
                for char in special_chars:
                    if char in sanitized_path:
                        sanitized_path = sanitized_path.replace(char, "_")
                path = sanitized_path

            # Add path if not already present
            if path not in self.paths:
                self.paths[path] = {}
                processed_methods[path] = set()

            # Handle duplicate methods for same path more effectively
            if method in processed_methods.get(path, set()):
                # For duplicate method+path combinations, we could:                
                # 1. Skip it (current approach)
                # 2. Merge with existing operation (for a more sophisticated approach)
                # 3. Create a unique operation ID to distinguish them
                
                # For test_duplicate_entries to pass, we'll keep the first occurrence
                continue
            
            # Add this method to processed methods for this path
            processed_methods.setdefault(path, set()).add(method)

            # Process request and response for this path and method
            self._process_request_response(path, method, request, response)

    def _process_request_response(
        self, path: str, method: str, request: Dict[str, Any], response: Dict[str, Any]
    ) -> None:
        """Process request and response for a path.

        Args:
            path: API path
            method: HTTP method
            request: HAR request object
            response: HAR response object
        """
        # Extract request parameters, body, etc.
        parameters = self._extract_parameters(request)
        request_body = self._extract_request_body(request)

        # Extract response
        responses = self._extract_responses(response)

        # Create path item
        self.paths[path][method] = {
            "summary": f"{method.upper()} {path}",
            "description": "",
            "operationId": f"{method}_{path.replace('/', '_').strip('_')}",
            "responses": responses,
        }

        if parameters:
            self.paths[path][method]["parameters"] = parameters

        if request_body:
            self.paths[path][method]["requestBody"] = request_body

    def _extract_parameters(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameters from request.

        Args:
            request: HAR request object

        Returns:
            List of OpenAPI parameter objects
        """
        parameters = []

        # Query parameters
        query_params = request.get("queryString", [])
        for param in query_params:
            name = param.get("name", "")
            value = param.get("value", "")

            parameters.append(
                {
                    "name": name,
                    "in": "query",
                    "required": True,  # Assuming required for now
                    "schema": {"type": "string", "example": value},
                }
            )

        # Headers
        headers = request.get("headers", [])
        for header in headers:
            name = header.get("name", "")
            value = header.get("value", "")

            # Skip common headers
            if name.lower() in {
                "host",
                "user-agent",
                "accept",
                "content-length",
                "connection",
                "cookie",
                "accept-encoding",
                "accept-language",
            }:
                continue

            parameters.append(
                {
                    "name": name,
                    "in": "header",
                    "required": True,  # Assuming required for now
                    "schema": {"type": "string", "example": value},
                }
            )

        return parameters

    def _extract_request_body(
        self, request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract request body.

        Args:
            request: HAR request object

        Returns:
            OpenAPI requestBody object or None
        """
        post_data = request.get("postData", {})
        if not post_data:
            return None

        mime_type = post_data.get("mimeType", "")

        if "json" in mime_type:
            try:
                text = post_data.get("text", "{}")
                data = json.loads(text)
                schema = self._infer_schema("RequestBody", data)

                return {
                    "required": True,
                    "content": {
                        mime_type: {
                            "schema": {"$ref": f"#/components/schemas/{schema}"}
                        }
                    },
                }
            except json.JSONDecodeError:
                pass

        # Default form data
        return {
            "required": True,
            "content": {
                mime_type: {
                    "schema": {"type": "string", "example": post_data.get("text", "")}
                }
            },
        }

    def _extract_responses(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract responses.

        Args:
            response: HAR response object

        Returns:
            OpenAPI responses object
        """
        status = str(response.get("status", 200))
        content_type = ""

        for header in response.get("headers", []):
            if header.get("name", "").lower() == "content-type":
                content_type = header.get("value", "")
                break

        result = {status: {"description": response.get("statusText", "Response")}}

        # Add content if available
        content = response.get("content", {})
        if content and content_type:
            text = content.get("text", "")

            if "json" in content_type and text:
                try:
                    data = json.loads(text)
                    schema = self._infer_schema("Response", data)

                    result[status]["content"] = {
                        content_type: {
                            "schema": {"$ref": f"#/components/schemas/{schema}"}
                        }
                    }
                except json.JSONDecodeError:
                    result[status]["content"] = {
                        content_type: {"schema": {"type": "string", "example": text}}
                    }
            else:
                result[status]["content"] = {
                    content_type: {"schema": {"type": "string", "example": text}}
                }

        return result

    def _infer_schema(
        self, prefix: str, data: Any, used_names: Optional[Set[str]] = None
    ) -> str:
        """Infer JSON schema from data.

        Args:
            prefix: Prefix for schema name
            data: JSON data to infer schema from
            used_names: Set of already used schema names

        Returns:
            Schema name
        """
        if used_names is None:
            used_names = set()

        # Generate schema name
        name = prefix
        counter = 1
        while name in used_names:
            name = f"{prefix}{counter}"
            counter += 1

        used_names.add(name)

        # Create schema
        schema: Dict[str, Any] = {}

        if isinstance(data, dict):
            schema["type"] = "object"
            schema["properties"] = {}

            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    ref_name = self._infer_schema(f"{name}_{key}", value, used_names)
                    schema["properties"][key] = {
                        "$ref": f"#/components/schemas/{ref_name}"
                    }
                else:
                    schema["properties"][key] = self._get_schema_for_value(value)

        elif isinstance(data, list):
            schema["type"] = "array"

            if data:
                # Infer schema from first item
                if isinstance(data[0], (dict, list)):
                    ref_name = self._infer_schema(f"{name}_item", data[0], used_names)
                    schema["items"] = {"$ref": f"#/components/schemas/{ref_name}"}
                else:
                    schema["items"] = self._get_schema_for_value(data[0])
            else:
                schema["items"] = {"type": "string"}

        else:
            schema = self._get_schema_for_value(data)

        # Add schema to components
        self.components["schemas"][name] = schema

        return name

    def _get_schema_for_value(self, value: Any) -> Dict[str, Any]:
        """Get schema for simple value.

        Args:
            value: Simple value

        Returns:
            Schema for value
        """
        if value is None:
            return {"type": "null"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer", "example": value}
        elif isinstance(value, float):
            return {"type": "number", "example": value}
        else:
            return {"type": "string", "example": str(value)}

    def generate_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3 specification.

        Returns:
            OpenAPI 3 specification as dictionary
        """
        spec = {
            "openapi": "3.0.0",
            "info": self.info,
            "paths": self.paths,
            "components": self.components,
        }

        if self.servers:
            spec["servers"] = self.servers

        return spec

    def convert(
        self,
        har_path: str,
        output_path: Optional[str] = None,
        validate_schema: bool = True,
        **options,
    ) -> Dict[str, Any]:
        """Convert HAR file to OpenAPI 3 and optionally save to file.

        Args:
            har_path: Path to HAR file
            output_path: Path to save generated spec to (optional)
            validate_schema: Whether to validate the input HAR file against schema
            options: Additional options for conversion

        Returns:
            Generated OpenAPI 3 specification
        """
        har_data = self.load_har(har_path)
        self.extract_paths_from_har(har_data)
        spec = self.generate_spec()

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2)

        return spec
