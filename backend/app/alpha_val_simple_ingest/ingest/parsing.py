from __future__ import annotations
import fitz  # PyMuPDF
from typing import List, Tuple, BinaryIO

# Returns list of (page_number (1-based), text)
def extract_pages_from_pdf(stream: BinaryIO) -> List[Tuple[int, str]]:
    pages: List[Tuple[int, str]] = []
    with fitz.open(stream=stream.read(), filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append((i, text))
    return pages
