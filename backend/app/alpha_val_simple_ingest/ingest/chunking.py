from __future__ import annotations
from typing import List, Tuple, Optional
import re, uuid
import unicodedata
import json
from .models import Chunk


def _clean_text(t: str) -> str:
    # light cleanup
    return re.sub(r"[ \t]+", " ", t).strip()


JSON_CONTROL_CHARS = dict.fromkeys(range(0x00, 0x20))  # C0 controls

def _strip_control_chars(s: str) -> str:
    return s.translate(JSON_CONTROL_CHARS)

def _normalize_unicode(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def _escape_problem_sequences(s: str) -> str:
    # Remove unpaired surrogates (can break JSON)
    return s.encode("utf-8", "ignore").decode("utf-8", "ignore")

# Sanitize a chunk of text for safe JSON embedding
def sanitize_chunk(s: str) -> str:
    # 1. Normalize unicode & drop weird controls
    s = _normalize_unicode(s)
    s = _strip_control_chars(s)
    # 2. Standardize quotes
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    # 3. Replace inch pattern 6" -> 6 in
    s = re.sub(r'(\d+)"', r"\1 in", s)
    # 4. Collapse excessive backslashes (avoid accidental escape storms)
    s = re.sub(r"\\{2,}", r"\\", s)
    # 5. Ensure newlines are plain \n
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # 6. Trim overly long runs of whitespace
    s = re.sub(r"[ \t]{2,}", " ", s)
    # 7. Remove zero-width & BOM
    s = s.replace("\ufeff", "").replace("\u200b", "")
    # 8. Strip any trailing incomplete JSON-looking fragment braces (optional heuristic)
    # (Leave actual JSON assembly to json.dumps; do not over-trim content)
    # 9. Final safe unicode cleanup
    s = _escape_problem_sequences(s)
    # 10. Hard length cap (prevent excessively huge JSON fields)
    MAX_CHARS = 8000
    if len(s) > MAX_CHARS:
        s = s[:MAX_CHARS] + "\n...TRUNCATED..."
    return s

# Chunk a document into overlapping text segments
def chunk_pages(
    doc_id: str,
    filename: str,
    pages: List[Tuple[int, str]],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Chunk]:
    """
    Concatenate pages, then carve into overlapping character chunks.
    Preserve page ranges per chunk and attach a naive section path if detected.
    """
    # Build a combined string with page separators
    segments = []
    page_offsets = []  # [(start_char, end_char, page_num)]
    cursor = 0
    for pg, txt in pages:
        clean = _clean_text(txt)
        segments.append(clean + "\n")
        start = cursor
        cursor += len(clean) + 1
        page_offsets.append((start, cursor, pg))

    full = "".join(segments)

    def page_range_for_span(start_c: int, end_c: int) -> Tuple[int, int]:
        touched = [pg for s, e, pg in page_offsets if not (e <= start_c or s >= end_c)]
        return (min(touched) if touched else 1, max(touched) if touched else 1)

    # naive section path detection (capture last heading-like line encountered)
    headings = set()
    for _, txt in pages:
        for line in txt.splitlines():
            if re.match(r"^(\d+\.?\s*)?[A-Z][A-Z\-\s]{4,}$", line.strip()):
                headings.add(line.strip())

    chunks: List[Chunk] = []
    i = 0
    while i < len(full):
        end = min(len(full), i + chunk_size)
        span = full[i:end]
        span = sanitize_chunk(span)  # <-- sanitization applied here
        ps, pe = page_range_for_span(i, end)
        chunk_id = str(uuid.uuid4())
        section_path = None
        # best-effort: last heading preceding this span (not tracked precisely here)
        section_path = next(iter(headings), None)
        chunks.append(
            Chunk(
                doc_id=doc_id,
                chunk_id=chunk_id,
                filename=filename,
                text=span,
                page_start=ps,
                page_end=pe,
                section_path=section_path,
                meta={"char_start": i, "char_end": end},
            )
        )
        if end == len(full):
            break
        i = end - chunk_overlap  # overlap
        i = max(i, 0)
    return chunks
