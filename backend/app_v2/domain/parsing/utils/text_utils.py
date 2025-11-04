"""Text processing utilities for PDF extraction and cleaning."""

from __future__ import annotations
from typing import List, Tuple, Dict, Any
import io
import json
import re
import hashlib
import uuid
import pdfplumber

# Fixed namespace for deterministic UUID5 generation across the app
NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")


def sha256_bytes(b: bytes) -> str:
    """Calculate SHA256 hash of bytes."""
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def make_doc_id(filename: str, file_sha256: str) -> str:
    """Generate stable document ID from filename and SHA256 hash."""
    # Stable across re-ingests of same file content+name
    return str(uuid.uuid5(NAMESPACE, f"pdf|{file_sha256}|{filename or ''}"))


def extract_text_per_page(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """Return list of (1-indexed page_num, raw_text)."""
    out: List[Tuple[int, str]] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text(x_tolerance=1.5, y_tolerance=1.5) or ""
            out.append((i, txt))
    return out


# --- Cleaning utilities ---


def _dehyphenate(text: str) -> str:
    """Remove hyphenation from line breaks."""
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)


def _collapse_ws(text: str) -> str:
    """Collapse whitespace in text."""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _strip_repeating_header_footer(
    pages: List[Tuple[int, str]],
) -> List[Tuple[int, str]]:
    """Drop repeated header/footer lines if they appear on ≥60% of pages."""

    def first_last_lines(t: str):
        lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
        return (lines[0], lines[-1]) if lines else ("", "")

    first_counts, last_counts = {}, {}
    for _, raw in pages:
        f, l = first_last_lines(raw)
        if f:
            first_counts[f] = first_counts.get(f, 0) + 1
        if l:
            last_counts[l] = last_counts.get(l, 0) + 1

    n = max(1, len(pages))
    header = next((k for k, v in first_counts.items() if v / n >= 0.6), None)
    footer = next((k for k, v in last_counts.items() if v / n >= 0.6), None)

    cleaned: List[Tuple[int, str]] = []
    for p, raw in pages:
        lines = [ln for ln in raw.splitlines()]
        if header and lines and lines[0].strip() == header:
            lines = lines[1:]
        if footer and lines and lines[-1].strip() == footer:
            lines = lines[:-1]
        cleaned.append((p, "\n".join(lines)))
    return cleaned


def clean_text(text: str) -> str:
    """Clean text by removing hyphenation and collapsing whitespace."""
    return _collapse_ws(_dehyphenate(text))


def chunk_by_page(
    clean_pages: List[Tuple[int, str]], doc_id: str
) -> List[Dict[str, Any]]:
    """Create chunks: 1 chunk per page. chunk_id = uuid5(doc_id|seq)."""
    chunks: List[Dict[str, Any]] = []
    for seq, (page, txt) in enumerate(clean_pages, start=1):
        chunk_id = str(uuid.uuid5(NAMESPACE, f"{doc_id}|{seq}"))
        chunks.append(
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "seq": seq,
                "page": page,
                "text": txt,
            }
        )
    return chunks


def chunk_by_character_limit(
    full_document_text: str, doc_id: str, char_limit: int = 5000
) -> List[Dict[str, Any]]:
    """Chunk the full document text into smaller chunks based on character limit."""
    chunks: List[Dict[str, Any]] = []
    current_pos = 0
    seq = 1

    while current_pos < len(full_document_text):
        chunk_text = full_document_text[current_pos : current_pos + char_limit]
        chunk_id = str(uuid.uuid5(NAMESPACE, f"{doc_id}|{seq}"))
        chunks.append(
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "seq": seq,
                "text": chunk_text,
            }
        )
        current_pos += char_limit
        seq += 1

    return chunks


def extract_fulltext(pages_clean: list[tuple[int, str]]) -> str:
    """Extract full text from cleaned pages."""
    # pages_clean is [(page_num, text), ...]
    pages_clean_sorted = sorted(pages_clean, key=lambda x: x[0])
    full_text = "\n\n".join(
        [f"[Page {p}]\n{t}" for p, t in pages_clean_sorted if t and t.strip()]
    )
    return full_text


def extract_and_clean(pdf_bytes: bytes, filename: str):
    """
    Extract and clean text from PDF.
    
    Returns:
      doc_id, file_sha256, pages_raw[(page, raw)], pages_clean[(page, clean)]
    """
    file_sha = sha256_bytes(pdf_bytes)
    # doc_id = make_doc_id(filename, file_sha)
    doc_id = str(uuid.uuid4())  # Use random UUID for doc_id to allow re-ingest
    pages_raw = extract_text_per_page(pdf_bytes)
    pages_no_hf = _strip_repeating_header_footer(pages_raw)
    pages_clean = [(p, clean_text(t)) for p, t in pages_no_hf]
    return doc_id, file_sha, pages_raw, pages_clean


def sanitize_metadata(metadata: dict) -> dict:
    """
    Ensure metadata values are of supported types for Pinecone.
    Supported types: string, number, boolean, list of strings.
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            sanitized[key] = value
        else:
            # Convert unsupported types (e.g., dicts) to strings
            sanitized[key] = (
                json.dumps(value) if isinstance(value, dict) else str(value)
            )
    return sanitized

