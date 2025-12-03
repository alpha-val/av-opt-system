"""
Text extraction from PDF files.

Wraps existing text cleaning functionality for the new pipeline.
"""

from typing import Tuple, List, Optional
from ..utils.text_utils import extract_and_clean, extract_fulltext
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract and clean text from PDF files."""
    
    def extract(
        self,
        pdf_bytes: bytes,
        filename: str,
        pages: Optional[str] = None
    ) -> Tuple[str, str, List[Tuple[int, str]], List[Tuple[int, str]]]:
        """
        Extract and clean text from PDF.
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename
            pages: Optional page range filter (e.g., "1-5,10")
            
        Returns:
            Tuple of (doc_id, file_sha256, pages_raw, pages_clean)
            - doc_id: Generated document identifier
            - file_sha256: SHA256 hash of file content
            - pages_raw: List of (page_num, raw_text) tuples
            - pages_clean: List of (page_num, cleaned_text) tuples
        """
        logger.info(f"Extracting text from {filename}")
        
        # Extract and clean using existing functionality
        doc_id, file_sha, pages_raw, pages_clean = extract_and_clean(
            pdf_bytes, filename
        )
        
        # Apply page filtering if specified
        if pages:
            pages_clean = self._filter_pages(pages_clean, pages)
            pages_raw = self._filter_pages(pages_raw, pages)
        
        logger.info(
            f"Extracted {len(pages_clean)} pages from {filename} "
            f"(SHA256: {file_sha[:8]}...)"
        )
        
        return doc_id, file_sha, pages_raw, pages_clean
    
    def extract_full_text(
        self,
        pages_clean: List[Tuple[int, str]]
    ) -> str:
        """
        Extract full text from cleaned pages.
        
        Args:
            pages_clean: List of (page_num, cleaned_text) tuples
            
        Returns:
            Full document text as single string
        """
        return extract_fulltext(pages_clean)
    
    def _filter_pages(
        self,
        pages: List[Tuple[int, str]],
        page_spec: str
    ) -> List[Tuple[int, str]]:
        """
        Filter pages based on page specification.
        
        Supports formats like:
        - "1-5" -> pages 1 through 5
        - "1,3,5" -> pages 1, 3, and 5
        - "1-5,10,20-25" -> combination
        
        Args:
            pages: List of (page_num, text) tuples
            page_spec: Page specification string
            
        Returns:
            Filtered list of pages
        """
        if not page_spec:
            return pages
        
        # Parse page ranges
        page_nums = set()
        for part in page_spec.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                page_nums.update(range(start, end + 1))
            else:
                page_nums.add(int(part))
        
        # Filter pages
        filtered = [(p, t) for p, t in pages if p in page_nums]
        
        logger.debug(f"Filtered to {len(filtered)} pages from {len(pages)} total")
        
        return filtered

