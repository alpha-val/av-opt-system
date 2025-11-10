"""
Character-based chunking strategy.

Chunks text content based on character limits with optional overlap.
"""

from typing import List, Dict, Any, Optional
from app_v2.domain.parsing.utils.text_utils import chunk_by_character_limit
from .base import BaseChunker
import logging

logger = logging.getLogger(__name__)


class CharacterChunker(BaseChunker):
    """Chunk text by character limit."""
    
    def __init__(
        self,
        doc_id: str,
        namespace,
        char_limit: int = 5000
    ):
        """
        Initialize character chunker.
        
        Args:
            doc_id: Document identifier
            namespace: UUID namespace for chunk ID generation
            char_limit: Maximum characters per chunk (default: 5000)
        """
        super().__init__(doc_id, namespace)
        self.char_limit = char_limit
    
    def chunk(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text content by character limit.
        
        Args:
            content: Full text content as string
            metadata: Optional metadata (artifact_type, project_id, user_id, etc.)
            
        Returns:
            List of chunk dictionaries
        """
        if not content:
            logger.warning(f"No content provided for chunking (doc_id: {self.doc_id})")
            return []
        
        # Use existing chunk_by_character_limit function
        chunks = chunk_by_character_limit(
            content,
            self.doc_id,
            char_limit=self.char_limit
        )
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk = self._add_metadata(chunk, metadata)
        
        logger.info(
            f"Chunked document {self.doc_id} into {len(chunks)} chunks "
            f"(char_limit: {self.char_limit})"
        )
        
        return chunks

