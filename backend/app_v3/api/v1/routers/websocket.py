"""
WebSocket router for real-time progress updates.

This module provides a FastAPI WebSocket endpoint that allows clients to
connect and receive real-time progress updates for file processing jobs.
Clients connect to a specific job_id and receive all progress events
emitted for that job.
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from ....domain.progress.publisher import ProgressPublisher
from ....domain.progress.events import ProgressEvent, Verbosity

logger = logging.getLogger(__name__)

# Create router
websocket_router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])

# Export router for main.py
__all__ = ["websocket_router", "set_progress_publisher"]

# Track active WebSocket connections: job_id -> list of WebSocket connections
# This allows multiple clients to subscribe to the same job
_active_connections: dict[str, list[WebSocket]] = {}


def get_progress_publisher() -> ProgressPublisher:
    """
    Get the global progress publisher instance.
    
    This function should be overridden or dependency-injected in the
    actual application. For now, it raises an error to indicate that
    the publisher must be set via set_progress_publisher().
    
    Returns:
        ProgressPublisher instance
        
    Raises:
        RuntimeError: If publisher has not been set
    """
    if not hasattr(get_progress_publisher, '_publisher'):
        raise RuntimeError(
            "Progress publisher not set. Call set_progress_publisher() first."
        )
    return get_progress_publisher._publisher


def set_progress_publisher(publisher: ProgressPublisher) -> None:
    """
    Set the global progress publisher instance.
    
    This should be called during application startup to inject the
    publisher instance that will be used by WebSocket connections.
    
    Args:
        publisher: ProgressPublisher instance
    """
    get_progress_publisher._publisher = publisher
    logger.info("Progress publisher set for WebSocket router")


def _add_connection(job_id: str, websocket: WebSocket) -> None:
    """
    Add a WebSocket connection for a job_id.
    
    Args:
        job_id: Job identifier
        websocket: WebSocket connection
    """
    if job_id not in _active_connections:
        _active_connections[job_id] = []
    _active_connections[job_id].append(websocket)
    logger.debug(f"Added WebSocket connection for job_id: {job_id}")


def _remove_connection(job_id: str, websocket: WebSocket) -> None:
    """
    Remove a WebSocket connection for a job_id.
    
    Args:
        job_id: Job identifier
        websocket: WebSocket connection
    """
    if job_id in _active_connections:
        try:
            _active_connections[job_id].remove(websocket)
            if not _active_connections[job_id]:
                del _active_connections[job_id]
            logger.debug(f"Removed WebSocket connection for job_id: {job_id}")
        except ValueError:
            # Connection not in list (already removed)
            pass


def _create_progress_callback(job_id: str, websocket: WebSocket):
    """
    Create a callback function for progress events.
    
    This callback will be called by the progress publisher whenever
    an event is published for the given job_id. It serializes the
    event to JSON and sends it over the WebSocket.
    
    Args:
        job_id: Job identifier
        websocket: WebSocket connection
        
    Returns:
        Callback function that accepts a ProgressEvent
    """
    async def callback(event: ProgressEvent) -> None:
        """
        Callback function to send progress event over WebSocket.
        
        Args:
            event: Progress event to send
        """
        try:
            # Serialize event to JSON
            event_dict = event.to_dict()
            message = json.dumps(event_dict)
            
            # Send over WebSocket
            await websocket.send_text(message)
            
            # logger.info(
            #     f"Sent progress event to WebSocket: job_id={job_id}, "
            #     f"stage={event.stage.value}, status={event.status.value}, progress={event.progress}%"
            # )
        except Exception as e:
            logger.error(
                f"Error sending progress event to WebSocket for job_id {job_id}: {e}",
                exc_info=True
            )
    
    return callback


@websocket_router.websocket("/progress/{job_id}")
async def websocket_progress(
    websocket: WebSocket,
    job_id: str,
    verbosity: Optional[str] = Query("low", description="Verbosity level: low, medium, high")
):
    """
    WebSocket endpoint for receiving progress updates for a specific job.
    
    Clients connect to this endpoint with a job_id to receive real-time
    progress updates. The connection remains open until the job completes
    or the client disconnects.
    
    Query Parameters:
        verbosity: Verbosity level ("low", "medium", "high") - currently
                   not used but reserved for future filtering
    
    Example:
        ws://localhost:8000/api/v1/ws/progress/123e4567-e89b-12d3-a456-426614174000?verbosity=medium
    
    Args:
        websocket: WebSocket connection
        job_id: Unique identifier for the processing job
        verbosity: Verbosity level (optional, default: "low")
    """
    # Validate verbosity
    try:
        verbosity_enum = Verbosity(verbosity.lower())
    except ValueError:
        await websocket.close(code=1008, reason=f"Invalid verbosity: {verbosity}")
        return
    
    # Accept WebSocket connection
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for job_id: {job_id} (verbosity: {verbosity})")
    
    # Get progress publisher
    try:
        publisher = get_progress_publisher()
    except RuntimeError as e:
        logger.error(f"Failed to get progress publisher: {e}")
        await websocket.close(code=1011, reason="Internal server error: publisher not configured")
        return
    
    # Create callback for progress events
    callback = _create_progress_callback(job_id, websocket)
    
    # Subscribe to progress events for this job_id
    publisher.subscribe(job_id, callback)
    _add_connection(job_id, websocket)
    logger.info(f"WebSocket subscribed to progress events for job_id: {job_id}")
    
    try:
        # Keep connection alive and handle incoming messages
        # Clients can send ping messages to keep connection alive
        while True:
            # Wait for messages from client (ping/pong or close)
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received message from client for job_id {job_id}: {data}")
                
                # Handle ping/pong (optional - can be extended)
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                # Client disconnected normally
                logger.info(f"WebSocket client disconnected for job_id: {job_id}")
                break
                
    except Exception as e:
        logger.error(
            f"Error in WebSocket connection for job_id {job_id}: {e}",
            exc_info=True
        )
    finally:
        # Cleanup: unsubscribe and remove connection
        publisher.unsubscribe(job_id)
        _remove_connection(job_id, websocket)
        logger.info(f"Cleaned up WebSocket connection for job_id: {job_id}")

