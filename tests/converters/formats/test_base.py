"""Tests for the base FormatConverter class."""

import pytest
from typing import Dict, Any, Optional

from har_oa3_converter.converters.formats.base import FormatConverter


class MockConverter(FormatConverter):
    """Mock converter implementation for testing."""
    
    @classmethod
    def get_source_format(cls) -> str:
        return "mock_source"
    
    @classmethod
    def get_target_format(cls) -> str:
        return "mock_target"
    
    def convert(self, source_path: str, target_path: Optional[str] = None, **options) -> Dict[str, Any]:
        return {"converted": True, "source": source_path, "target": target_path, "options": options}


class TestFormatConverter:
    """Tests for the FormatConverter base class."""
    
    def test_get_name(self):
        """Test the get_name class method."""
        assert MockConverter.get_name() == "MockConverter"
    
    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        # Attempt to create a class that doesn't implement all abstract methods
        with pytest.raises(TypeError):
            class IncompleteConverter(FormatConverter):
                pass
            
            # This should fail because abstract methods aren't implemented
            IncompleteConverter()
    
    def test_mock_converter(self):
        """Test the mock converter implementation."""
        converter = MockConverter()
        
        # Test class methods
        assert converter.get_source_format() == "mock_source"
        assert converter.get_target_format() == "mock_target"
        
        # Test convert method
        result = converter.convert("source.json", "target.json", option1="value1")
        assert result == {
            "converted": True, 
            "source": "source.json", 
            "target": "target.json", 
            "options": {"option1": "value1"}
        }
