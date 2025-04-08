"""File handling utilities for various file formats."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from jsonschema import ValidationError, validate

from har_oa3_converter.utils.format_detector import guess_format_from_content


class FileHandler:
    """File handler for YAML and JSON files with schema validation support."""

    # Dictionary to store loaded schemas
    _schemas: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_schema(cls, schema_name: str, schema: Dict[str, Any]) -> None:
        """Register a schema for validation.

        Args:
            schema_name: Name of the schema
            schema: JSON schema document
        """
        cls._schemas[schema_name] = schema

    @classmethod
    def load_schema(cls, schema_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a schema from a file.

        Args:
            schema_path: Path to schema file

        Returns:
            Loaded schema
        """
        schema_path = Path(schema_path)
        with open(schema_path, "r", encoding="utf-8") as f:
            if schema_path.suffix.lower() in [".json"]:
                return json.load(f)
            else:
                return yaml.safe_load(f)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load content from a file based on its extension.

        Args:
            file_path: Path to file

        Returns:
            Loaded content as dictionary

        Raises:
            ValueError: If file could not be loaded
            FileNotFoundError: If file does not exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".json", ".har"]:
                    # Parse as JSON
                    content = json.load(f)
                elif file_path.suffix.lower() in [".yaml", ".yml"]:
                    # Parse as YAML
                    content = yaml.safe_load(f)
                else:
                    # Try JSON first, then YAML if that fails
                    try:
                        content = json.load(f)
                    except json.JSONDecodeError:
                        f.seek(0)  # Reset file position
                        content = yaml.safe_load(f)

                if not isinstance(content, dict):
                    raise ValueError(
                        f"Loaded content is not a dictionary: {type(content)}"
                    )

                return content
        except Exception as e:
            raise ValueError(f"Failed to load file {file_path}: {str(e)}")

    @classmethod
    def save(cls, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save data to a file based on extension.

        Args:
            data: Data to save
            file_path: Path to save to

        Raises:
            ValueError: If file could not be saved
        """
        file_path = Path(file_path)

        # Create parent directories if they don't exist
        os.makedirs(file_path.parent, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".json", ".har"]:
                    json.dump(data, f, indent=2)
                elif file_path.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(data, f, sort_keys=False)
                else:
                    # Default to JSON
                    json.dump(data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save file {file_path}: {str(e)}")

    @classmethod
    def validate(cls, data: Dict[str, Any], schema_name: str) -> bool:
        """Validate data against a registered schema.

        Args:
            data: Data to validate
            schema_name: Name of schema to validate against

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If schema is not registered
        """
        if schema_name not in cls._schemas:
            raise ValueError(f"Schema '{schema_name}' not registered")

        try:
            validate(instance=data, schema=cls._schemas[schema_name])
            return True
        except ValidationError:
            return False

    @classmethod
    def load_and_validate(
        cls, file_path: Union[str, Path], schema_name: str
    ) -> Dict[str, Any]:
        """Load a file and validate it against a schema.

        Args:
            file_path: Path to file
            schema_name: Name of schema to validate against

        Returns:
            Loaded and validated data

        Raises:
            ValueError: If file could not be loaded or validation failed
        """
        data = cls.load(file_path)

        if not cls.validate(data, schema_name):
            raise ValueError(
                f"File {file_path} failed validation against schema '{schema_name}'"
            )

        return data

    @classmethod
    def read_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read file content as a dictionary.

        Args:
            file_path: Path to file

        Returns:
            File content as dictionary
        """
        return cls.load(file_path)

    @classmethod
    def write_file(cls, file_path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Write data to a file.

        Args:
            file_path: Path to file
            data: Data to write
        """
        cls.save(data, file_path)

    @classmethod
    def process_uploaded_file(cls, file) -> Dict[str, Any]:
        """Process an uploaded file from FastAPI.

        Args:
            file: UploadFile from FastAPI

        Returns:
            File content as dictionary
        """
        content = file.file.read()
        try:
            # Try to parse as JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            # If not JSON, try YAML
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Unable to parse file content: {str(e)}")
