"""
Base chunker interface and chunking strategy enum.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class ChunkingStrategy(Enum):
    """Supported chunking strategies."""
    CHARACTER = "character"
    PAGE = "page"
    BYTE = "byte"


class BaseChunker(ABC):
    """Abstract base class for chunkers."""
    
    def __init__(self, doc_id: str, namespace: uuid.UUID):
        """
        Initialize chunker.
        
        Args:
            doc_id: Document identifier
            namespace: UUID namespace for deterministic chunk ID generation
        """
        self.doc_id = doc_id
        self.namespace = namespace
    
    @abstractmethod
    def chunk(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk content into a list of chunk dictionaries.
        
        Args:
            content: Content to chunk (text, bytes, pages, etc.)
            metadata: Optional metadata to include in chunks
            
        Returns:
            List of chunk dictionaries with required fields:
            - id: Unique chunk identifier
            - chunk_id: Same as id
            - doc_id: Document identifier
            - seq: Sequence number (1-indexed)
            - text: Chunk text content
            - properties: Additional properties (artifact_type, project_id, user_id, etc.)
        """
        pass
    
    def _generate_chunk_id(self, seq: int) -> str:
        """
        Generate deterministic chunk ID using UUID5.
        
        Args:
            seq: Sequence number
            
        Returns:
            UUID string
        """
        key = f"{self.doc_id}|{seq}"
        return str(uuid.uuid5(self.namespace, key))
    
    def _add_metadata(
        self,
        chunk: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add metadata to chunk properties.
        
        Args:
            chunk: Chunk dictionary
            metadata: Metadata to add
            
        Returns:
            Updated chunk dictionary
        """
        if metadata:
            if "properties" not in chunk:
                chunk["properties"] = {}
            chunk["properties"].update(metadata)
        
        return chunk

