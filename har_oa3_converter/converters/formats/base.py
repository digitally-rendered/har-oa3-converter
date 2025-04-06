"""Base converter class for format converters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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
        """Convert from source format to target format.

        Args:
            source_path: Path to source file
            target_path: Path to target file (optional)
            options: Additional options

        Returns:
            Converted data
        """
        pass
