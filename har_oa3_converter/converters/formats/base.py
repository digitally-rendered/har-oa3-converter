"""Base converter class for format converters.

This module defines the base interfaces for converter classes. The converters are responsible
for transforming data between different API specification formats without file I/O dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar, Union

# Type variables for source and target data types
SourceT = TypeVar("SourceT")
TargetT = TypeVar("TargetT")


class FormatConverter(ABC, Generic[SourceT, TargetT]):
    """Base abstract class for format converters.

    This class defines the interface for converters that transform data between different
    API specification formats. Converters work directly with data structures rather than files.
    """

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
    def convert_data(
        self, source_data: Dict[str, Any], **options: Any
    ) -> Dict[str, Any]:
        """Convert from source format to target format.

        Args:
            source_data: Source data as a dictionary
            options: Additional converter-specific options

        Returns:
            Converted data as a dictionary
        """
        pass

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options: Any
    ) -> Dict[str, Any]:
        """Legacy method for file-based conversion.

        This method is kept for backward compatibility with existing code.
        It wraps the new convert_data method, handling file I/O.

        Args:
            source_path: Path to source file
            target_path: Path to target file (optional)
            options: Additional converter-specific options

        Returns:
            Converted data as a dictionary
        """
        from har_oa3_converter.utils.file_handler import FileHandler

        # Read source file
        file_handler = FileHandler()
        source_data = file_handler.load(source_path)

        # Convert data
        result = self.convert_data(source_data, **options)

        # Write to target file if specified
        if target_path:
            file_handler.save(result, target_path)

        return result
