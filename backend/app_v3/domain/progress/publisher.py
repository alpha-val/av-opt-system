"""
Progress publisher/subscriber interface and implementation.

This module provides an abstract interface for publishing progress events
and an in-memory implementation. The interface is designed to be easily
swappable with a Redis-based implementation for multi-process deployments.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional
from threading import Lock

from .events import ProgressEvent

logger = logging.getLogger(__name__)


class ProgressPublisher(ABC):
    """
    Abstract base class for progress event publishers.
    
    This interface defines the contract for publishing and subscribing to
    progress events. Implementations can use in-memory queues (for single
    process) or Redis pub/sub (for multi-process deployments).
    
    The key design principle is that subscribers register callbacks for
    specific job_ids, and publishers emit events that are routed to the
    appropriate subscribers.
    """
    
    @abstractmethod
    def publish(self, job_id: str, event: ProgressEvent) -> None:
        """
        Publish a progress event for a specific job.
        
        Args:
            job_id: Unique identifier for the processing job
            event: Progress event to publish
        """
        pass
    
    @abstractmethod
    def subscribe(
        self,
        job_id: str,
        callback: Callable[[ProgressEvent], None]
    ) -> None:
        """
        Subscribe to progress events for a specific job.
        
        Args:
            job_id: Unique identifier for the processing job
            callback: Function to call when an event is published for this job
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, job_id: str) -> None:
        """
        Unsubscribe from progress events for a specific job.
        
        Args:
            job_id: Unique identifier for the processing job
        """
        pass


class InMemoryProgressPublisher(ProgressPublisher):
    """
    In-memory implementation of ProgressPublisher.
    
    This implementation uses Python dictionaries and asyncio queues to
    manage subscriptions and event routing. It's suitable for single-process
    deployments and provides a simple, fast implementation.
    
    For multi-process deployments, you can swap this with a Redis-based
    implementation that implements the same ProgressPublisher interface.
    
    Thread-safety is ensured using locks for subscription management.
    """
    
    def __init__(self):
        """
        Initialize the in-memory publisher.
        
        Creates internal data structures for managing subscriptions:
        - _subscribers: Maps job_id to list of callback functions
        - _lock: Thread lock for thread-safe subscription management
        """
        # Map job_id -> list of callback functions
        self._subscribers: Dict[str, List[Callable[[ProgressEvent], None]]] = {}
        # Thread lock for thread-safe operations
        self._lock = Lock()
        logger.info("Initialized InMemoryProgressPublisher")
    
    def publish(self, job_id: str, event: ProgressEvent) -> None:
        """
        Publish a progress event to all subscribers for the given job_id.
        
        This method is thread-safe and will call all registered callbacks
        synchronously. If a callback raises an exception, it's logged but
        doesn't prevent other callbacks from being called.
        
        Args:
            job_id: Unique identifier for the processing job
            event: Progress event to publish
        """
        with self._lock:
            callbacks = self._subscribers.get(job_id, [])
        
        if not callbacks:
            logger.debug(f"No subscribers for job_id: {job_id}")
            return
        
        logger.debug(
            f"Publishing event for job_id {job_id}: "
            f"stage={event.stage.value}, status={event.status.value}, "
            f"progress={event.progress}%"
        )
        
        # Call all registered callbacks
        # We iterate over a copy to avoid issues if callbacks modify subscriptions
        for callback in callbacks[:]:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in progress callback for job_id {job_id}: {e}",
                    exc_info=True
                )
    
    def subscribe(
        self,
        job_id: str,
        callback: Callable[[ProgressEvent], None]
    ) -> None:
        """
        Subscribe a callback function to progress events for a job_id.
        
        The callback will be called whenever an event is published for
        this job_id. Multiple callbacks can be registered for the same job_id.
        
        Args:
            job_id: Unique identifier for the processing job
            callback: Function to call when an event is published
        """
        with self._lock:
            if job_id not in self._subscribers:
                self._subscribers[job_id] = []
            self._subscribers[job_id].append(callback)
            logger.debug(f"Subscribed callback for job_id: {job_id}")
    
    def unsubscribe(self, job_id: str) -> None:
        """
        Unsubscribe all callbacks for a specific job_id.
        
        This removes all registered callbacks for the job_id, effectively
        cleaning up subscriptions when a job is complete or a WebSocket
        connection is closed.
        
        Args:
            job_id: Unique identifier for the processing job
        """
        with self._lock:
            if job_id in self._subscribers:
                del self._subscribers[job_id]
                logger.debug(f"Unsubscribed all callbacks for job_id: {job_id}")
    
    def get_subscriber_count(self, job_id: str) -> int:
        """
        Get the number of subscribers for a job_id.
        
        Useful for debugging and monitoring.
        
        Args:
            job_id: Unique identifier for the processing job
            
        Returns:
            Number of active subscribers for this job_id
        """
        with self._lock:
            return len(self._subscribers.get(job_id, []))
    
    def get_all_job_ids(self) -> List[str]:
        """
        Get all job_ids that have active subscriptions.
        
        Useful for debugging and monitoring.
        
        Returns:
            List of job_ids with active subscriptions
        """
        with self._lock:
            return list(self._subscribers.keys())

