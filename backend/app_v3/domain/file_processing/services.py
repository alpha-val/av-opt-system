"""
File processing service layer.

This module provides a service layer that orchestrates file processing
using processors and integrates with the progress tracking system. It
handles processor selection, validation, and error handling.
"""

import logging
from typing import Dict, Any, Optional, List

from .base import FileProcessor
from .processor import ExampleFileProcessor
from ..progress.publisher import ProgressPublisher
from ..progress.events import Stage, Status

logger = logging.getLogger(__name__)


class FileProcessingService:
    """
    Service for processing files with progress tracking.
    
    This service manages file processors and coordinates the processing
    workflow. It selects the appropriate processor based on file type,
    validates files, and handles errors.
    
    The service is designed to work with the background task runner,
    which calls the process_file() method with job_id and progress_publisher.
    """
    
    def __init__(self):
        """
        Initialize the file processing service.
        
        Registers available file processors. In a real implementation,
        you might use a plugin system or dependency injection to register
        processors dynamically.
        """
        # Map file extension -> processor instance
        self._processors: Dict[str, FileProcessor] = {}
        
        # Register default processors
        example_processor = ExampleFileProcessor()
        for file_type in example_processor.get_supported_file_types():
            self._processors[file_type] = example_processor
        
        logger.info(
            f"Initialized FileProcessingService with processors for: "
            f"{', '.join(self._processors.keys())}"
        )
    
    def register_processor(self, file_type: str, processor: FileProcessor) -> None:
        """
        Register a file processor for a specific file type.
        
        Args:
            file_type: File extension (e.g., "pdf", "csv")
            processor: FileProcessor instance
        """
        self._processors[file_type] = processor
        logger.info(f"Registered processor for file type: {file_type}")
    
    def get_processor(self, filename: str) -> Optional[FileProcessor]:
        """
        Get the appropriate processor for a file.
        
        Args:
            filename: Name of the file (used to determine file type)
            
        Returns:
            FileProcessor instance, or None if no processor found
        """
        if '.' not in filename:
            return None
        
        extension = filename.rsplit('.', 1)[1].lower()
        return self._processors.get(extension)
    
    def process_file(
        self,
        file_bytes: bytes,
        filename: str,
        job_id: str,
        progress_publisher: ProgressPublisher,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a file using the appropriate processor.
        
        This method:
        1. Selects the appropriate processor based on file type
        2. Validates the file
        3. Calls the processor's process() method
        4. Returns processing results
        
        This method is designed to be called by the background task runner,
        which provides job_id and progress_publisher.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            job_id: Unique identifier for this processing job
            progress_publisher: Progress publisher instance
            **kwargs: Additional parameters to pass to processor
        
        Returns:
            Dictionary with processing results:
            - success: bool
            - data: Processed data
            - metadata: Processing metadata
            - errors: List of errors
        """
        logger.info(f"Processing file: {filename} (job_id: {job_id})")
        
        # Get processor for this file type
        processor = self.get_processor(filename)
        
        if processor is None:
            error_msg = f"No processor found for file: {filename}"
            logger.error(error_msg)
            
            # Emit error event
            from ..progress.events import ProgressEvent
            error_event = ProgressEvent(
                job_id=job_id,
                stage=Stage.ERROR,
                status=Status.FAILED,
                progress=0,
                seq=0,
                meta={
                    "error_type": "NoProcessorError",
                    "error_message": error_msg,
                    "filename": filename
                }
            )
            progress_publisher.publish(job_id, error_event)
            
            return {
                "success": False,
                "data": None,
                "metadata": {
                    "filename": filename,
                    "job_id": job_id
                },
                "errors": [error_msg]
            }
        
        # Validate file
        is_valid, error_message = processor.validate_file(file_bytes, filename)
        
        if not is_valid:
            error_msg = f"File validation failed: {error_message}"
            logger.error(error_msg)
            
            # Emit error event
            from ..progress.events import ProgressEvent
            error_event = ProgressEvent(
                job_id=job_id,
                stage=Stage.ERROR,
                status=Status.FAILED,
                progress=0,
                seq=0,
                meta={
                    "error_type": "ValidationError",
                    "error_message": error_msg,
                    "filename": filename
                }
            )
            progress_publisher.publish(job_id, error_event)
            
            return {
                "success": False,
                "data": None,
                "metadata": {
                    "filename": filename,
                    "job_id": job_id
                },
                "errors": [error_msg]
            }
        
        # Process file using the selected processor
        try:
            result = processor.process(
                file_bytes,
                job_id,
                progress_publisher,
                filename=filename,
                **kwargs
            )
            return result
        
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}", exc_info=True)
            
            # Error event should be emitted by processor, but emit one here as safety
            from ..progress.events import ProgressEvent
            error_event = ProgressEvent(
                job_id=job_id,
                stage=Stage.ERROR,
                status=Status.FAILED,
                progress=0,
                seq=999,
                meta={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "filename": filename
                }
            )
            progress_publisher.publish(job_id, error_event)
            
            return {
                "success": False,
                "data": None,
                "metadata": {
                    "filename": filename,
                    "job_id": job_id
                },
                "errors": [{
                    "type": type(e).__name__,
                    "message": str(e)
                }]
            }
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get list of all supported file types.
        
        Returns:
            List of file extensions that have registered processors
        """
        return list(self._processors.keys())

