"""
PDF text extraction + chunking utilities.
- Uses PyPDF2 for PDF text extraction (lightweight).
- Provides token-aware chunking if tiktoken is available; falls back to char-based.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import re

# PDF extraction
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# Optional token-based chunking
try:
    import tiktoken
except Exception:
    tiktoken = None


def extract_text_from_pdf_stream(stream) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 not installed. Please `pip install PyPDF2`.")
    reader = PdfReader(stream)
    parts = []
    for pg in reader.pages:
        try:
            parts.append(pg.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts).strip()


def extract_text_from_pdf_path(path: str) -> str:
    with open(path, "rb") as f:
        return extract_text_from_pdf_stream(f)


def _token_len(text: str, encoding_name: str = "cl100k_base") -> int:
    if tiktoken is None:
        return len(text)
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = 1200,  # ~tokens, if tiktoken present; else characters
    chunk_overlap: int = 200,
    encoding_name: str = "cl100k_base",
) -> List[Dict[str, Any]]:
    """
    Returns list of chunks: [{ "text": "...", "meta": {...} }, ...]
    Keeps overlap context for better downstream extraction/embedding.
    """
    if not text or not text.strip():
        return []

    if tiktoken is None:
        # Fallback = character-based chunking
        chunks = []
        start = 0
        L = len(text)
        while start < L:
            end = min(start + chunk_size, L)
            part = text[start:end]
            chunks.append({"text": part, "meta": {"start": start, "end": end}})
            if end == L:
                break
            start = max(0, end - chunk_overlap)
        return chunks

    # Token-based chunking
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    chunks = []
    start = 0
    n = len(tokens)
    while start < n:
        end = min(start + chunk_size, n)
        piece = enc.decode(tokens[start:end])
        chunks.append({"text": piece, "meta": {"tok_start": start, "tok_end": end}})
        if end == n:
            break
        start = max(0, end - chunk_overlap)
    return chunks
