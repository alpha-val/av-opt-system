"""
File processing router.

This module provides FastAPI endpoints for file upload and processing.
It demonstrates the integration pattern with the progress tracking system:
1. Accept file upload
2. Generate job_id
3. Return job_id immediately
4. Submit processing to background runner
5. Client connects to WebSocket to receive progress updates
"""

import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from ....domain.file_processing.services import FileProcessingService
from ....domain.progress.task_runner import BackgroundTaskRunner
from ....domain.progress.publisher import ProgressPublisher

logger = logging.getLogger(__name__)

# Create router
files_router = APIRouter(prefix="/api/v1/files", tags=["files"])

# Global instances (will be injected in main.py)
_file_processing_service: Optional[FileProcessingService] = None
_task_runner: Optional[BackgroundTaskRunner] = None
_progress_publisher: Optional[ProgressPublisher] = None


def set_file_processing_service(service: FileProcessingService) -> None:
    """Set the global file processing service instance."""
    global _file_processing_service
    _file_processing_service = service
    logger.info("File processing service set for files router")


def set_task_runner(runner: BackgroundTaskRunner) -> None:
    """Set the global task runner instance."""
    global _task_runner
    _task_runner = runner
    logger.info("Task runner set for files router")


def set_progress_publisher(publisher: ProgressPublisher) -> None:
    """Set the global progress publisher instance."""
    global _progress_publisher
    _progress_publisher = publisher
    logger.info("Progress publisher set for files router")


def _get_service() -> FileProcessingService:
    """Get the file processing service instance."""
    if _file_processing_service is None:
        raise RuntimeError("File processing service not initialized")
    return _file_processing_service


def _get_task_runner() -> BackgroundTaskRunner:
    """Get the task runner instance."""
    if _task_runner is None:
        raise RuntimeError("Task runner not initialized")
    return _task_runner


def _get_progress_publisher() -> ProgressPublisher:
    """Get the progress publisher instance."""
    if _progress_publisher is None:
        raise RuntimeError("Progress publisher not initialized")
    return _progress_publisher


@files_router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def process_file(
    file: UploadFile = File(...),
    verbosity: Optional[str] = Form("low", description="Verbosity level: low, medium, high"),
    simulate_delay: Optional[bool] = Form(True, description="Simulate processing delay (for testing)")
):
    """
    Upload and process a file with progress tracking.
    
    This endpoint:
    1. Accepts a file upload
    2. Generates a unique job_id
    3. Returns the job_id immediately (HTTP 202 Accepted)
    4. Submits file processing to background task runner
    5. Client should connect to WebSocket endpoint to receive progress updates
    
    The processing happens asynchronously in a background thread. The client
    can connect to `/api/v1/ws/progress/{job_id}` to receive real-time updates.
    
    Args:
        file: File to process
        verbosity: Verbosity level for progress updates ("low", "medium", "high")
        simulate_delay: Whether to simulate processing delays (for testing/demo)
    
    Returns:
        Dictionary with job_id and status:
        {
            "job_id": "uuid-string",
            "status": "queued",
            "websocket_url": "/api/v1/ws/progress/{job_id}"
        }
    
    Raises:
        HTTPException: If service/runner/publisher not initialized or file processing fails
    """
    try:
        # Get service instances
        service = _get_service()
        runner = _get_task_runner()
        publisher = _get_progress_publisher()
        
        # Read file content
        file_bytes = await file.read()
        filename = file.filename or "unknown"
        
        logger.info(f"Received file upload: {filename} (size: {len(file_bytes)} bytes)")
        
        # Submit processing to background runner
        # The runner will generate a job_id and inject it into the processing function
        job_id = runner.submit(
            service.process_file,
            file_bytes,
            filename=filename,
            progress_publisher=publisher,
            verbosity=verbosity,
            simulate_delay=simulate_delay
        )
        
        logger.info(f"File processing queued with job_id: {job_id}")
        
        # Return job_id immediately
        return {
            "job_id": job_id,
            "status": "queued",
            "websocket_url": f"/api/v1/ws/progress/{job_id}",
            "message": "File processing started. Connect to WebSocket endpoint for progress updates."
        }
    
    except RuntimeError as e:
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File processing service not available"
        )
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@files_router.get("/supported-types")
async def get_supported_file_types():
    """
    Get list of supported file types.
    
    Returns:
        Dictionary with list of supported file extensions
    """
    try:
        service = _get_service()
        supported_types = service.get_supported_file_types()
        
        return {
            "supported_types": supported_types,
            "count": len(supported_types)
        }
    except RuntimeError as e:
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File processing service not available"
        )

