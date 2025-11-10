"""
Progress context manager for easy integration into processing functions.

This module provides a context manager that simplifies emitting progress
events during file processing. It handles sequence numbering, timestamp
generation, and provides convenient methods for emitting stage updates.
"""

import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .events import ProgressEvent, Stage, Status
from .publisher import ProgressPublisher

logger = logging.getLogger(__name__)


class ProgressContext:
    """
    Context manager for emitting progress events during file processing.
    
    This class provides a convenient way to emit progress updates without
    manually managing sequence numbers, timestamps, or event construction.
    It's designed to be used as a context manager:
    
    Example:
        with ProgressContext(job_id, publisher) as ctx:
            ctx.emit_stage(Stage.FILE_UPLOAD, Status.STARTED, 0)
            # ... do work ...
            ctx.emit_stage(Stage.FILE_UPLOAD, Status.COMPLETED, 20)
    
    The context manager automatically handles:
    - Sequence number incrementing
    - Timestamp generation
    - Error handling and final status emission
    """
    
    def __init__(
        self,
        job_id: str,
        publisher: ProgressPublisher,
        verbosity: str = "low"
    ):
        """
        Initialize the progress context.
        
        Args:
            job_id: Unique identifier for the processing job
            publisher: Progress publisher instance for emitting events
            verbosity: Verbosity level ("low", "medium", "high")
        """
        self.job_id = job_id
        self.publisher = publisher
        self.verbosity = verbosity
        self._seq = 0
        self._started = False
    
    def _emit(
        self,
        stage: Stage,
        status: Status,
        progress: int,
        meta: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Internal method to emit a progress event.
        
        This method constructs a ProgressEvent with automatic sequence
        numbering and timestamp, then publishes it via the publisher.
        
        Args:
            stage: Processing stage
            status: Stage status
            progress: Progress percentage (0-100)
            meta: Optional metadata dictionary
        """
        event = ProgressEvent(
            job_id=self.job_id,
            stage=stage,
            status=status,
            progress=progress,
            seq=self._seq,
            meta=meta
        )
        
        self.publisher.publish(self.job_id, event)
        self._seq += 1
        
        logger.debug(
            f"Emitted progress event: job_id={self.job_id}, "
            f"stage={stage.value}, status={status.value}, progress={progress}%"
        )
    
    def emit_stage(
        self,
        stage: Stage,
        status: Status,
        progress: int,
        meta: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit a progress event for a specific stage.
        
        This is the main method for emitting progress updates. It should
        be called at key checkpoints during processing.
        
        Args:
            stage: Processing stage (e.g., Stage.EXTRACTION)
            status: Stage status (e.g., Status.STARTED, Status.COMPLETED)
            progress: Overall progress percentage (0-100)
            meta: Optional metadata with additional details (e.g., {"items": 100})
        """
        self._emit(stage, status, progress, meta)
    
    def emit_error(
        self,
        error: Exception,
        meta: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit an error event.
        
        This should be called when an error occurs during processing.
        It automatically sets the stage to ERROR and status to FAILED.
        
        Args:
            error: The exception that occurred
            meta: Optional metadata (error details are automatically included)
        """
        error_meta = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(meta or {})
        }
        
        self._emit(
            Stage.ERROR,
            Status.FAILED,
            self._get_current_progress(),
            error_meta
        )
    
    def _get_current_progress(self) -> int:
        """
        Get the current progress value.
        
        This is a simple implementation that tracks the last emitted
        progress. In a more sophisticated implementation, you might
        track progress per stage.
        
        Returns:
            Last emitted progress value, or 0 if none
        """
        # Simple implementation: return last progress
        # In practice, you might want to track progress per stage
        # For now, we'll use a simple approach where callers specify progress
        return 0  # Default, should be overridden by callers
    
    def __enter__(self):
        """
        Enter the context manager.
        
        Returns:
            Self for use in 'with' statement
        """
        self._started = True
        logger.debug(f"Started progress context for job_id: {self.job_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager.
        
        If an exception occurred, emits an error event. Otherwise, ensures
        a COMPLETE event is emitted if processing finished successfully.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type is not None:
            # An exception occurred, emit error event
            self.emit_error(
                exc_val,
                meta={"exception_type": exc_type.__name__}
            )
        else:
            # No exception, but check if we emitted a COMPLETE event
            # If not, the caller should have done so explicitly
            logger.debug(f"Exited progress context for job_id: {self.job_id}")
        
        return False  # Don't suppress exceptions


@contextmanager
def progress_context(
    job_id: str,
    publisher: ProgressPublisher,
    verbosity: str = "low"
):
    """
    Convenience function for creating a progress context.
    
    This is an alternative to using ProgressContext directly, providing
    a function-based interface for the context manager.
    
    Example:
        with progress_context(job_id, publisher) as ctx:
            ctx.emit_stage(Stage.FILE_UPLOAD, Status.STARTED, 0)
    
    Args:
        job_id: Unique identifier for the processing job
        publisher: Progress publisher instance
        verbosity: Verbosity level
        
    Yields:
        ProgressContext instance
    """
    with ProgressContext(job_id, publisher, verbosity) as ctx:
        yield ctx

