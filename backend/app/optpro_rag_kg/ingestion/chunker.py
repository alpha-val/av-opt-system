from typing import List, Dict, Any
from ..utils.ids import stable_id
from .pdf_parser import parse_pdf
from ..utils.logging import get_logger
import spacy
import os, re, unicodedata

# Optional: Token counter if available
try:
    import tiktoken

    enc = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(text: str) -> int:
        return len(enc.encode(text))

except ImportError:
    enc = None

    def count_tokens(text: str) -> int:
        return len(text) // 4  # rough approximation


log = get_logger(__name__)
nlp = spacy.load("en_core_web_md")
nlp.add_pipe("sentencizer")


def _normalize_chunk_text(t: str) -> str:
    if not t:
        return ""
    # Replace non-breaking spaces and newlines
    t = t.replace("\xa0", " ").replace("\n", " ").strip()
    # Unicode normalization & thin spaces
    t = unicodedata.normalize("NFC", t).replace("\u2009", " ").replace("\ufeff", "")
    # Standardize bullets
    t = t.replace("●", "•")
    # Collapse pattern: newline + (only spaces or a single space line) + newline => single space
    # This removes the per‑word line breaks pattern: "Word\n \nNext"
    t = re.sub(r"\n[ \t]*\n", " ", t)
    # Remove leftover isolated newlines immediately followed by lowercase/number (word wraps)
    t = re.sub(r"\n(?=[a-z0-9])", " ", t)
    # Compress multiple spaces
    t = re.sub(r"[ \t]{2,}", " ", t)
    # Restore paragraph breaks where we accidentally flattened true blank lines:
    # Heuristic: if we flattened a period followed by a capital, keep as is (fine for LLMs).
    # Ensure bullets start on new line
    t = re.sub(r"\s*•\s*", "\n• ", t)
    return t.strip()


def chunk_text(
    pdf_bytes: bytes,
    doc_id: str,
    title: str,
    max_tokens: int = 350,
    overlap_chars: int = 100,
) -> List[Dict[str, Any]]:
    """
    Splits PDF text into chunks respecting sentence boundaries, with token budget and character overlap.
    """

    # Use page-aware PDF parser if available
    full_text, pages = parse_pdf(pdf_bytes)  # full_text: str, pages: List[str]
    doc = nlp(full_text)
    sentences = [_normalize_chunk_text(sent.text) for sent in doc.sents if sent.text.strip()]

    chunks = []
    buf = []
    token_buf = 0
    section_idx = 0

    for idx, sentence in enumerate(sentences):
        sentence_tokens = count_tokens(sentence)

        # If adding this sentence would overflow, flush current buffer first
        if buf and token_buf + sentence_tokens > max_tokens:
            chunk_text = " ".join(buf)
            section_id = f"{doc_id}_sec_{section_idx:03d}"
            chunk_id = stable_id(section_id, chunk_text)

            chunks.append(
                {
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "document_id": doc_id,
                    "section_id": section_id,
                    "title": title,
                    "text": chunk_text,
                    "page_start": 0,
                    "page_end": 0,
                    "entity_ids": [],
                    "metadata": {},
                }
            )

            # Handle overlap
            if overlap_chars > 0:
                overlap_text = chunk_text[-overlap_chars:]
                overlap_doc = nlp(overlap_text)
                buf = [
                    _normalize_chunk_text(sent.text)
                    for sent in overlap_doc.sents
                    if sent.text.strip()
                ]
                token_buf = sum(count_tokens(s) for s in buf)
            else:
                buf = []
                token_buf = 0

            section_idx += 1

        # Always append current sentence *after* flush logic
        buf.append(sentence)
        token_buf += sentence_tokens

    # Flush final buffer
    if buf:
        chunk_text = " ".join(buf)
        section_id = f"{doc_id}_sec_{section_idx:03d}"
        chunk_id = stable_id(section_id, chunk_text)
        chunks.append(
            {
                "id": chunk_id,
                "doc_id": doc_id,
                "document_id": doc_id,
                "section_id": section_id,
                "title": title,
                "text": chunk_text,
                "page_start": 0,
                "page_end": 0,
                "entity_ids": [],
                "metadata": {},
            }
        )    

    return chunks