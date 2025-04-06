"""Tests for the file handler module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

from har_oa3_converter.schemas import HAR_SCHEMA, get_schema
from har_oa3_converter.utils.file_handler import FileHandler


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {"test": "data", "nested": {"key": "value"}}


@pytest.fixture
def json_file(sample_json_data):
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_json_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


@pytest.fixture
def yaml_file(sample_json_data):
    """Create a temporary YAML file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        yaml_content = yaml.dump(sample_json_data, default_flow_style=False)
        f.write(yaml_content.encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestFileHandler:
    """Test class for file handler module."""

    def setup_method(self):
        """Setup for tests."""
        # Clear any registered schemas before each test
        FileHandler._schemas = {}

    def test_load_json_file(self, json_file, sample_json_data):
        """Test loading a JSON file."""
        data = FileHandler.load(json_file)
        assert data == sample_json_data

    def test_load_yaml_file(self, yaml_file, sample_json_data):
        """Test loading a YAML file."""
        data = FileHandler.load(yaml_file)
        assert data == sample_json_data

    def test_save_json_file(self, sample_json_data):
        """Test saving a JSON file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            file_path = f.name

        try:
            # Save data to file
            FileHandler.save(sample_json_data, file_path)

            # Load data back to verify
            with open(file_path, "r") as f:
                loaded_data = json.load(f)

            assert loaded_data == sample_json_data
        finally:
            os.unlink(file_path)

    def test_save_yaml_file(self, sample_json_data):
        """Test saving a YAML file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            file_path = f.name

        try:
            # Save data to file
            FileHandler.save(sample_json_data, file_path)

            # Load data back to verify
            with open(file_path, "r") as f:
                loaded_data = yaml.safe_load(f)

            assert loaded_data == sample_json_data
        finally:
            os.unlink(file_path)

    def test_load_invalid_extension(self):
        """Test loading a file with an invalid extension."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"invalid data")
            file_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to load file"):
                FileHandler.load(file_path)
        finally:
            os.unlink(file_path)

    def test_save_with_txt_extension(self, sample_json_data):
        """Test saving a file with txt extension - should default to JSON."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            file_path = f.name

        try:
            # This should work as the FileHandler will default to JSON
            FileHandler.save(sample_json_data, file_path)

            # Read file contents to verify it saved as JSON
            with open(file_path, "r") as f:
                content = f.read()

            # Should be valid JSON
            parsed = json.loads(content)
            assert parsed == sample_json_data
        finally:
            os.unlink(file_path)

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            FileHandler.load("nonexistent.json")

    def test_register_schema(self):
        """Test registering a schema."""
        # Register a sample schema
        sample_schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        FileHandler.register_schema("test_schema", sample_schema)

        # Verify schema is registered by checking internal _schemas dict
        assert "test_schema" in FileHandler._schemas
        assert FileHandler._schemas["test_schema"] == sample_schema

    def test_load_schema(self):
        """Test loading a schema from a file."""
        # Create a sample schema file
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}

        # Test with JSON schema file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            json_path = f.name
            f.write(json.dumps(schema).encode("utf-8"))

        # Test with YAML schema file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            yaml_path = f.name
            f.write(yaml.dump(schema).encode("utf-8"))

        try:
            # Test loading JSON schema
            json_schema = FileHandler.load_schema(json_path)
            assert json_schema == schema

            # Test loading YAML schema
            yaml_schema = FileHandler.load_schema(yaml_path)
            assert yaml_schema == schema
        finally:
            # Cleanup
            os.unlink(json_path)
            os.unlink(yaml_path)

    def test_validate(self):
        """Test validating data against a schema."""
        # Register a schema
        schema = {
            "type": "object",
            "required": ["test"],
            "properties": {"test": {"type": "string"}},
        }
        FileHandler.register_schema("test_schema", schema)

        # Valid data
        valid_data = {"test": "value"}
        assert FileHandler.validate(valid_data, "test_schema") is True

        # Invalid data (missing required field)
        invalid_data = {"other": "value"}
        assert FileHandler.validate(invalid_data, "test_schema") is False

        # Test with unknown schema
        with pytest.raises(ValueError, match="Schema 'unknown' not registered"):
            FileHandler.validate({}, "unknown")

    def test_load_and_validate(self, sample_json_data):
        """Test loading and validating a file."""
        # Register a schema that matches the sample data
        schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}, "nested": {"type": "object"}},
        }
        FileHandler.register_schema("test_schema", schema)

        # Create a test file with sample data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(json.dumps(sample_json_data).encode("utf-8"))
            file_path = f.name

        try:
            # Test that load_and_validate works
            data = FileHandler.load_and_validate(file_path, "test_schema")
            assert data == sample_json_data

            # Test with validation failure
            # Register a schema that won't match the sample data
            invalid_schema = {"type": "object", "required": ["missing_field"]}
            FileHandler.register_schema("invalid_schema", invalid_schema)

            with pytest.raises(ValueError, match="failed validation against schema"):
                FileHandler.load_and_validate(file_path, "invalid_schema")
        finally:
            os.unlink(file_path)

    def test_save_in_nested_directory(self, sample_json_data):
        """Test saving a file in a nested directory that doesn't exist yet."""
        # Create a temporary root directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define a nested path that doesn't exist yet
            nested_path = os.path.join(temp_dir, "level1", "level2", "file.json")

            try:
                # Save data - should create directories as needed
                FileHandler.save(sample_json_data, nested_path)

                # Verify directories were created
                assert os.path.exists(os.path.dirname(nested_path))

                # Verify file was saved correctly
                loaded_data = FileHandler.load(nested_path)
                assert loaded_data == sample_json_data
            finally:
                # Directory will be cleaned up by tempfile.TemporaryDirectory
                pass

    def test_file_format_detection_basic(self):
        """Test basic file format detection based on file extension."""
        # Create files with different extensions
        for ext in [".json", ".yaml", ".yml", ".har"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(b'{"test": "data"}')
                file_path = f.name

            try:
                # All of these should load without error
                data = FileHandler.load(file_path)
                assert data == {"test": "data"}
            finally:
                os.unlink(file_path)

    def test_load_non_dict_content(self):
        """Test loading content that's not a dictionary."""
        # Create a JSON file with a list instead of a dict
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(b"[1, 2, 3]")
            file_path = f.name

        try:
            with pytest.raises(ValueError, match="Loaded content is not a dictionary"):
                FileHandler.load(file_path)
        finally:
            os.unlink(file_path)

    def test_save_with_error(self, sample_json_data, monkeypatch):
        """Test saving a file with an error."""

        # Mock open to raise an exception
        def mock_open(*args, **kwargs):
            raise IOError("Simulated error")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(ValueError, match="Failed to save file"):
            FileHandler.save(sample_json_data, "any_file.json")
