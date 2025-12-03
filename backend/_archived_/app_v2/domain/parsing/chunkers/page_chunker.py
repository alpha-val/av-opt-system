"""
Page-based chunking strategy.

Chunks content by page - one chunk per page.
"""

from typing import List, Dict, Any, Optional, Tuple
from app_v2.domain.parsing.utils.text_utils import chunk_by_page
from .base import BaseChunker
import logging

logger = logging.getLogger(__name__)


class PageChunker(BaseChunker):
    """Chunk text by page."""
    
    def chunk(
        self,
        content: List[Tuple[int, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk pages into one chunk per page.
        
        Args:
            content: List of (page_num, text) tuples
            metadata: Optional metadata (artifact_type, project_id, user_id, etc.)
            
        Returns:
            List of chunk dictionaries (one per page)
        """
        if not content:
            logger.warning(f"No pages provided for chunking (doc_id: {self.doc_id})")
            return []
        
        # Use existing chunk_by_page function
        chunks = chunk_by_page(content, self.doc_id)
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk = self._add_metadata(chunk, metadata)
        
        logger.info(
            f"Chunked document {self.doc_id} into {len(chunks)} chunks "
            f"(one per page)"
        )
        
        return chunks

