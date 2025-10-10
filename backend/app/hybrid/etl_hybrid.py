from __future__ import annotations
from typing import Optional, Dict, Any, List
import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd
import logging

from ..text_clean import extract_and_clean
from ..bronze_store import (
    bulk_upsert_rows,
    ensure_bronze_indexes,
    store_document_metadata,
    upsert_table,
)
from ..etl_tabular_data import (
    _extract_tables_cascade,
    make_table_id,
    make_row_id,
)
from .build_prompt_with_tables import gen_prompt_with_tables
from ..ontology import load_ontology

logger = logging.getLogger(__name__)
router_hybrid_etl = APIRouter()


def _format_table_for_llm(
    table_id: str,
    table_type: str,
    page: int,
    df_dict: List[Dict[str, Any]],
    columns: List[str],
    max_rows: int = 10,
) -> str:
    """
    Format a parsed table as text for LLM consumption.

    Args:
        table_id: Unique table identifier
        table_type: Classified table type
        page: Page number
        df_dict: Table data as list of row dictionaries
        columns: Column names
        max_rows: Maximum rows to include (default 10)

    Returns:
        Markdown-style table wrapped in [TABLE] tags
    """
    header = " | ".join(columns)
    separator = " | ".join(["-" * min(len(col), 20) for col in columns])

    rows = []
    for row_dict in df_dict[:max_rows]:
        row_values = [str(row_dict.get(col, "")).strip() for col in columns]
        rows.append(" | ".join(row_values))

    table_text = f"""
[TABLE table_id="{table_id}" table_type="{table_type}" page="{page}"]
| {header} |
| {separator} |
"""
    for row in rows:
        table_text += f"| {row} |\n"

    if len(df_dict) > max_rows:
        table_text += f"... ({len(df_dict) - max_rows} more rows)\n"

    table_text += "[/TABLE]\n"

    return table_text


def _classify_table_type(
    columns: List[str], first_rows: List[Dict[str, Any]], table_meta: Dict[str, Any]
) -> str:
    """
    Classify table type based on columns and content.

    Args:
        columns: List of column names
        first_rows: First few rows of data
        table_meta: Additional metadata about the table

    Returns:
        Table type string (equipment_cost, lang_factor, etc.)
    """
    cols_lower = [str(c).lower() for c in columns]

    # Check for cost tables
    if any("cost" in c or "price" in c for c in cols_lower):
        if any("equipment" in c or "model" in c or "item" in c for c in cols_lower):
            return "equipment_cost"
        elif any("wbs" in c or "code" in c for c in cols_lower):
            return "wbs_breakdown"
        return "cost_table"

    # Check for lang factor tables
    if any("factor" in c or "multiplier" in c for c in cols_lower):
        if any("lang" in c or "installation" in c for c in cols_lower):
            return "lang_factor"

    # Check for sizing tables
    if any("capacity" in c or "throughput" in c for c in cols_lower):
        if any("model" in c or "equipment" in c or "size" in c for c in cols_lower):
            return "equipment_sizing"

    # Check for escalation tables
    if "year" in cols_lower and any(
        "index" in c or "cepci" in c or "cpi" in c for c in cols_lower
    ):
        return "escalation_index"

    # Check for performance tables
    if any(
        "availability" in c or "utilization" in c or "efficiency" in c
        for c in cols_lower
    ):
        return "performance_data"

    # Check for specification tables
    if any("specification" in c or "parameter" in c for c in cols_lower):
        return "equipment_specification"

    # Default
    return "generic"


def _extract_entities_hybrid(
    text_chunks: List[Dict[str, Any]],
    table_contexts: List[str],
    ontology: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract entities from both text and tables using LLM.

    Args:
        text_chunks: Cleaned text chunks from document
        table_contexts: Formatted table strings with [TABLE] markers
        ontology: Domain ontology

    Returns:
        Combined extraction results
    """
    # Check if extract function exists
    try:
        from .extract_with_openai import openai_extract_hybrid
    except ImportError:
        logger.warning(
            "[ETL:HYBRID] - extract_with_openai module not found, returning empty result"
        )
        return {
            "text_entities": [],
            "text_relationships": [],
            "table_entities": [],
            "table_metadata": [],
            "cross_references": [],
            "note": "LLM extraction not configured",
        }

    # Generate hybrid prompt
    try:
        prompt = gen_prompt_with_tables(ontology)
    except Exception as e:
        logger.error(f"[ETL:HYBRID] - Failed to generate prompt: {e}")
        from ..build_prompt import gen_prompt

        prompt = gen_prompt(ontology)

    # Combine text and tables for LLM
    combined_input = []

    # Add text chunks
    for chunk in text_chunks:
        if chunk.get("text"):
            combined_input.append(
                {"type": "text", "content": chunk.get("text", ""), "metadata": chunk}
            )

    # Add table contexts
    for table_ctx in table_contexts:
        combined_input.append({"type": "table", "content": table_ctx, "metadata": {}})

    # Call LLM with hybrid prompt
    try:
        result = openai_extract_hybrid(prompt, combined_input)

        # Ensure result is a dictionary
        if not isinstance(result, dict):
            logger.warning(f"[ETL:HYBRID] - Unexpected result type: {type(result)}")
            return {
                "text_entities": [],
                "text_relationships": [],
                "table_entities": [],
                "table_metadata": [],
                "cross_references": [],
                "raw_result": str(result),
            }

        return result

    except Exception as e:
        logger.error(f"[ETL:HYBRID] - LLM extraction error: {e}")
        import traceback

        traceback.print_exc()
        return {
            "text_entities": [],
            "text_relationships": [],
            "table_entities": [],
            "table_metadata": [],
            "cross_references": [],
            "error": str(e),
        }


@router_hybrid_etl.post("/etl_ingest_hybrid")
def etl_ingest_hybrid(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    project_id: str = Form(...),
    pages: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    artifact_type: str = Form("technical_report"),
):
    """
    Hybrid ingestion: Parse tables deterministically + extract text entities with LLM.

    Workflow:
    1. Extract and clean text from PDF
    2. Parse tables into rows/columns (deterministic)
    3. Classify table types
    4. Format tables for LLM context
    5. Extract entities from text + table context using LLM
    6. Store both structured table data and extracted entities

    Args:
        file: PDF file upload
        user_id: User identifier
        project_id: Project identifier
        pages: Optional page range (e.g., "1-5,10")
        description: Optional description
        artifact_type: Type of artifact (default: technical_report)

    Returns:
        Dictionary with ingestion results including doc_id, tables, entities
    """
    # Ensure indexes exist
    ensure_bronze_indexes()

    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    # Read file bytes
    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    logger.info(f"[ETL:HYBRID] - Starting hybrid ingestion for {filename}")

    # -------------------------------------------------------------------------
    # 1) Extract and clean text
    # -------------------------------------------------------------------------
    try:
        result = extract_and_clean(pdf_bytes, filename)

        # Unpack result - should be tuple of (doc_id, file_sha, pages_raw, pages_clean)
        if isinstance(result, tuple) and len(result) == 4:
            doc_id, file_sha, pages_raw, pages_clean = result
        else:
            logger.error(
                f"[ETL:HYBRID] - Unexpected extract_and_clean result type: {type(result)}"
            )
            raise HTTPException(
                500, f"Text extraction returned unexpected format: {type(result)}"
            )

    except Exception as e:
        logger.error(f"[ETL:HYBRID] - Text extraction failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(500, f"Text extraction failed: {str(e)}")

    # Validate pages_clean structure
    if not isinstance(pages_clean, list):
        logger.warning(f"[ETL:HYBRID] - pages_clean is not a list: {type(pages_clean)}")
        pages_clean = []

    logger.info(f"[ETL:HYBRID] - Extracted {len(pages_clean)} text pages from document")

    # -------------------------------------------------------------------------
    # 2) Extract tables (deterministic parsing)
    # -------------------------------------------------------------------------
    try:
        table_results = _extract_tables_cascade(pdf_bytes, pages)
        logger.info(
            f"[ETL:HYBRID] - Extracted {len(table_results)} tables using cascade"
        )
    except Exception as e:
        logger.error(f"[ETL:HYBRID] - Table extraction failed: {e}")
        table_results = []

    tables_written = 0
    rows_written = 0
    table_contexts = []
    table_metadata_list = []

    # Load ontology
    try:
        ontology = load_ontology()
    except Exception as e:
        logger.warning(f"[ETL:HYBRID] - Failed to load ontology: {e}")
        ontology = {}

    # -------------------------------------------------------------------------
    # 3) Process each table
    # -------------------------------------------------------------------------
    for t in table_results:
        df: pd.DataFrame = t["df"]
        meta = t.get("meta", {})

        page = int(meta.get("page", 1))
        index = int(meta.get("index", 0))
        table_id = make_table_id(doc_id, page, index)

        # Ensure column names are strings
        df.columns = [str(c) for c in df.columns]
        columns = list(df.columns)

        # Convert to dict for classification
        df_dict = df.to_dict(orient="records")

        # 4) Classify table type
        table_type = _classify_table_type(columns, df_dict[:5], meta)

        logger.info(
            f"[ETL:HYBRID] - Processing table {table_id} (type: {table_type}, rows: {len(df)})"
        )

        # 5) Format for LLM context
        table_context = _format_table_for_llm(
            table_id=table_id,
            table_type=table_type,
            page=page,
            df_dict=df_dict,
            columns=columns,
        )
        table_contexts.append(table_context)

        # 6) Store table metadata
        preview = df.head(5).to_dict(orient="records")

        # Build complete metadata dictionary
        table_doc = {
            "table_id": table_id,
            "user_id": user_id,
            "project_id": project_id,
            "description": description,
            "table_type": table_type,
            "data_type": "tabular",
            "artifact_type": artifact_type,
            "preview": preview,
            "row_count": len(df),
            "column_count": df.shape[1],
            "columns": columns,
            "page": page,
            "index": index,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        }

        # Merge original meta from extraction
        table_doc.update(meta)

        try:
            # Call upsert_table with correct signature: (doc_id, table_id, meta, properties)
            upsert_table(
                doc_id=doc_id, table_id=table_id, meta=table_doc, properties=table_doc
            )
            tables_written += 1

            table_metadata_list.append(
                {
                    "table_id": table_id,
                    "table_type": table_type,
                    "page": page,
                    "rows": len(df),
                    "columns": len(columns),
                }
            )

        except Exception as e:
            logger.error(f"[ETL:HYBRID] - Failed to upsert table {table_id}: {e}")
            import traceback

            traceback.print_exc()
            continue

        # 7) Store rows (deterministic data)
        row_docs: List[Dict[str, Any]] = []
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
                {
                    "_id": row_id,
                    "table_id": table_id,
                    "row_idx": i_num,
                    "cells": cells,
                    "table_type": table_type,
                    "properties": meta,
                }
            )

        # Bulk insert rows
        if row_docs:
            try:
                bulk_upsert_rows(row_docs)
                rows_written += len(row_docs)
                logger.info(
                    f"[ETL:HYBRID] - Stored {len(row_docs)} rows for table {table_id}"
                )
            except Exception as e:
                logger.error(
                    f"[ETL:HYBRID] - Failed to store rows for table {table_id}: {e}"
                )

    # -------------------------------------------------------------------------
    # 8) Extract entities from text + table context using LLM
    # -------------------------------------------------------------------------
    logger.info(
        f"[ETL:HYBRID] - Extracting entities from {len(pages_clean)} text chunks and {len(table_contexts)} tables"
    )

    # Build text_chunks with proper validation
    text_chunks = []
    for page in pages_clean:
        if isinstance(page, dict):
            text_content = page.get("clean") or page.get("text", "")
            page_num = page.get("page_num") or page.get("page", len(text_chunks) + 1)

            if text_content:
                text_chunks.append({"text": text_content, "page_num": page_num})
        elif isinstance(page, str):
            # If page is just a string, use it directly
            text_chunks.append({"text": page, "page_num": len(text_chunks) + 1})
        else:
            logger.warning(f"[ETL:HYBRID] - Unexpected page format: {type(page)}")

    # Initialize empty result in case extraction fails
    extraction_result = {
        "text_entities": [],
        "text_relationships": [],
        "table_entities": [],
        "table_metadata": [],
        "cross_references": [],
    }

    # Extract entities using LLM
    if text_chunks or table_contexts:
        try:
            extraction_result = _extract_entities_hybrid(
                text_chunks=text_chunks,
                table_contexts=table_contexts,
                ontology=ontology,
            )
            logger.info(
                f"[ETL:HYBRID] - Extracted {len(extraction_result.get('text_entities', []))} text entities, "
                f"{len(extraction_result.get('table_entities', []))} table entities"
            )
        except Exception as e:
            logger.error(f"[ETL:HYBRID] - Entity extraction failed: {e}")
            import traceback

            traceback.print_exc()
    else:
        logger.warning(
            "[ETL:HYBRID] - No text chunks or tables to extract entities from"
        )

    # -------------------------------------------------------------------------
    # 9) Store document metadata
    # -------------------------------------------------------------------------
    try:
        doc_metadata = store_document_metadata(
            doc_id=doc_id,
            filename=filename,
            project_id=project_id,
            user_id=user_id,
            artifact_type=artifact_type,
        )
        logger.info(f"[ETL:HYBRID] - Stored document metadata for {doc_id}")
    except Exception as e:
        logger.error(f"[ETL:HYBRID] - Failed to store document metadata: {e}")
        doc_metadata = None

    # -------------------------------------------------------------------------
    # 10) Build and return response
    # -------------------------------------------------------------------------
    response = {
        "doc_id": doc_id,
        "filename": filename,
        "pages": len(pages_clean),
        "tables_written": tables_written,
        "rows_written": rows_written,
        "table_metadata": table_metadata_list,
        "entities_extracted": {
            "text_entities": len(extraction_result.get("text_entities", [])),
            "table_entities": len(extraction_result.get("table_entities", [])),
            "cross_references": len(extraction_result.get("cross_references", [])),
        },
        "user_id": user_id,
        "project_id": project_id,
        "document_metadata": doc_metadata,
        "extraction_result": extraction_result,
    }

    logger.info(
        f"[ETL:HYBRID] - Completed hybrid ingestion for {filename}: "
        f"{tables_written} tables, {rows_written} rows, "
        f"{response['entities_extracted']['text_entities']} text entities, "
        f"{response['entities_extracted']['table_entities']} table entities"
    )

    return response
