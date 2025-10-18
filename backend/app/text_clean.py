# text_clean.py
from __future__ import annotations
from typing import List, Tuple, Dict, Any
import io, re, hashlib, uuid
import pdfplumber

# Fixed namespace for deterministic UUID5 generation across the app
NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def make_doc_id(filename: str, file_sha256: str) -> str:
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
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)


def _collapse_ws(text: str) -> str:
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
    return _collapse_ws(_dehyphenate(text))


def chunk_by_page(
    clean_pages: List[Tuple[int, str]], doc_id: str
) -> List[Dict[str, Any]]:
    """Bronze: 1 chunk per page. chunk_id = uuid5(doc_id|seq)."""
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


def extract_and_clean(pdf_bytes: bytes, filename: str):
    """
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


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

# List of attribute names to process for value/unit extraction
ATTRIBUTE_NAMES_WITH_UNITS = [
    "amount",
    "capacity",
    "flow_rate",
    "output_rate",
    "processing_rate",
    "production_rate",
    "size_capacity",
    "speed",
    "throughput",
    "volume",
]


def _parse_attribute_with_capacity(attribute: str) -> Dict[str, Any]:
    """
    Parse an attribute-value pair like "flow_rate:500 gals/hr" and convert it
    to "capacity_value:500" and "capacity_unit:gals/hr".
    Retains the original attribute in the output.

    Args:
        attribute: A string in the format "key:value unit".

    Returns:
        A dictionary with the original attribute, "key_value", and "key_unit".
    """
    if ":" not in attribute:
        raise ValueError(f"Invalid attribute format: {attribute}")

    # Split the attribute into key and value
    key, value = attribute.split(":", 1)
    key = key.strip()

    # Parse the value and unit
    match = re.match(r"([\d,.]+)\s*([^\d\s]+)", value.strip())
    if match:
        value_part, unit_part = match.group(1), match.group(2)
        return {
            f"{key}": attribute,  # Retain the original attribute
            f"capacity_value": value_part,
            f"capacity_unit": unit_part,
        }

    # If no match, return the original value with empty unit
    return {
        f"{key}": attribute,  # Retain the original attribute
        f"{key}_value": value.strip(),
        f"{key}_unit": "",
    }


# Process extracted nodes
def process_extracted_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach source back-pointer and doc metadata to each node."""
    for n in nodes:
        # Process capacity attributes
        properties = n.get("properties", {})
        new_properties = {}

        # Check if properties already have 'capacity_value' and 'capacity_unit'
        if "capacity_value" in properties and "capacity_unit" in properties:
            new_properties = properties  # Already processed
            n["properties"] = new_properties
            continue

        for k, v in properties.items():
            if k in ATTRIBUTE_NAMES_WITH_UNITS:
                parsed = _parse_attribute_with_capacity(f"{k}:{v}")
                new_properties.update(parsed)
            else:
                new_properties[k] = v

        n["properties"] = new_properties
    return nodes
