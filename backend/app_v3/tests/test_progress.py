"""
Tests for progress tracking infrastructure.

This module contains unit tests for the progress tracking system,
including event schema, publisher, context manager, and task runner.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock

from ..domain.progress.events import ProgressEvent, Stage, Status, Verbosity
from ..domain.progress.publisher import InMemoryProgressPublisher
from ..domain.progress.context import ProgressContext
from ..domain.progress.task_runner import BackgroundTaskRunner


class TestProgressEvent:
    """Test cases for ProgressEvent dataclass."""
    
    def test_create_event(self):
        """Test creating a progress event."""
        event = ProgressEvent(
            job_id="test-job-123",
            stage=Stage.EXTRACTION,
            status=Status.STARTED,
            progress=50
        )
        
        assert event.job_id == "test-job-123"
        assert event.stage == Stage.EXTRACTION
        assert event.status == Status.STARTED
        assert event.progress == 50
        assert event.seq == 0
        assert event.meta is None
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = ProgressEvent(
            job_id="test-job-123",
            stage=Stage.COMPLETE,
            status=Status.COMPLETED,
            progress=100,
            seq=5,
            meta={"items": 10}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["job_id"] == "test-job-123"
        assert event_dict["stage"] == "complete"
        assert event_dict["status"] == "completed"
        assert event_dict["progress"] == 100
        assert event_dict["seq"] == 5
        assert event_dict["meta"]["items"] == 10
        assert "timestamp" in event_dict
    
    def test_progress_validation(self):
        """Test that progress value is validated."""
        # Valid progress values
        event1 = ProgressEvent(
            job_id="test",
            stage=Stage.FILE_UPLOAD,
            status=Status.STARTED,
            progress=0
        )
        assert event1.progress == 0
        
        event2 = ProgressEvent(
            job_id="test",
            stage=Stage.COMPLETE,
            status=Status.COMPLETED,
            progress=100
        )
        assert event2.progress == 100
        
        # Invalid progress values
        with pytest.raises(ValueError):
            ProgressEvent(
                job_id="test",
                stage=Stage.FILE_UPLOAD,
                status=Status.STARTED,
                progress=-1
            )
        
        with pytest.raises(ValueError):
            ProgressEvent(
                job_id="test",
                stage=Stage.FILE_UPLOAD,
                status=Status.STARTED,
                progress=101
            )


class TestInMemoryProgressPublisher:
    """Test cases for InMemoryProgressPublisher."""
    
    def test_publish_and_subscribe(self):
        """Test publishing and subscribing to events."""
        publisher = InMemoryProgressPublisher()
        callback = Mock()
        
        # Subscribe to job_id
        publisher.subscribe("job-123", callback)
        
        # Publish event
        event = ProgressEvent(
            job_id="job-123",
            stage=Stage.EXTRACTION,
            status=Status.STARTED,
            progress=10
        )
        publisher.publish("job-123", event)
        
        # Verify callback was called
        callback.assert_called_once_with(event)
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same job_id."""
        publisher = InMemoryProgressPublisher()
        callback1 = Mock()
        callback2 = Mock()
        
        publisher.subscribe("job-123", callback1)
        publisher.subscribe("job-123", callback2)
        
        event = ProgressEvent(
            job_id="job-123",
            stage=Stage.EXTRACTION,
            status=Status.STARTED,
            progress=10
        )
        publisher.publish("job-123", event)
        
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        publisher = InMemoryProgressPublisher()
        callback = Mock()
        
        publisher.subscribe("job-123", callback)
        publisher.unsubscribe("job-123")
        
        event = ProgressEvent(
            job_id="job-123",
            stage=Stage.EXTRACTION,
            status=Status.STARTED,
            progress=10
        )
        publisher.publish("job-123", event)
        
        # Callback should not be called after unsubscribe
        callback.assert_not_called()
    
    def test_publish_without_subscribers(self):
        """Test publishing when no subscribers exist."""
        publisher = InMemoryProgressPublisher()
        
        event = ProgressEvent(
            job_id="job-123",
            stage=Stage.EXTRACTION,
            status=Status.STARTED,
            progress=10
        )
        
        # Should not raise an error
        publisher.publish("job-123", event)


class TestProgressContext:
    """Test cases for ProgressContext."""
    
    def test_emit_stage(self):
        """Test emitting stage updates."""
        publisher = InMemoryProgressPublisher()
        callback = Mock()
        publisher.subscribe("job-123", callback)
        
        with ProgressContext("job-123", publisher) as ctx:
            ctx.emit_stage(Stage.EXTRACTION, Status.STARTED, 10)
            ctx.emit_stage(Stage.EXTRACTION, Status.COMPLETED, 20)
        
        # Verify events were published
        assert callback.call_count == 2
        
        # Check first event
        first_event = callback.call_args_list[0][0][0]
        assert first_event.stage == Stage.EXTRACTION
        assert first_event.status == Status.STARTED
        assert first_event.progress == 10
        assert first_event.seq == 0
        
        # Check second event
        second_event = callback.call_args_list[1][0][0]
        assert second_event.stage == Stage.EXTRACTION
        assert second_event.status == Status.COMPLETED
        assert second_event.progress == 20
        assert second_event.seq == 1
    
    def test_emit_error(self):
        """Test emitting error events."""
        publisher = InMemoryProgressPublisher()
        callback = Mock()
        publisher.subscribe("job-123", callback)
        
        with ProgressContext("job-123", publisher) as ctx:
            ctx.emit_error(ValueError("Test error"), meta={"key": "value"})
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.stage == Stage.ERROR
        assert event.status == Status.FAILED
        assert "error_type" in event.meta
        assert "error_message" in event.meta
        assert event.meta["key"] == "value"
    
    def test_sequence_numbering(self):
        """Test that sequence numbers are auto-incremented."""
        publisher = InMemoryProgressPublisher()
        callback = Mock()
        publisher.subscribe("job-123", callback)
        
        with ProgressContext("job-123", publisher) as ctx:
            ctx.emit_stage(Stage.FILE_UPLOAD, Status.STARTED, 0)
            ctx.emit_stage(Stage.EXTRACTION, Status.STARTED, 10)
            ctx.emit_stage(Stage.PROCESSING, Status.STARTED, 20)
        
        assert callback.call_count == 3
        
        # Verify sequence numbers
        events = [call[0][0] for call in callback.call_args_list]
        assert events[0].seq == 0
        assert events[1].seq == 1
        assert events[2].seq == 2


class TestBackgroundTaskRunner:
    """Test cases for BackgroundTaskRunner."""
    
    def test_submit_task(self):
        """Test submitting a task to the runner."""
        publisher = InMemoryProgressPublisher()
        runner = BackgroundTaskRunner(max_workers=2)
        
        def simple_task(job_id, progress_publisher, **kwargs):
            """Simple task that emits a progress event."""
            from ..domain.progress.events import ProgressEvent, Stage, Status
            event = ProgressEvent(
                job_id=job_id,
                stage=Stage.COMPLETE,
                status=Status.COMPLETED,
                progress=100
            )
            progress_publisher.publish(job_id, event)
            return "result"
        
        callback = Mock()
        publisher.subscribe("test-job", callback)
        
        job_id = runner.submit(
            simple_task,
            job_id="test-job",
            progress_publisher=publisher
        )
        
        # Wait for task to complete
        time.sleep(0.5)
        
        # Verify job_id was returned
        assert job_id == "test-job"
        
        # Verify event was published
        callback.assert_called()
        
        # Cleanup
        runner.shutdown(wait=True)
    
    def test_submit_with_auto_generated_job_id(self):
        """Test that job_id is auto-generated if not provided."""
        publisher = InMemoryProgressPublisher()
        runner = BackgroundTaskRunner(max_workers=2)
        
        def simple_task(job_id, progress_publisher, **kwargs):
            return "result"
        
        job_id = runner.submit(
            simple_task,
            progress_publisher=publisher
        )
        
        # Verify job_id was generated
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        
        # Cleanup
        runner.shutdown(wait=True)
    
    def test_get_job_status(self):
        """Test getting job status."""
        publisher = InMemoryProgressPublisher()
        runner = BackgroundTaskRunner(max_workers=2)
        
        def slow_task(job_id, progress_publisher, **kwargs):
            time.sleep(0.1)
            return "result"
        
        job_id = runner.submit(
            slow_task,
            progress_publisher=publisher
        )
        
        # Check status while running
        status = runner.get_job_status(job_id)
        assert status in ["running", "done"]  # May complete quickly
        
        # Wait for completion
        time.sleep(0.2)
        status = runner.get_job_status(job_id)
        assert status == "done"
        
        # Cleanup
        runner.shutdown(wait=True)

