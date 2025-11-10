"""
File processing module.

This module provides infrastructure for processing files with progress tracking.
It includes:
- Base processor interface
- Example processor implementation
- Service layer for orchestrating processing
"""

from .base import FileProcessor
from .processor import ExampleFileProcessor
from .services import FileProcessingService

__all__ = [
    "FileProcessor",
    "ExampleFileProcessor",
    "FileProcessingService",
]

