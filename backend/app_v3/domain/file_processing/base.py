"""
Base interface for file processors.

This module defines the abstract interface that all file processors should
implement. This ensures consistency and makes it easy to add new processor
types while maintaining the same integration pattern with progress tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..progress.publisher import ProgressPublisher
from ..progress.events import Stage, Status


class FileProcessor(ABC):
    """
    Abstract base class for file processors.
    
    All file processors should inherit from this class and implement
    the process() method. The processor receives a job_id and progress_publisher
    to enable progress tracking.
    
    Example:
        class PDFProcessor(FileProcessor):
            def process(self, file_bytes: bytes, job_id: str,
                      progress_publisher: ProgressPublisher, **kwargs):
                with ProgressContext(job_id, progress_publisher) as ctx:
                    ctx.emit_stage(Stage.EXTRACTION, Status.STARTED, 0)
                    # ... process file ...
                    ctx.emit_stage(Stage.COMPLETE, Status.COMPLETED, 100)
    """
    
    @abstractmethod
    def process(
        self,
        file_bytes: bytes,
        job_id: str,
        progress_publisher: ProgressPublisher,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a file and return results.
        
        This method should:
        1. Use ProgressContext to emit progress updates
        2. Handle errors and emit error events
        3. Return a dictionary with processing results
        
        Args:
            file_bytes: File content as bytes
            The file content to be processed
        job_id: Unique identifier for this processing job
            Used for progress tracking and WebSocket updates
        progress_publisher: Progress publisher instance
            Used to emit progress events during processing
        **kwargs: Additional processing parameters
            Processor-specific configuration options
        
        Returns:
            Dictionary with processing results, including:
            - success: bool indicating if processing succeeded
            - data: Processed data (structure depends on processor type)
            - metadata: Additional metadata about the processing
            - errors: List of errors if any occurred
        
        Raises:
            Exception: If processing fails critically (should also emit error event)
        """
        pass
    
    @abstractmethod
    def get_supported_file_types(self) -> list[str]:
        """
        Get list of file types (extensions) supported by this processor.
        
        Returns:
            List of file extensions (e.g., ["pdf", "docx", "txt"])
        """
        pass
    
    def validate_file(self, file_bytes: bytes, filename: str) -> tuple[bool, Optional[str]]:
        """
        Validate that the file can be processed by this processor.
        
        Default implementation checks file extension. Subclasses can
        override to add more sophisticated validation (e.g., magic numbers).
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file can be processed
            - error_message: None if valid, error description if invalid
        """
        if not filename:
            return False, "Filename is required"
        
        # Extract extension
        if '.' not in filename:
            return False, "File must have an extension"
        
        extension = filename.rsplit('.', 1)[1].lower()
        supported = self.get_supported_file_types()
        
        if extension not in supported:
            return False, f"File type '{extension}' not supported. Supported types: {', '.join(supported)}"
        
        return True, None

