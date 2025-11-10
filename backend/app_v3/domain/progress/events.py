"""
Progress event schema and constants.

Defines the standardized structure for progress events that are emitted
during file processing operations. This ensures consistency across all
processing modules and makes it easy for the frontend to render progress.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class Stage(str, Enum):
    """
    Processing stage constants.
    
    These represent the major phases of file processing:
    - FILE_UPLOAD: File has been received and validated
    - EXTRACTION: Extracting content from the file
    - PROCESSING: Processing extracted content (e.g., parsing, transformation)
    - VALIDATION: Validating processed data
    - STORAGE: Storing data in databases/storage systems
    - COMPLETE: Processing is complete
    - ERROR: An error occurred during processing
    """
    FILE_UPLOAD = "file_upload"
    EXTRACTION = "extraction"
    PROCESSING = "processing"
    VALIDATION = "validation"
    STORAGE = "storage"
    COMPLETE = "complete"
    ERROR = "error"


class Status(str, Enum):
    """
    Status constants for each stage.
    
    - STARTED: Stage has just begun
    - IN_PROGRESS: Stage is currently running
    - COMPLETED: Stage has finished successfully
    - FAILED: Stage encountered an error
    """
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Verbosity(str, Enum):
    """
    Verbosity levels for progress reporting.
    
    Controls how much detail is included in progress events:
    - LOW: Only major stage transitions (default)
    - MEDIUM: Stage transitions + key milestones
    - HIGH: Detailed progress including sub-steps
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ProgressEvent:
    """
    Standardized progress event structure.
    
    This dataclass represents a single progress update emitted during
    file processing. All processing functions should emit events using
    this structure to ensure consistency.
    
    Attributes:
        job_id: Unique identifier for the processing job
        stage: Current processing stage (from Stage enum)
        status: Status of the current stage (from Status enum)
        progress: Overall progress percentage (0-100)
        seq: Sequence number for ordering events (auto-incremented)
        meta: Optional metadata dictionary with additional details
        timestamp: When the event was created (auto-generated)
    """
    job_id: str
    stage: Stage
    status: Status
    progress: int  # 0-100
    seq: int = 0
    meta: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "job_id": self.job_id,
            "stage": self.stage.value,
            "status": self.status.value,
            "progress": self.progress,
            "seq": self.seq,
            "meta": self.meta or {},
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __post_init__(self):
        """Validate progress value after initialization."""
        if not 0 <= self.progress <= 100:
            raise ValueError(f"Progress must be between 0 and 100, got {self.progress}")

