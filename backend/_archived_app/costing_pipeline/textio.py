"""
PDF text extraction + chunking utilities.
- Uses PyPDF2 for PDF text extraction (lightweight).
- Provides token-aware chunking if tiktoken is available; falls back to char-based.
"""

from __future__ import annotations
from typing import List, Dict, Any
import re
from uuid import uuid5
from .config_adapter import NAMESPACE


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

def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # 1. Normalize unicode spaces
    text = text.replace("\u2009", " ")  # thin space
    text = text.replace("\u00a0", " ")  # non-breaking space

    # 2. Replace bullets with dash
    text = text.replace("●", "-")

    # 3. Remove hyphenation across lines (e.g. "Car-\nson")
    text = re.sub(r"-\s*\n\s*", "", text)

    # 4. Collapse linebreaks that are *not* paragraph breaks
    # Any newline not followed by another newline = sentence continuation
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # 5. Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    # 6. Collapse multiple newlines but keep paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


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


def chunk_text(
    text: str,
    chunk_size: int = 1200,  # tokens if tiktoken present; else characters
    chunk_overlap: int = 200,
    encoding_name: str = "cl100k_base",
) -> List[Dict[str, Any]]:
    """
    Returns a list of chunks: [{ "text": str, "seq": int, "meta": {...} }, ...]
    - If tiktoken is available: token-based chunking with token offsets (tok_start/tok_end).
    - Otherwise: character-based chunking with char offsets (start/end).
    NOTE: No chunk_id is assigned here; do that deterministically later (doc_id|seq).
    """
    if not text or not text.strip():
        return []

    chunks: List[Dict[str, Any]] = []

    # --- Character-based fallback ---
    if tiktoken is None:
        L = len(text)
        start = 0
        seq = 0
        while start < L:
            end = min(start + chunk_size, L)
            piece = text[start:end]
            chunks.append(
                {
                    "text": piece,
                    "seq": seq,
                    "meta": {"start": start, "end": end},
                }
            )
            if end == L:
                break
            start = max(0, end - chunk_overlap)
            seq += 1
        return chunks

    # --- Token-based chunking ---
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    n = len(tokens)
    start = 0
    seq = 0
    while start < n:
        end = min(start + chunk_size, n)
        # decode the token slice back to text; we keep token offsets for provenance
        piece = enc.decode(tokens[start:end])
        chunks.append(
            {
                "text": piece,
                "seq": seq,
                "meta": {"tok_start": start, "tok_end": end},
            }
        )
        if end == n:
            break
        start = max(0, end - chunk_overlap)
        seq += 1

    return chunks


def normalize_chunks_for_ingest(raw_chunks, doc_id: str, namespace: str):
    """
    Normalize raw chunk dicts -> deterministic identity for cross-system joins.
    Returns list of dicts ready for Pinecone + Neo4j upsert.
    """
    norm = []
    print(
        f"[INGEST 4.1] Normalizing chunks for doc_id={doc_id}, namespace={namespace}, chunks: {len(raw_chunks)}"
    )
    print("[INGEST 4.2] NAMESPACE =", NAMESPACE)
    try:
        for i, ch in enumerate(raw_chunks):
            seq = int(ch.get("seq", ch.get("chunk_idx", i)))
            text = (ch.get("text") or "").strip()
            # deterministic, namespace-agnostic chunk id
            chunk_id = str(uuid5(NAMESPACE, f"{doc_id}|{seq}"))

            print(f"[DEBUG] normalizing chunk {chunk_id} (seq={seq})")

            norm.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "seq": seq,
                    "text": text,
                    "page": ch.get("page"),
                    "namespace": namespace,  # where you'll store the vector, not part of ID
                }
            )
        print(f"[INGEST 4.4] - Normalized len: {len(norm)}")
        return norm
    except Exception as e:
        print(f"[ERROR] Failed to normalize chunks: {e}")
        return []
