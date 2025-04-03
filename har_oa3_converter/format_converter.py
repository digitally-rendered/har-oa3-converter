"""Format converter module for transforming between different API specification formats."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from har_oa3_converter.converter import HarToOas3Converter


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
    def convert(self, source_path: str, target_path: Optional[str] = None, **options) -> Dict[str, Any]:
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

    def convert(self, source_path: str, target_path: Optional[str] = None, **options) -> Dict[str, Any]:
        """Convert HAR to OpenAPI 3.
        
        Args:
            source_path: Path to HAR file
            target_path: Path to output OpenAPI 3 file (optional)
            options: Additional options (title, version, description, servers)
            
        Returns:
            OpenAPI 3 specification as dictionary
        """
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
            servers=servers or None
        )
        
        return converter.convert(source_path, target_path)


class OpenApi3ToSwaggerConverter(FormatConverter):
    """Converter from OpenAPI 3 to Swagger 2 (OpenAPI 2)."""

    @classmethod
    def get_source_format(cls) -> str:
        return "openapi3"

    @classmethod
    def get_target_format(cls) -> str:
        return "swagger"

    def convert(self, source_path: str, target_path: Optional[str] = None, **options) -> Dict[str, Any]:
        """Convert OpenAPI 3 to Swagger 2.
        
        Args:
            source_path: Path to OpenAPI 3 file
            target_path: Path to output Swagger file (optional)
            options: Additional options
            
        Returns:
            Swagger specification as dictionary
        """
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
            "definitions": {}
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
                    "responses": {}
                }
                
                # Convert parameters
                for param in operation.get("parameters", []):
                    # In OpenAPI 3, content is used, in Swagger 2 it's type/format
                    if "schema" in param:
                        schema = param["schema"]
                        new_param = {**param}
                        if "$ref" in schema:
                            ref = schema["$ref"].replace("#/components/schemas/", "#/definitions/")
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
                            "schema": self._convert_schema_ref(schema)
                        }
                        new_operation["parameters"].append(body_param)
                        break
                        
                # Convert responses
                for status, response in operation.get("responses", {}).items():
                    new_response = {
                        "description": response.get("description", "")
                    }
                    
                    if "content" in response:
                        for content_type, content_schema in response["content"].items():
                            if "schema" in content_schema:
                                new_response["schema"] = self._convert_schema_ref(content_schema["schema"])
                            break
                    
                    new_operation["responses"][status] = new_response
                
                # Add produces/consumes based on content types
                produces = []
                consumes = []
                
                if "requestBody" in operation:
                    for content_type in operation["requestBody"].get("content", {}).keys():
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
            return {"$ref": schema["$ref"].replace("#/components/schemas/", "#/definitions/")}
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
                new_schema["properties"][prop_name] = self._convert_schema_ref(prop_schema)
                
        # Handle arrays
        if "items" in new_schema and isinstance(new_schema["items"], dict):
            new_schema["items"] = self._convert_schema_ref(new_schema["items"])
            
        return new_schema


# Register all available converters
CONVERTERS = [
    HarToOpenApi3Converter,
    OpenApi3ToSwaggerConverter,
]

# Format mapping for file extensions
FORMAT_EXTENSIONS = {
    "har": [".har"],
    "openapi3": [".yaml", ".yml", ".json"],
    "swagger": [".json", ".yaml", ".yml"],
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


def get_converter_for_formats(source_format: str, target_format: str) -> Optional[Type[FormatConverter]]:
    """Get converter class that can convert from source to target format.
    
    Args:
        source_format: Source format name
        target_format: Target format name
        
    Returns:
        Converter class or None if no suitable converter found
    """
    for converter_cls in CONVERTERS:
        if (converter_cls.get_source_format() == source_format and 
            converter_cls.get_target_format() == target_format):
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


def convert_file(source_path: str, target_path: str, source_format: Optional[str] = None, 
                target_format: Optional[str] = None, **options) -> Optional[Dict[str, Any]]:
    """Convert file from source format to target format.
    
    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_format: Source format name (will be guessed if not provided)
        target_format: Target format name (will be guessed if not provided)
        options: Additional converter-specific options
        
    Returns:
        Converted data or None if conversion failed
    """
    # Verify source file exists
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file '{source_path}' not found")
    
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
        raise ValueError(f"No converter available for {source_format} to {target_format}")
        
    # Create converter and convert
    converter = converter_cls()
    return converter.convert(source_path, target_path, **options)
