from fastapi import APIRouter, Query, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import json
import logging
import pandas as pd
import datetime
import uuid

from ..text_clean import extract_and_clean, NAMESPACE
from ..ontology import load_ontology
from ..build_prompt import gen_prompt
from .tabular_rules import TABULAR_RULES
from .table_payload import build_llm_payload
from .extract_with_openai import call_llm_for_tables
from .validator import validate_kg_structure
from .silver_store import store_silver_nodes, store_silver_edges

logger = logging.getLogger(__name__)
router_ingest_tables = APIRouter()


def _extract_tables_from_pdf(
    pdf_bytes: bytes, pages: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF using cascade approach (Camelot → pdfplumber fallback).

    Args:
        pdf_bytes: PDF file bytes
        pages: Optional page range (e.g., "1-5,10")

    Returns:
        List of table dictionaries with 'df' and 'meta'
    """
    try:
        from ..pdf_extract import extract_pdf_tables

        tables = extract_pdf_tables(pdf_bytes, pages=pages)
        logger.info(f"[TABLE_EXTRACT] Extracted {len(tables)} tables using cascade")
        return tables
    except ImportError:
        logger.warning(
            "[TABLE_EXTRACT] pdf_extract module not found, falling back to Camelot"
        )
        return _extract_tables_camelot(pdf_bytes, pages)
    except Exception as e:
        logger.error(
            f"[TABLE_EXTRACT] Cascade extraction failed: {e}, falling back to Camelot"
        )
        return _extract_tables_camelot(pdf_bytes, pages)


def _extract_tables_camelot(
    pdf_bytes: bytes, pages: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fallback: Extract tables using Camelot only.

    Args:
        pdf_bytes: PDF file bytes
        pages: Optional page range

    Returns:
        List of table dictionaries
    """
    try:
        import camelot
        import tempfile
        import os
    except ImportError:
        logger.error("[TABLE_EXTRACT] Camelot not installed")
        return []

    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(pdf_bytes)

        pages_str = pages or "1-end"
        tables = camelot.read_pdf(path, pages=pages_str, flavor="lattice")

        out = []
        for i, t in enumerate(tables or []):
            df = t.df
            # Light cleanup
            df = (
                df.replace(r"^\s*$", None, regex=True)
                .dropna(how="all")
                .dropna(axis=1, how="all")
            )
            out.append(
                {"df": df, "meta": {"page": t.page, "flavor": "lattice", "index": i}}
            )

        logger.info(f"[TABLE_EXTRACT] Extracted {len(out)} tables using Camelot")
        return out

    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def make_table_id(doc_id: str, page: int, index: int) -> str:
    """Generate deterministic table ID."""
    return f"tbl::{doc_id}::p{page}::{index}"


def make_row_id(table_id: str, row_idx: int) -> str:
    """Generate deterministic row ID."""
    return f"row::{table_id}::{row_idx}"


def _prepare_table_metadata(
    df: pd.DataFrame,
    meta: Dict[str, Any],
    doc_id: str,
    project_id: str,
    user_id: str,
    filename: str,
) -> Dict[str, Any]:
    """
    Prepare table metadata in the format expected by downstream processing.

    Args:
        df: DataFrame with table data
        meta: Extraction metadata (page, index, etc.)
        doc_id: Document identifier
        project_id: Project identifier
        user_id: User identifier
        filename: Source filename

    Returns:
        Table metadata dictionary
    """
    page = int(meta.get("page", 1))
    index = int(meta.get("index", 0))
    table_id = make_table_id(doc_id, page, index)

    # Ensure column names are strings
    df.columns = [str(c) for c in df.columns]
    columns = list(df.columns)

    # Create preview
    preview = df.head(5).to_dict(orient="records")

    table_metadata = {
        "table_id": table_id,
        "doc_id": doc_id,
        "project_id": project_id,
        "user_id": user_id,
        "filename": filename,
        "page": page,
        "index": index,
        "columns": columns,
        "column_count": len(columns),
        "row_count": len(df),
        "preview": preview,
        "data_type": "tabular",
        "artifact_type": "tabular_data",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
        **meta,  # Include original extraction metadata
    }

    return table_metadata


def _prepare_row_documents(df: pd.DataFrame, table_id: str) -> List[Dict[str, Any]]:
    """
    Convert DataFrame rows to row documents format.

    Args:
        df: DataFrame with table data
        table_id: Table identifier

    Returns:
        List of row documents
    """
    row_docs = []
    columns = [str(c) for c in df.columns]

    for i, row in df.iterrows():
        # Handle different index types
        i_num = (
            int(i)
            if isinstance(i, (int, float)) or (isinstance(i, str) and i.isdigit())
            else len(row_docs)
        )

        row_id = make_row_id(table_id, i_num)

        # Build cell data
        cells = []
        for col in columns:
            raw = row.get(col)
            val = None if pd.isna(raw) else str(raw)
            cells.append({"col": col, "raw": val, "text": val})

        row_docs.append(
            {"_id": row_id, "table_id": table_id, "row_idx": i_num, "cells": cells}
        )

    return row_docs


def enhance_with_lineage(
    kg_data: Dict[str, Any], table_meta: Dict[str, Any], rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Add lineage edges connecting entities to their source rows.
    """
    table_id = table_meta.get("table_id")

    # DEBUG: Log what we receive
    logger.info(f"[LINEAGE] Received {len(kg_data.get('nodes', []))} nodes")
    logger.info(f"[LINEAGE] Received {len(kg_data.get('edges', []))} edges")

    # # Filter out invalid nodes (strings, non-dicts)
    # valid_nodes = []
    # for i, node in enumerate(kg_data.get("nodes", [])):
    #     # DEBUG: Log type of each node
    #     logger.debug(f"[LINEAGE] Node {i}: type={type(node)}, value={str(node)[:100]}")

    #     if isinstance(node, str):
    #         logger.warning(f"[LINEAGE] Skipping string node at index {i}: {node}")
    #         continue
    #     if not isinstance(node, dict):
    #         logger.warning(f"[LINEAGE] Skipping non-dict node at index {i}: {type(node)}")
    #         continue

    #     # Node is valid dict
    #     valid_nodes.append(node)

    # logger.info(
    #     f"[LINEAGE] Filtered to {len(valid_nodes)} valid nodes (removed {len(kg_data.get('nodes', [])) - len(valid_nodes)})"
    # )
    # kg_data["nodes"] = valid_nodes

    # Filter out invalid edges
    # valid_edges = []
    # for i, edge in enumerate(kg_data.get("edges", [])):
    #     logger.debug(f"[LINEAGE] Edge {i}: type={type(edge)}, value={str(edge)[:100]}")

    #     if isinstance(edge, str):
    #         logger.warning(f"[LINEAGE] Skipping string edge at index {i}: {edge}")
    #         continue
    #     if not isinstance(edge, dict):
    #         logger.warning(f"[LINEAGE] Skipping non-dict edge at index {i}: {type(edge)}")
    #         continue

    #     valid_edges.append(edge)

    # logger.info(
    #     f"[LINEAGE] Filtered to {len(valid_edges)} valid edges (removed {len(kg_data.get('edges', [])) - len(valid_edges)})"
    # )
    # kg_data["edges"] = valid_edges
    valid_nodes = kg_data.get("nodes", [])
    valid_edges = kg_data.get("edges", [])

    # Create TableRow nodes
    table_row_nodes = []
    for row in rows:
        if not isinstance(row, dict):
            logger.warning(f"[LINEAGE] Skipping invalid row: {type(row)}")
            continue

        table_row_nodes.append(
            {
                "id": row.get("_id"),
                "type": "TableRow",
                "properties": {
                    "row_index": row.get("row_idx", 0),
                    "table_id": table_id,
                    "confidence": 1.0,
                },
            }
        )

    # Add lineage edges from entities to rows
    lineage_edges = []
    for node in valid_nodes.get("nodes", []):
        if not isinstance(node.get("properties"), dict):
            continue

        row_idx = node.get("properties", {}).get("row_index")
        if row_idx is not None:
            matching_row = next(
                (
                    r
                    for r in rows
                    if isinstance(r, dict) and r.get("row_idx") == row_idx
                ),
                None,
            )
            if matching_row:
                lineage_edges.append(
                    {
                        "source": node.get("id"),
                        "target": matching_row.get("_id"),
                        "type": "DERIVES_FROM",
                        "properties": {
                            "row_index": row_idx,
                            "extraction_method": "tabular_direct",
                            "confidence": 1.0,
                        },
                    }
                )

    # Merge into KG data
    kg_data["nodes"].extend(table_row_nodes)
    kg_data["edges"].extend(lineage_edges)

    logger.info(
        f"[LINEAGE] Final: {len(kg_data['nodes'])} total nodes ({len(valid_nodes)} entities + {len(table_row_nodes)} TableRow), "
        f"{len(kg_data['edges'])} total edges ({len(valid_edges)} original + {len(lineage_edges)} lineage)"
    )

    return kg_data


@router_ingest_tables.post("/tables_to_entities")
def map_tables_to_entities(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    user_id: str = Form(...),
    pages: Optional[str] = Form(None),
    batch_size: int = Form(50),
):
    """
    Extract entities from PDF tables using LLM.

    This endpoint:
    1. Accepts a PDF file upload
    2. Extracts tables from the PDF
    3. Converts table rows to entities using LLM
    4. Stores entities in Silver collection

    Args:
        file: PDF file upload
        project_id: Project identifier
        user_id: User identifier
        pages: Optional page range (e.g., "1-5,10")
        batch_size: Rows per LLM call (default 50)

    Returns:
        Extraction statistics including tables, rows, nodes, and edges
    """
    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    # Read PDF bytes
    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    logger.info(f"[TABULAR_PIPELINE] Starting table extraction for {filename}")

    # Extract and clean text to get doc_id
    try:
        doc_id, file_sha, pages_raw, pages_clean = extract_and_clean(
            pdf_bytes, filename
        )
        logger.info(f"[TABULAR_PIPELINE] Generated doc_id: {doc_id}")
    except Exception as e:
        logger.error(f"[TABULAR_PIPELINE] Text extraction failed: {e}")
        raise HTTPException(500, f"Text extraction failed: {str(e)}")

    # Extract tables from PDF
    try:
        table_results = _extract_tables_from_pdf(pdf_bytes, pages)
        logger.info(
            f"[TABULAR_PIPELINE] Extracted {len(table_results)} tables from PDF"
        )
    except Exception as e:
        logger.error(f"[TABULAR_PIPELINE] Table extraction failed: {e}")
        raise HTTPException(500, f"Table extraction failed: {str(e)}")

    if not table_results:
        logger.warning(f"[TABULAR_PIPELINE] No tables found in {filename}")
        return {
            "doc_id": doc_id,
            "filename": filename,
            "tables_processed": 0,
            "rows_processed": 0,
            "nodes_created": 0,
            "edges_created": 0,
            "errors": ["No tables found in PDF"],
        }

    # Load ontology and build prompt
    ontology = load_ontology()
    base_prompt = gen_prompt(ontology)
    full_prompt = base_prompt  # + "\n\n" + TABULAR_RULES

    results = {
        "doc_id": doc_id,
        "filename": filename,
        "tables_processed": 0,
        "rows_processed": 0,
        "nodes_created": 0,
        "edges_created": 0,
        "errors": [],
    }

    # Process each extracted table
    for table_result in table_results:
        df = table_result["df"]
        meta = table_result.get("meta", {})

        # Prepare table metadata
        table_meta = _prepare_table_metadata(
            df=df,
            meta=meta,
            doc_id=doc_id,
            project_id=project_id,
            user_id=user_id,
            filename=filename,
        )

        table_id = table_meta["table_id"]
        logger.info(f"[TABULAR_PIPELINE] Processing table {table_id} ({len(df)} rows)")

        try:
            # Prepare row documents
            rows = _prepare_row_documents(df, table_id)

            if not rows:
                logger.warning(f"[TABULAR_PIPELINE] No rows in table {table_id}")
                continue

            # Limit rows for this batch
            rows_batch = rows[:batch_size]

            # Build LLM payload
            payload = build_llm_payload(table_meta, rows_batch, max_rows=batch_size)

            # Construct prompt with payload
            input_text = (
                f"{full_prompt}\n\n"
                f"INPUT TABLE DATA (JSON):\n"
                f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
            )

            # Call LLM
            logger.info(
                f"[TABULAR_PIPELINE] Calling LLM for table {table_id} ({len(rows_batch)} rows)"
            )
            kg_data = call_llm_for_tables(input_text, ontology)

            # Check for errors in response
            if "error" in kg_data:
                logger.error(
                    f"[TABULAR_PIPELINE] LLM extraction failed for {table_id}: {kg_data['error']}"
                )
                results["errors"].append(
                    {"table_id": table_id, "error": kg_data["error"]}
                )
                continue

            # # Validate structure
            # validation_errors = validate_kg_structure(kg_data, ontology)
            # if validation_errors:
            #     logger.error(f"[TABULAR_PIPELINE] Validation failed for {table_id}: {validation_errors}")
            #     results["errors"].append({
            #         "table_id": table_id,
            #         "errors": validation_errors
            #     })
            #     continue

            # Add lineage
            # kg_data = enhance_with_lineage(kg_data, table_meta, rows_batch)
            print(f"KG DATA: {kg_data}")
            # Store in Silver
            nodes_written = store_silver_nodes(
                kg_data.get("nodes", []),
                project_id=project_id,
                doc_id=doc_id,
                user_id=user_id,
            )
            edges_written = store_silver_edges(
                kg_data.get("edges", []),
                project_id=project_id,
                doc_id=doc_id,
                user_id=user_id,
            )

            results["tables_processed"] += 1
            results["rows_processed"] += len(rows_batch)
            results["nodes_created"] += nodes_written
            results["edges_created"] += edges_written

            logger.info(
                f"[TABULAR_PIPELINE] Table {table_id}: {nodes_written} nodes, {edges_written} edges"
            )

        except Exception as e:
            logger.error(f"[TABULAR_PIPELINE] Failed to process table {table_id}: {e}")
            import traceback

            traceback.print_exc()
            results["errors"].append({"table_id": table_id, "error": str(e)})
            continue

    logger.info(f"[TABULAR_PIPELINE] Completed: {results}")
    return results
