"""
Background task runner for asynchronous file processing.

This module provides a wrapper around ThreadPoolExecutor (or ProcessPoolExecutor)
that integrates with the progress publishing system. It allows processing
functions to run in the background while still emitting progress updates.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Callable, Any, Optional, Dict
from threading import Lock

from .publisher import ProgressPublisher
from .events import ProgressEvent, Stage, Status

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """
    Background task executor with progress tracking integration.
    
    This class wraps a ThreadPoolExecutor (or ProcessPoolExecutor) and
    provides methods for submitting processing tasks that can emit progress
    events. It tracks active jobs and handles error reporting.
    
    The key design is that processing functions receive a job_id and
    progress_publisher, allowing them to emit progress updates that are
    routed to WebSocket connections.
    
    Example:
        runner = BackgroundTaskRunner(max_workers=4)
        job_id = runner.submit(
            process_file,
            file_bytes,
            job_id=None,  # Will be auto-generated
            progress_publisher=publisher,
            filename="example.pdf"
        )
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        use_processes: bool = False
    ):
        """
        Initialize the background task runner.
        
        Args:
            max_workers: Maximum number of worker threads/processes
            use_processes: If True, use ProcessPoolExecutor instead of ThreadPoolExecutor
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        
        # Create executor based on configuration
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
            logger.info(f"Initialized BackgroundTaskRunner with ProcessPoolExecutor (max_workers={max_workers})")
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            logger.info(f"Initialized BackgroundTaskRunner with ThreadPoolExecutor (max_workers={max_workers})")
        
        # Track active jobs: job_id -> Future
        self._active_jobs: Dict[str, Any] = {}
        self._lock = Lock()
    
    def submit(
        self,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        progress_publisher: Optional[ProgressPublisher] = None,
        **kwargs
    ) -> str:
        """
        Submit a processing function to run in the background.
        
        This method wraps the function call to handle job_id generation,
        error reporting, and progress event emission. The function should
        accept job_id and progress_publisher as keyword arguments.
        
        Args:
            func: Processing function to execute
            *args: Positional arguments to pass to func
            job_id: Optional job ID (auto-generated if not provided)
            progress_publisher: Progress publisher instance (required for progress tracking)
            **kwargs: Keyword arguments to pass to func
            
        Returns:
            Job ID for tracking this task
            
        Raises:
            ValueError: If progress_publisher is None
        """
        if progress_publisher is None:
            raise ValueError("progress_publisher is required for progress tracking")
        
        # Generate job_id if not provided
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        # Inject job_id and progress_publisher into kwargs
        kwargs['job_id'] = job_id
        kwargs['progress_publisher'] = progress_publisher
        
        # Wrap function to handle errors and emit initial/error events
        def wrapped_func(*fargs, **fkwargs):
            """Wrapper function that handles progress events and errors."""
            try:
                # Emit initial event
                initial_event = ProgressEvent(
                    job_id=job_id,
                    stage=Stage.FILE_UPLOAD,
                    status=Status.STARTED,
                    progress=0,
                    seq=0,
                    meta={"message": "Processing started"}
                )
                progress_publisher.publish(job_id, initial_event)
                
                # Call the actual processing function
                result = func(*fargs, **fkwargs)
                
                # Emit completion event (if function didn't already)
                # Note: The function should emit COMPLETE event itself,
                # but we emit one here as a safety net
                complete_event = ProgressEvent(
                    job_id=job_id,
                    stage=Stage.COMPLETE,
                    status=Status.COMPLETED,
                    progress=100,
                    seq=999,  # High seq number
                    meta={"message": "Processing completed successfully"}
                )
                progress_publisher.publish(job_id, complete_event)
                
                return result
                
            except Exception as e:
                # Emit error event
                error_event = ProgressEvent(
                    job_id=job_id,
                    stage=Stage.ERROR,
                    status=Status.FAILED,
                    progress=0,
                    seq=999,
                    meta={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "message": "Processing failed"
                    }
                )
                progress_publisher.publish(job_id, error_event)
                logger.error(f"Error in background task {job_id}: {e}", exc_info=True)
                raise
        
        # Submit to executor
        future = self.executor.submit(wrapped_func, *args, **kwargs)
        
        # Track the job
        with self._lock:
            self._active_jobs[job_id] = future
        
        logger.info(f"Submitted background task with job_id: {job_id}")
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """
        Get the status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Status string: "running", "done", "cancelled", or None if not found
        """
        with self._lock:
            future = self._active_jobs.get(job_id)
        
        if future is None:
            return None
        
        if future.done():
            if future.cancelled():
                return "cancelled"
            return "done"
        return "running"
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found or already done
        """
        with self._lock:
            future = self._active_jobs.get(job_id)
        
        if future is None:
            return False
        
        if future.done():
            return False
        
        cancelled = future.cancel()
        if cancelled:
            logger.info(f"Cancelled job: {job_id}")
            with self._lock:
                del self._active_jobs[job_id]
        
        return cancelled
    
    def get_active_job_ids(self) -> list:
        """
        Get list of active job IDs.
        
        Returns:
            List of job IDs that are currently running
        """
        with self._lock:
            return [
                job_id for job_id, future in self._active_jobs.items()
                if not future.done()
            ]
    
    def cleanup_completed_jobs(self) -> int:
        """
        Remove completed jobs from tracking.
        
        This is a cleanup method that can be called periodically to
        prevent memory leaks from accumulating completed job futures.
        
        Returns:
            Number of jobs cleaned up
        """
        with self._lock:
            completed = [
                job_id for job_id, future in self._active_jobs.items()
                if future.done()
            ]
            for job_id in completed:
                del self._active_jobs[job_id]
        
        if completed:
            logger.debug(f"Cleaned up {len(completed)} completed jobs")
        
        return len(completed)
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor and wait for tasks to complete.
        
        Args:
            wait: If True, wait for all tasks to complete before returning
        """
        logger.info("Shutting down BackgroundTaskRunner...")
        self.executor.shutdown(wait=wait)
        with self._lock:
            self._active_jobs.clear()
        logger.info("BackgroundTaskRunner shutdown complete")

