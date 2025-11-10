"""
Example file processor implementation.

This module provides an example implementation of a file processor that
demonstrates how to integrate with the progress tracking system. This can
serve as a template for implementing actual file processors (e.g., PDF,
Excel, CSV processors).
"""

import logging
import time
from typing import Dict, Any

from .base import FileProcessor
from ..progress.publisher import ProgressPublisher
from ..progress.context import ProgressContext
from ..progress.events import Stage, Status

logger = logging.getLogger(__name__)


class ExampleFileProcessor(FileProcessor):
    """
    Example file processor that demonstrates progress tracking integration.
    
    This processor simulates file processing with multiple stages and
    demonstrates how to use ProgressContext to emit progress updates.
    In a real implementation, this would perform actual file processing
    (e.g., parsing PDF, extracting data, validating, storing).
    """
    
    def __init__(self):
        """Initialize the example processor."""
        self.supported_types = ["txt", "pdf", "csv"]
    
    def process(
        self,
        file_bytes: bytes,
        job_id: str,
        progress_publisher: ProgressPublisher,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a file with progress tracking.
        
        This example demonstrates the typical pattern:
        1. Use ProgressContext to manage progress events
        2. Emit stage updates at key checkpoints
        3. Handle errors and emit error events
        4. Return processing results
        
        Args:
            file_bytes: File content as bytes
            job_id: Unique identifier for this processing job
            progress_publisher: Progress publisher instance
            **kwargs: Additional parameters (e.g., filename, options)
        
        Returns:
            Dictionary with processing results
        """
        filename = kwargs.get("filename", "unknown")
        simulate_delay = kwargs.get("simulate_delay", True)
        
        logger.info(f"Processing file: {filename} (job_id: {job_id})")
        
        try:
            with ProgressContext(job_id, progress_publisher) as ctx:
                # Stage 1: File Upload
                ctx.emit_stage(
                    Stage.FILE_UPLOAD,
                    Status.STARTED,
                    0,
                    meta={"filename": filename, "size": len(file_bytes)}
                )
                
                if simulate_delay:
                    time.sleep(0.5)  # Simulate processing time
                
                ctx.emit_stage(
                    Stage.FILE_UPLOAD,
                    Status.COMPLETED,
                    10,
                    meta={"message": "File validated and ready for processing"}
                )
                
                # Stage 2: Extraction
                ctx.emit_stage(
                    Stage.EXTRACTION,
                    Status.STARTED,
                    10,
                    meta={"message": "Starting content extraction"}
                )
                
                if simulate_delay:
                    time.sleep(1.0)  # Simulate extraction time
                
                # Simulate extracting some data
                extracted_items = len(file_bytes) // 100  # Fake metric
                
                ctx.emit_stage(
                    Stage.EXTRACTION,
                    Status.COMPLETED,
                    40,
                    meta={
                        "message": "Extraction completed",
                        "items_extracted": extracted_items
                    }
                )
                
                # Stage 3: Processing
                ctx.emit_stage(
                    Stage.PROCESSING,
                    Status.STARTED,
                    40,
                    meta={"message": "Processing extracted content"}
                )
                
                if simulate_delay:
                    time.sleep(1.5)  # Simulate processing time
                
                # Simulate processing results
                processed_count = extracted_items * 2
                
                ctx.emit_stage(
                    Stage.PROCESSING,
                    Status.IN_PROGRESS,
                    60,
                    meta={"items_processed": processed_count // 2}
                )
                
                if simulate_delay:
                    time.sleep(1.0)
                
                ctx.emit_stage(
                    Stage.PROCESSING,
                    Status.COMPLETED,
                    70,
                    meta={
                        "message": "Processing completed",
                        "items_processed": processed_count
                    }
                )
                
                # Stage 4: Validation
                ctx.emit_stage(
                    Stage.VALIDATION,
                    Status.STARTED,
                    70,
                    meta={"message": "Validating processed data"}
                )
                
                if simulate_delay:
                    time.sleep(0.5)
                
                # Simulate validation results
                valid_count = int(processed_count * 0.95)  # 95% valid
                invalid_count = processed_count - valid_count
                
                ctx.emit_stage(
                    Stage.VALIDATION,
                    Status.COMPLETED,
                    85,
                    meta={
                        "message": "Validation completed",
                        "valid_items": valid_count,
                        "invalid_items": invalid_count
                    }
                )
                
                # Stage 5: Storage
                ctx.emit_stage(
                    Stage.STORAGE,
                    Status.STARTED,
                    85,
                    meta={"message": "Storing processed data"}
                )
                
                if simulate_delay:
                    time.sleep(0.5)
                
                ctx.emit_stage(
                    Stage.STORAGE,
                    Status.COMPLETED,
                    95,
                    meta={
                        "message": "Storage completed",
                        "items_stored": valid_count
                    }
                )
                
                # Stage 6: Complete
                ctx.emit_stage(
                    Stage.COMPLETE,
                    Status.COMPLETED,
                    100,
                    meta={
                        "message": "File processing completed successfully",
                        "summary": {
                            "filename": filename,
                            "file_size": len(file_bytes),
                            "items_extracted": extracted_items,
                            "items_processed": processed_count,
                            "items_validated": valid_count,
                            "items_stored": valid_count
                        }
                    }
                )
                
                # Return processing results
                return {
                    "success": True,
                    "data": {
                        "filename": filename,
                        "file_size": len(file_bytes),
                        "items_extracted": extracted_items,
                        "items_processed": processed_count,
                        "items_validated": valid_count,
                        "items_stored": valid_count
                    },
                    "metadata": {
                        "processor": "ExampleFileProcessor",
                        "job_id": job_id
                    },
                    "errors": []
                }
        
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}", exc_info=True)
            
            # Error event is automatically emitted by ProgressContext.__exit__
            # But we can also emit it explicitly if needed
            
            return {
                "success": False,
                "data": None,
                "metadata": {
                    "processor": "ExampleFileProcessor",
                    "job_id": job_id,
                    "filename": filename
                },
                "errors": [{
                    "type": type(e).__name__,
                    "message": str(e)
                }]
            }
    
    def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported file types.
        
        Returns:
            List of file extensions supported by this processor
        """
        return self.supported_types

