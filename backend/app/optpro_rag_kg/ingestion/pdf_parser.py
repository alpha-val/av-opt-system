"""PDF parsing using PyPDF2. Fallback: treat input as plain text if PDF fails."""
from typing import Tuple
from PyPDF2 import PdfReader
from io import BytesIO

def parse_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
    """
    Parse a PDF file from bytes and extract text along with the page count.

    Parameters:
    - pdf_bytes: Raw PDF content as bytes.

    Returns:
    - Tuple containing the extracted text and the page count.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))  # Use BytesIO to read from bytes
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        page_count = len(reader.pages)
        return text, page_count
    except Exception:
        # Fallback: treat input as plain text
        try:
            return pdf_bytes.decode("utf-8"), 0
        except UnicodeDecodeError:
            return "", 0
