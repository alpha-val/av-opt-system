"""
Byte-based chunking strategy.

Chunks binary content or text based on byte limits.
"""

from typing import List, Dict, Any, Optional
from .base import BaseChunker
import logging

logger = logging.getLogger(__name__)


class ByteChunker(BaseChunker):
    """Chunk content by byte limit."""
    
    def __init__(
        self,
        doc_id: str,
        namespace,
        byte_limit: int = 5000
    ):
        """
        Initialize byte chunker.
        
        Args:
            doc_id: Document identifier
            namespace: UUID namespace for chunk ID generation
            byte_limit: Maximum bytes per chunk (default: 5000)
        """
        super().__init__(doc_id, namespace)
        self.byte_limit = byte_limit
    
    def chunk(
        self,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk binary content by byte limit.
        
        Args:
            content: Binary content as bytes
            metadata: Optional metadata (artifact_type, project_id, user_id, etc.)
            
        Returns:
            List of chunk dictionaries
        """
        if not content:
            logger.warning(f"No content provided for chunking (doc_id: {self.doc_id})")
            return []
        
        chunks = []
        seq = 1
        current_pos = 0
        
        while current_pos < len(content):
            chunk_bytes = content[current_pos : current_pos + self.byte_limit]
            
            # Generate chunk ID
            chunk_id = self._generate_chunk_id(seq)
            
            # Create chunk dictionary
            chunk = {
                "id": chunk_id,
                "chunk_id": chunk_id,
                "doc_id": self.doc_id,
                "seq": seq,
                "text": chunk_bytes.decode("utf-8", errors="replace"),  # Decode for text storage
                "byte_length": len(chunk_bytes),
                "byte_start": current_pos,
                "byte_end": current_pos + len(chunk_bytes),
            }
            
            # Add metadata
            chunk = self._add_metadata(chunk, metadata)
            
            chunks.append(chunk)
            
            current_pos += self.byte_limit
            seq += 1
        
        logger.info(
            f"Chunked document {self.doc_id} into {len(chunks)} chunks "
            f"(byte_limit: {self.byte_limit})"
        )
        
        return chunks

