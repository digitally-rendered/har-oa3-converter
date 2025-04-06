"""Format converter module for transforming between different API specification formats."""

import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

import yaml

from har_oa3_converter.converters.har_to_oas3 import HarToOas3Converter
from har_oa3_converter.converters.schema_validator import detect_format, validate_file
from har_oa3_converter.utils.file_handler import FileHandler


class FormatConverter(ABC):
    """Base abstract class for format converters."""

    @classmethod
    def get_name(cls) -> str:
        """Get the name of the converter.

        Returns:
            The name of the converter
        """
        return cls.__name__

    @classmethod
    @abstractmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        pass

    @classmethod
    @abstractmethod
    def get_target_format(cls) -> str:
        """Get the target format this converter produces.

        Returns:
            Target format name
        """
        pass

    @abstractmethod
    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert from source to target format.

        Args:
            source_path: Path to source file
            target_path: Path to target file (optional)
            options: Additional converter-specific options

        Returns:
            Converted data
        """
        pass


class HarToOpenApi3Converter(FormatConverter):
    """Converter from HAR to OpenAPI 3."""

    @classmethod
    def get_source_format(cls) -> str:
        return "har"

    @classmethod
    def get_target_format(cls) -> str:
        return "openapi3"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert HAR to OpenAPI 3.

        Args:
            source_path: Path to HAR file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Validate input file against HAR schema if validation is enabled
        validate_schema = options.pop("validate_schema", True)
        if validate_schema:
            is_valid, format_name, error = validate_file(source_path)
            if not is_valid:
                raise ValueError(f"Invalid HAR file: {error}")
            if format_name != "har":
                raise ValueError(f"Expected HAR file but detected {format_name}")
        info = {}
        if "title" in options:
            info["title"] = options["title"]
        if "version" in options:
            info["version"] = options["version"]
        if "description" in options:
            info["description"] = options["description"]

        servers = []
        if "servers" in options and options["servers"]:
            for server in options["servers"]:
                servers.append({"url": server})

        converter = HarToOas3Converter(
            base_path=options.get("base_path"),
            info=info or None,
            servers=servers or None,
        )

        # Pass validate_schema parameter to HarToOas3Converter
        return converter.convert(
            source_path, target_path, validate_schema=False
        )  # Validation already done above


class OpenApi3ToOpenApi3Converter(FormatConverter):
    """Converter for OpenAPI 3 to OpenAPI 3 (format-to-format conversion)."""

    @classmethod
    def get_source_format(cls) -> str:
        return "openapi3"

    @classmethod
    def get_target_format(cls) -> str:
        return "openapi3"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert OpenAPI 3 to OpenAPI 3 (format conversion only).

        Args:
            source_path: Path to OpenAPI 3 file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Validate input file against OpenAPI 3 schema if validation is enabled
        validate_schema = options.pop("validate_schema", True)
        if validate_schema:
            is_valid, format_name, error = validate_file(source_path)
            if not is_valid:
                raise ValueError(f"Invalid OpenAPI 3 file: {error}")
            if format_name != "openapi3":
                raise ValueError(f"Expected OpenAPI 3 file but detected {format_name}")
        # Load OpenAPI 3 file
        with open(source_path, "r", encoding="utf-8") as f:
            if source_path.endswith(".json"):
                openapi3 = json.load(f)
            else:
                openapi3 = yaml.safe_load(f)

        # Apply any options modifications
        if options.get("title") or options.get("version") or options.get("description"):
            if "info" not in openapi3:
                openapi3["info"] = {}

            if options.get("title"):
                openapi3["info"]["title"] = options["title"]

            if options.get("version"):
                openapi3["info"]["version"] = options["version"]

            if options.get("description"):
                openapi3["info"]["description"] = options["description"]

        # Add servers if provided
        if options.get("servers"):
            openapi3["servers"] = [{"url": server} for server in options["servers"]]

        # Save output if target path provided
        if target_path:
            with open(target_path, "w", encoding="utf-8") as f:
                if target_path.endswith(".json"):
                    json.dump(openapi3, f, indent=2)
                else:
                    yaml.dump(openapi3, f, default_flow_style=False)

        return openapi3


class OpenApi3ToSwaggerConverter(FormatConverter):
    """Converter from OpenAPI 3 to Swagger 2 (OpenAPI 2)."""

    @classmethod
    def get_source_format(cls) -> str:
        return "openapi3"

    @classmethod
    def get_target_format(cls) -> str:
        return "swagger"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert OpenAPI 3 to Swagger 2.

        Args:
            source_path: Path to OpenAPI 3 file
            target_path: Path to output Swagger file (optional)
            options: Additional options

        Returns:
            Swagger specification as dictionary
        """
        # Validate input file against OpenAPI 3 schema if validation is enabled
        validate_schema = options.pop("validate_schema", True)
        if validate_schema:
            is_valid, format_name, error = validate_file(source_path)
            if not is_valid:
                raise ValueError(f"Invalid OpenAPI 3 file: {error}")
            if format_name != "openapi3":
                raise ValueError(f"Expected OpenAPI 3 file but detected {format_name}")
        # Load OpenAPI 3 file
        with open(source_path, "r", encoding="utf-8") as f:
            if source_path.endswith(".json"):
                openapi3 = json.load(f)
            else:
                openapi3 = yaml.safe_load(f)

        # Convert OpenAPI 3 to Swagger 2
        swagger = self._convert_openapi3_to_swagger2(openapi3)

        # Save output if target path provided
        if target_path:
            with open(target_path, "w", encoding="utf-8") as f:
                if target_path.endswith(".json"):
                    json.dump(swagger, f, indent=2)
                else:
                    yaml.dump(swagger, f, default_flow_style=False)

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
        swagger = {
            "swagger": "2.0",
            "info": openapi3.get("info", {}),
            "paths": {},
            "definitions": {},
        }

        # Convert servers to host, basePath, schemes
        servers = openapi3.get("servers", [])
        if servers and "url" in servers[0]:
            url = servers[0]["url"]
            if "//" in url:
                scheme, rest = url.split("//", 1)
                swagger["schemes"] = [scheme.rstrip(":")]

                if "/" in rest:
                    host, path = rest.split("/", 1)
                    swagger["host"] = host
                    swagger["basePath"] = f"/{path}"
                else:
                    swagger["host"] = rest
                    swagger["basePath"] = "/"

        # Convert paths
        for path, methods in openapi3.get("paths", {}).items():
            swagger["paths"][path] = {}

            for method, operation in methods.items():
                new_operation = {
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operationId": operation.get("operationId", ""),
                    "parameters": [],
                    "responses": {},
                }

                # Convert parameters
                for param in operation.get("parameters", []):
                    # In OpenAPI 3, content is used, in Swagger 2 it's type/format
                    if "schema" in param:
                        schema = param["schema"]
                        new_param = {**param}
                        if "$ref" in schema:
                            ref = schema["$ref"].replace(
                                "#/components/schemas/", "#/definitions/"
                            )
                            new_param["schema"] = {"$ref": ref}
                        else:
                            new_param["type"] = schema.get("type", "string")
                            if "format" in schema:
                                new_param["format"] = schema["format"]
                        new_operation["parameters"].append(new_param)
                    else:
                        new_operation["parameters"].append(param)

                # Convert request body to parameter
                if "requestBody" in operation:
                    content = operation["requestBody"].get("content", {})
                    for content_type, content_schema in content.items():
                        schema = content_schema.get("schema", {})
                        body_param = {
                            "name": "body",
                            "in": "body",
                            "required": operation["requestBody"].get("required", False),
                            "schema": self._convert_schema_ref(schema),
                        }
                        new_operation["parameters"].append(body_param)
                        break

                # Convert responses
                for status, response in operation.get("responses", {}).items():
                    new_response = {"description": response.get("description", "")}

                    if "content" in response:
                        for content_type, content_schema in response["content"].items():
                            if "schema" in content_schema:
                                new_response["schema"] = self._convert_schema_ref(
                                    content_schema["schema"]
                                )
                            break

                    new_operation["responses"][status] = new_response

                # Add produces/consumes based on content types
                produces = []
                consumes = []

                if "requestBody" in operation:
                    for content_type in (
                        operation["requestBody"].get("content", {}).keys()
                    ):
                        consumes.append(content_type)

                for response in operation.get("responses", {}).values():
                    for content_type in response.get("content", {}).keys():
                        if content_type not in produces:
                            produces.append(content_type)

                if produces:
                    new_operation["produces"] = produces
                if consumes:
                    new_operation["consumes"] = consumes

                swagger["paths"][path][method] = new_operation

        # Convert components to definitions
        for name, schema in openapi3.get("components", {}).get("schemas", {}).items():
            swagger["definitions"][name] = self._convert_schema(schema)

        return swagger

    def _convert_schema_ref(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema references from OpenAPI 3 format to Swagger 2.

        Args:
            schema: Schema object possibly containing references

        Returns:
            Converted schema
        """
        if "$ref" in schema:
            return {
                "$ref": schema["$ref"].replace(
                    "#/components/schemas/", "#/definitions/"
                )
            }
        return self._convert_schema(schema)

    def _convert_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema object from OpenAPI 3 format to Swagger 2.

        Args:
            schema: Schema object

        Returns:
            Converted schema
        """
        new_schema = {**schema}

        # Handle nested objects
        if "properties" in new_schema:
            for prop_name, prop_schema in new_schema["properties"].items():
                new_schema["properties"][prop_name] = self._convert_schema_ref(
                    prop_schema
                )

        # Handle arrays
        if "items" in new_schema and isinstance(new_schema["items"], dict):
            new_schema["items"] = self._convert_schema_ref(new_schema["items"])

        return new_schema


class PostmanToHarConverter(FormatConverter):
    """Converter from Postman Collection to HAR."""

    @classmethod
    def get_source_format(cls) -> str:
        return "postman"

    @classmethod
    def get_target_format(cls) -> str:
        return "har"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert Postman Collection to HAR format.

        Args:
            source_path: Path to Postman Collection file
            target_path: Path to output HAR file (optional)
            options: Additional options

        Returns:
            HAR data as dictionary
        """
        # Validate input file against Postman schema if validation is enabled
        validate_schema = options.pop("validate_schema", True)
        if validate_schema:
            is_valid, format_name, error = validate_file(source_path)
            if not is_valid:
                raise ValueError(f"Invalid Postman Collection file: {error}")
            if format_name != "postman":
                raise ValueError(
                    f"Expected Postman Collection file but detected {format_name}"
                )
        # Load Postman Collection
        with open(source_path, "r", encoding="utf-8") as f:
            postman_data = json.load(f)

        # Initialize HAR structure
        har_data = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "har-oa3-converter",
                    "version": "1.0.0",
                    "comment": "Created from Postman Collection",
                },
                "entries": [],
            }
        }

        # Process Postman items (requests)
        # Ensure entries is correctly typed as List[Dict[str, Any]] for mypy
        entries: List[Dict[str, Any]] = har_data["log"]["entries"]
        self._process_postman_items(postman_data, entries)

        # Save output if target path provided
        if target_path:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(har_data, f, indent=2)

        return har_data

    def _process_postman_items(
        self, postman_data: Dict[str, Any], entries: List[Dict[str, Any]]
    ) -> None:
        """Process Postman Collection items and add them to HAR entries.

        Args:
            postman_data: Postman Collection data
            entries: HAR entries list to populate
        """
        # Process root items
        items = postman_data.get("item", [])
        self._process_items(items, entries)

    def _process_items(
        self, items: List[Dict[str, Any]], entries: List[Dict[str, Any]]
    ) -> None:
        """Process Postman items recursively.

        Args:
            items: List of Postman items
            entries: HAR entries list to populate
        """
        for item in items:
            # Check if it's a folder (has subitems)
            if "item" in item:
                self._process_items(item["item"], entries)
            # It's a request
            elif "request" in item:
                entry = self._convert_request_to_entry(item)
                if entry:
                    entries.append(entry)

    def _convert_request_to_entry(
        self, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert a Postman request to a HAR entry.

        Args:
            item: Postman request item

        Returns:
            HAR entry or None if conversion failed
        """
        request_data = item.get("request", {})
        if not request_data:
            return None

        # Extract URL
        url = ""
        if isinstance(request_data.get("url"), str):
            url = request_data["url"]
        elif isinstance(request_data.get("url"), dict):
            url_obj = request_data["url"]
            raw_url = url_obj.get("raw")
            if raw_url:
                url = raw_url

        if not url:
            return None

        # Create HAR entry
        entry = {
            "request": {
                "method": request_data.get("method", "GET"),
                "url": url,
                "httpVersion": "HTTP/1.1",
                "headers": self._convert_headers(request_data.get("header", [])),
                "queryString": self._convert_query_params(request_data.get("url", {})),
                "cookies": [],
                "headersSize": -1,
                "bodySize": -1,
            },
            "response": {
                "status": 200,
                "statusText": "OK",
                "httpVersion": "HTTP/1.1",
                "headers": [],
                "cookies": [],
                "content": {"size": 0, "mimeType": "application/json", "text": "{}"},
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": -1,
            },
            "cache": {},
            "timings": {"send": 0, "wait": 0, "receive": 0},
        }

        # Add body if present
        body_data = request_data.get("body", {})
        if body_data and body_data.get("mode") in ["raw", "urlencoded", "formdata"]:
            self._add_request_body(entry["request"], body_data)

        # Add example response if available
        if "response" in item and item["response"]:
            example_response = (
                item["response"][0]
                if isinstance(item["response"], list)
                else item["response"]
            )
            if example_response:
                self._add_example_response(entry["response"], example_response)

        return entry

    def _convert_headers(self, headers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Convert Postman headers to HAR format.

        Args:
            headers: Postman headers list

        Returns:
            HAR headers list
        """
        result = []
        for header in headers:
            if header.get("disabled"):
                continue
            result.append(
                {"name": header.get("key", ""), "value": header.get("value", "")}
            )
        return result

    def _convert_query_params(self, url_obj: Dict[str, Any]) -> List[Dict[str, str]]:
        """Convert Postman URL query params to HAR format.

        Args:
            url_obj: Postman URL object

        Returns:
            HAR query string parameters
        """
        result = []

        # Handle string URL
        if isinstance(url_obj, str):
            url_parts = url_obj.split("?")
            if len(url_parts) > 1:
                query_string = url_parts[1]
                for param in query_string.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        result.append({"name": key, "value": value})
            return result

        # Handle URL object
        query = url_obj.get("query", [])
        for param in query:
            if param.get("disabled"):
                continue
            result.append(
                {"name": param.get("key", ""), "value": param.get("value", "")}
            )

        return result

    def _add_request_body(
        self, request: Dict[str, Any], body_data: Dict[str, Any]
    ) -> None:
        """Add body data to HAR request.

        Args:
            request: HAR request object
            body_data: Postman body data
        """
        mode = body_data.get("mode")

        if mode == "raw":
            mime_type = "text/plain"
            options = body_data.get("options", {})

            # Determine content type from options
            if options.get("raw", {}).get("language") == "json":
                mime_type = "application/json"
            elif options.get("raw", {}).get("language") == "xml":
                mime_type = "application/xml"

            request["postData"] = {
                "mimeType": mime_type,
                "text": body_data.get("raw", ""),
            }
        elif mode == "urlencoded":
            params = []
            for param in body_data.get("urlencoded", []):
                if param.get("disabled"):
                    continue
                params.append(
                    {"name": param.get("key", ""), "value": param.get("value", "")}
                )

            request["postData"] = {
                "mimeType": "application/x-www-form-urlencoded",
                "params": params,
            }
        elif mode == "formdata":
            params = []
            for param in body_data.get("formdata", []):
                if param.get("disabled"):
                    continue
                params.append(
                    {
                        "name": param.get("key", ""),
                        "value": (
                            param.get("value", "")
                            if param.get("type") == "text"
                            else "<file>"
                        ),
                    }
                )

            request["postData"] = {"mimeType": "multipart/form-data", "params": params}

    def _add_example_response(
        self, response: Dict[str, Any], example: Dict[str, Any]
    ) -> None:
        """Add example response data to HAR response.

        Args:
            response: HAR response object
            example: Postman example response
        """
        response["status"] = example.get("code", 200)
        response["statusText"] = example.get("status", "OK")

        # Add headers
        response["headers"] = self._convert_headers(example.get("header", []))

        # Add body
        body = example.get("body", "")
        content_type = "text/plain"

        # Try to determine content type from headers
        for header in response["headers"]:
            if header["name"].lower() == "content-type":
                content_type = header["value"]
                break

        response["content"] = {
            "size": len(body) if body else 0,
            "mimeType": content_type,
            "text": body or "{}",
        }


class PostmanToOpenApi3Converter(FormatConverter):
    """Converter from Postman Collection to OpenAPI 3."""

    @classmethod
    def get_source_format(cls) -> str:
        return "postman"

    @classmethod
    def get_target_format(cls) -> str:
        return "openapi3"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert Postman Collection to OpenAPI 3.

        Args:
            source_path: Path to Postman Collection file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)

        Returns:
            OpenAPI 3 specification as dictionary
        """
        # Validate input file against Postman schema if validation is enabled
        validate_schema = options.pop("validate_schema", True)
        if validate_schema:
            is_valid, format_name, error = validate_file(source_path)
            if not is_valid:
                raise ValueError(f"Invalid Postman Collection file: {error}")
            if format_name != "postman":
                raise ValueError(
                    f"Expected Postman Collection file but detected {format_name}"
                )
        # We'll implement this by first converting to HAR, then to OpenAPI 3
        # This maintains consistency with the existing conversion flow

        # First convert to HAR
        postman_to_har = PostmanToHarConverter()
        har_data = postman_to_har.convert(source_path)

        # Then convert HAR to OpenAPI 3
        info = {}
        if "title" in options:
            info["title"] = options["title"]
        if "version" in options:
            info["version"] = options["version"]
        if "description" in options:
            info["description"] = options["description"]

        servers = []
        if "servers" in options and options["servers"]:
            for server in options["servers"]:
                servers.append({"url": server})

        # Create a temporary HAR file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".har", mode="w"
        ) as tmp_har:
            json.dump(har_data, tmp_har)
            har_path = tmp_har.name

        try:
            # Convert HAR to OpenAPI 3
            converter = HarToOas3Converter(
                base_path=options.get("base_path"),
                info=info or None,
                servers=servers or None,
            )

            result = converter.convert(har_path, target_path)
            return result
        finally:
            # Clean up temporary file
            os.unlink(har_path)


# Register all available converters
CONVERTERS = [
    HarToOpenApi3Converter,
    OpenApi3ToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
    PostmanToHarConverter,
    PostmanToOpenApi3Converter,
]

# Format mapping for file extensions
FORMAT_EXTENSIONS = {
    "har": [".har"],
    "openapi3": [".yaml", ".yml", ".json"],
    "swagger": [".json", ".yaml", ".yml"],
    "postman": [".json", ".postman_collection.json"],
}


def get_available_formats() -> List[str]:
    """Get list of available formats.

    Returns:
        List of format names
    """
    formats = set()
    for converter_cls in CONVERTERS:
        formats.add(converter_cls.get_source_format())
        formats.add(converter_cls.get_target_format())
    return sorted(list(formats))


def get_converter_for_formats(
    source_format: str, target_format: str
) -> Optional[Type[FormatConverter]]:
    """Get converter class that can convert from source to target format.

    Args:
        source_format: Source format name
        target_format: Target format name

    Returns:
        Converter class or None if no suitable converter found
    """
    for converter_cls in CONVERTERS:
        if (
            converter_cls.get_source_format() == source_format
            and converter_cls.get_target_format() == target_format
        ):
            return converter_cls
    return None


def guess_format_from_file(file_path: str) -> Optional[str]:
    """Guess format from file extension.

    Args:
        file_path: Path to file

    Returns:
        Format name or None if format could not be determined
    """
    ext = os.path.splitext(file_path)[1].lower()

    for format_name, extensions in FORMAT_EXTENSIONS.items():
        if ext in extensions:
            # For ambiguous extensions (.yaml, .json), try to determine format by content
            if ext in [".yaml", ".yml", ".json"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        if ext == ".json":
                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)

                        # Determine format by content
                        if "swagger" in data:
                            return "swagger"
                        elif "openapi" in data:
                            return "openapi3"
                except:
                    pass
            return format_name

    return None


def convert_file(
    source_path: str,
    target_path: str,
    source_format: Optional[str] = None,
    target_format: Optional[str] = None,
    validate_schema: bool = True,
    **options,
) -> Optional[Dict[str, Any]]:
    """Convert file from source format to target format.

    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_format: Source format name (will be guessed if not provided)
        target_format: Target format name (will be guessed if not provided)
        validate_schema: Whether to validate input against schema
        options: Additional converter-specific options

    Returns:
        Converted data or None if conversion failed
    """
    # Verify source file exists
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file '{source_path}' not found")

    # Validate schema if requested
    if validate_schema:
        # Validate the file and detect format
        is_valid, detected_format, error = validate_file(source_path)
        if not is_valid:
            raise ValueError(f"Invalid source file: {error}")

        # If we detected a format and none was provided, use the detected format
        if detected_format and not source_format:
            source_format = detected_format
            print(f"Detected source format: {source_format}")

    # Guess formats if not provided
    if not source_format:
        source_format = guess_format_from_file(source_path)
        if not source_format:
            raise ValueError(f"Could not determine source format for '{source_path}'")

    if not target_format:
        target_format = guess_format_from_file(target_path)
        if not target_format:
            # Try to guess from target file extension
            ext = os.path.splitext(target_path)[1].lower()
            for format_name, extensions in FORMAT_EXTENSIONS.items():
                if ext in extensions:
                    target_format = format_name
                    break

        if not target_format:
            raise ValueError(f"Could not determine target format for '{target_path}'")

    # Get converter
    converter_cls = get_converter_for_formats(source_format, target_format)
    if not converter_cls:
        raise ValueError(
            f"No converter available for {source_format} to {target_format}"
        )

    # Create converter and convert
    converter = converter_cls()
    return converter.convert(source_path, target_path, **options)
