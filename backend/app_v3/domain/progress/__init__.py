"""
Progress tracking module for file processing operations.

This module provides infrastructure for emitting and subscribing to
real-time progress updates during file processing. It includes:
- Event schema and constants
- Publisher/subscriber interface
- Context manager for easy integration
- Background task runner
"""

from .events import ProgressEvent, Stage, Status, Verbosity
from .publisher import ProgressPublisher, InMemoryProgressPublisher
from .context import ProgressContext
from .task_runner import BackgroundTaskRunner

__all__ = [
    "ProgressEvent",
    "Stage",
    "Status",
    "Verbosity",
    "ProgressPublisher",
    "InMemoryProgressPublisher",
    "ProgressContext",
    "BackgroundTaskRunner",
]

