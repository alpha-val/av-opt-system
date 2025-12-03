from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


def normalize_column_name(col: str) -> str:
    """
    Convert column header to snake_case property name.

    Examples:
        "Capacity (tph)" → "capacity_tph"
        "Roll Diameter (in)" → "roll_diameter_in"
    """
    # Extract unit in parentheses
    unit_match = re.search(r"\(([^)]+)\)", col)
    unit_suffix = f"_{unit_match.group(1).lower()}" if unit_match else ""

    # Remove parentheses content
    col_clean = re.sub(r"\s*\([^)]*\)", "", col)

    # Convert to snake_case
    col_clean = col_clean.strip().lower()
    col_clean = re.sub(r"[\s\-]+", "_", col_clean)
    col_clean = re.sub(r"[^a-z0-9_]", "", col_clean)

    return col_clean + unit_suffix


def extract_units(columns: List[str]) -> Dict[str, str]:
    """Extract unit mappings from column headers."""
    units = {}
    for col in columns:
        unit_match = re.search(r"\(([^)]+)\)", col)
        if unit_match:
            normalized = normalize_column_name(col)
            units[normalized] = unit_match.group(1)
    return units


def build_row_payload(row_doc: Dict[str, Any], columns: List[str]) -> Dict[str, Any]:
    """
    Extract cell data from Bronze row document.

    Args:
        row_doc: Raw row from Bronze collection
        columns: Ordered column names

    Returns:
        Clean row payload with normalized column names
    """
    cells = row_doc.get("cells", [])
    row_data = {}

    for cell in cells:
        col_name = cell.get("col", "")
        raw_value = cell.get("raw")

        if raw_value is not None and str(raw_value).strip():
            normalized_name = normalize_column_name(col_name)
            row_data[normalized_name] = str(raw_value).strip()

    return {
        "row_id": row_doc.get("_id"),
        "row_index": row_doc.get("row_idx", 0),
        "cells": row_data,
    }


def build_llm_payload(
    table_meta: Dict[str, Any], rows: List[Dict[str, Any]], max_rows: int = 50
) -> Dict[str, Any]:
    """
    Build structured payload for LLM extraction.

    Args:
        table_meta: Table metadata from Bronze
        rows: Row documents from Bronze
        max_rows: Max rows per batch (default 50)

    Returns:
        Compact payload for LLM
    """
    columns = table_meta.get("columns", [])

    # Extract units from headers
    header_units = extract_units(columns)

    # Build row payloads
    row_payloads = []
    for row_doc in rows[:max_rows]:
        row_payloads.append(build_row_payload(row_doc, columns))

    payload = {
        "table_metadata": {
            "table_id": table_meta.get("table_id"),
            "doc_id": table_meta.get("doc_id"),
            "source_doc": table_meta.get("properties", {}).get(
                "artifact_type", "unknown"
            ),
            "page": table_meta.get("page", 1),
            "table_type": table_meta.get("table_type", "generic"),
            "columns": columns,
            "column_count": len(columns),
            "row_count": len(row_payloads),
            "header_units": header_units,
        },
        "rows": row_payloads,
    }

    logger.info(f"Built payload: {len(row_payloads)} rows, {len(columns)} columns")

    return payload
