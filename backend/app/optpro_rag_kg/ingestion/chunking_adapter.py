"""Adapter around user's chunking/parsing modules.
- Uses user's chunker if available, else PyPDF2 fallback.
- Provides Chunk dataclass and extract_chunks_from_pdf_bytes(...).
- Hooks included for advanced parsing/table extraction.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import io

# Try user modules
HAVE_USER_CHUNKER = False
try:
    import chunking as user_chunking
    HAVE_USER_CHUNKER = True
except Exception:
    user_chunking = None

try:
    import parsing as user_parsing
    HAVE_USER_PARSING = True
except Exception:
    HAVE_USER_PARSING = False

# Fallback
try:
    from PyPDF2 import PdfReader
    HAVE_PYPDF = True
except Exception:
    HAVE_PYPDF = False

@dataclass
class Chunk:
    doc_id: str
    chunk_idx: int
    text: str
    filename: str
    page_start: int
    page_end: int
    section_path: Optional[str] = None

# ---- HOOK: ADVANCED_PDF_PARSER_START ----
# Insert richer parser/table extractor here later.
# ---- HOOK: ADVANCED_PDF_PARSER_END ----

def _extract_pages_pypdf(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    if not HAVE_PYPDF:
        return [(1, "")]
    reader = PdfReader(io.BytesIO(pdf_bytes))
    out = []
    for i, p in enumerate(reader.pages, start=1):
        try:
            out.append((i, p.extract_text() or ""))
        except Exception:
            out.append((i, ""))
    return out

def _basic_page_chunker(doc_id: str, filename: str, pages: List[Tuple[int, str]], chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    idx = 0
    for pg, txt in pages:
        text = (txt or "").strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            slice_ = text[start:end]
            chunks.append(Chunk(doc_id=doc_id, chunk_idx=idx, text=slice_, filename=filename, page_start=pg, page_end=pg))
            idx += 1
            if end >= len(text):
                break
            start = max(0, end - chunk_overlap)
    return chunks

def extract_chunks_from_pdf_bytes(doc_id: str, filename: str, pdf_bytes: bytes, chunk_size: int = 1200, chunk_overlap: int = 100) -> List[Chunk]:
    if HAVE_USER_CHUNKER and hasattr(user_chunking, "extract_chunks_from_pdf_bytes"):
        return user_chunking.extract_chunks_from_pdf_bytes(doc_id, filename, pdf_bytes, chunk_size, chunk_overlap)
    pages = _extract_pages_pypdf(pdf_bytes)
    return _basic_page_chunker(doc_id, filename, pages, chunk_size, chunk_overlap)
