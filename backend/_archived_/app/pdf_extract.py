from __future__ import annotations
from typing import List, Dict, Any, Optional, Iterable, Tuple, Union
import io
import os
import tempfile

# Soft deps – we handle absence gracefully
try:
    import camelot  # vector PDF tables (lattice/stream)

    _HAVE_CAMELOT = True
except Exception:
    _HAVE_CAMELOT = False

import pdfplumber  # lightweight page introspection (vector vs scanned)
from PIL import Image
from pdf2image import convert_from_bytes, convert_from_path  # render pages to images

from .pdf_ocr import extract_tables_from_image


def _materialize_pdf_to_path(pdf: Union[str, bytes, io.BytesIO]) -> Tuple[str, bool]:
    """
    Returns (path, is_temp). Accepts filesystem path, bytes, or stream.
    """
    if isinstance(pdf, str) and os.path.exists(pdf):
        return pdf, False
    # bytes / stream → temp file
    data = None
    if isinstance(pdf, (bytes, bytearray)):
        data = pdf
    else:
        try:
            pdf.seek(0)
            data = pdf.read()
        except Exception:
            raise ValueError(
                "Unsupported pdf input; pass a path, bytes, or a file-like object."
            )
    fd, tmp = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return tmp, True


def _pages_arg_to_list(pages: Optional[str], total_pages: int) -> List[int]:
    """
    "1,3-5" → [1,3,4,5]. 1-indexed for user friendliness; we output 1-indexed too.
    """
    if not pages:
        return list(range(1, total_pages + 1))
    out = []
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            out.extend(list(range(min(a, b), max(a, b) + 1)))
        else:
            out.append(int(part))
    out = [p for p in out if 1 <= p <= total_pages]
    return sorted(set(out))


def _vector_tables_camelot(pdf_path: str, page_str: str) -> List[Dict[str, Any]]:
    """
    Try Camelot in lattice then stream mode. Returns list of dicts with df + meta.
    """
    results: List[Dict[str, Any]] = []
    if not _HAVE_CAMELOT:
        return results

    def _tables_to_results(tables, flavor: str):
        out = []
        for i, t in enumerate(tables or []):
            df = t.df
            # Clean up: drop fully empty rows/cols
            df = df.replace(r"^\s*$", None, regex=True)
            df = df.dropna(how="all").dropna(axis=1, how="all")
            bbox = getattr(t, "bbox", None)
            out.append(
                {
                    "df": df,
                    "columns": list(df.columns),
                    "rows": df.to_dict(orient="records"),
                    "meta": {
                        "page": t.page,
                        "bbox": bbox,
                        "flavor": flavor,
                        "index": i,
                    },
                }
            )
        return out

    try:
        tables = camelot.read_pdf(pdf_path, pages=page_str, flavor="lattice")
        results.extend(_tables_to_results(tables, "lattice"))
        # Complement with stream tables on same pages (may find additional)
        # tables_stream = camelot.read_pdf(pdf_path, pages=page_str, flavor="stream")
        # results.extend(_tables_to_results(tables_stream, "stream"))
    except Exception:
        # Silently ignore – we’ll fall back to OCR if needed
        pass
    return results


def extract_pdf_tables(
    pdf: Union[str, bytes, io.BytesIO], *, pages: Optional[str] = None, dpi: int = 300
) -> List[Dict[str, Any]]:
    """
    Main cascade:
      1) If any page looks vector-like → try Camelot (lattice+stream).
      2) For pages with no vector tables or for image-only pages → render to image and OCR tables.
    Returns: [{ "df": pandas.DataFrame, "meta": {...}}]
    """
    path, is_temp = _materialize_pdf_to_path(pdf)
    out: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(path) as pdf_doc:
            total = len(pdf_doc.pages)
            want_pages = _pages_arg_to_list(pages, total)  # 1-indexed
            page_str = ",".join(map(str, want_pages))

            # Try vector extraction across requested pages (if Camelot present)
            if _HAVE_CAMELOT:
                out.extend(_vector_tables_camelot(path, page_str))

            # Track which pages are already covered by Camelot
            covered = set(
                [r["meta"]["page"] for r in out if "meta" in r and "page" in r["meta"]]
            )

            # For any requested page not covered, run OCR extraction
            for pnum in want_pages:
                if pnum in covered:
                    continue
                page = pdf_doc.pages[pnum - 1]
                # If page has characters and lines, Camelot probably should have caught it; still OCR as fallback
                # Render page → image
                # Prefer convert_from_path on whole PDF once? For simplicity, per page via crop:
                pil_images = convert_from_path(
                    path, dpi=dpi, first_page=pnum, last_page=pnum
                )
                if not pil_images:
                    continue
                img = pil_images[0]
                ocr_tables = extract_tables_from_image(img)
                for i, tbl in enumerate(ocr_tables):
                    out.append(
                        {
                            "df": tbl,
                            "meta": {
                                "page": pnum,
                                "bbox": None,
                                "flavor": "ocr",
                                "index": i,
                            },
                        }
                    )
    finally:
        if is_temp:
            try:
                os.remove(path)
            except Exception:
                pass
    return out
