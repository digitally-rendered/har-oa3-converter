"""Tests for the FileHandler integration module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from har_oa3_converter.converters.file_handler_integration import (
    register_schemas,
    load_file,
    save_file,
    validate_with_schema
)
from har_oa3_converter.utils.file_handler import FileHandler


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "test": "data",
        "nested": {"key": "value"}
    }


@pytest.fixture
def sample_har_data():
    """Sample HAR data for testing."""
    return {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "Browser",
                "version": "1.0"
            },
            "entries": []
        }
    }


@pytest.fixture
def sample_file(sample_data):
    """Create a temporary file with sample data."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)


class TestFileHandlerIntegration:
    """Test class for the FileHandler integration module."""
    
    def test_register_schemas(self):
        """Test registering schemas with the FileHandler."""
        # Register schemas
        register_schemas()
        
        # Verify that schemas have been registered
        # We can't directly access the schemas, but we can verify by validation
        assert validate_with_schema({"log": {"version": "1.2", "creator": {"name": "Browser"}, "entries": []}}, "har")
        
        # Test with invalid schema name
        with pytest.raises(ValueError):
            validate_with_schema({}, "invalid_schema")
    
    def test_load_file(self, sample_file, sample_data):
        """Test loading a file."""
        # Load the file
        data = load_file(sample_file)
        
        # Verify the loaded data
        assert data == sample_data
        
        # Test with nonexistent file
        with pytest.raises(FileNotFoundError):
            load_file("nonexistent_file.json")
    
    def test_save_file(self, sample_data):
        """Test saving a file."""
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            file_path = f.name
        
        try:
            # Save the data to the file
            save_file(sample_data, file_path)
            
            # Verify the file was created
            assert os.path.exists(file_path)
            
            # Load the file and verify the content
            with open(file_path, "r") as f:
                loaded_data = json.load(f)
            
            assert loaded_data == sample_data
        finally:
            # Cleanup
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_validate_with_schema(self, sample_har_data):
        """Test validating data against a schema."""
        # Register schemas first
        register_schemas()
        
        # Validate valid HAR data
        assert validate_with_schema(sample_har_data, "har")
        
        # Test with invalid HAR data
        invalid_data = {"invalid": "data"}
        assert not validate_with_schema(invalid_data, "har")
