# etl_bronze.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
import os, tempfile, uuid, datetime
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .text_clean import extract_and_clean, NAMESPACE
from .bronze_store import (
    bulk_upsert_rows,
    ensure_bronze_indexes,
    store_document_metadata,
    upsert_table,
)

router_vault_data = APIRouter()


# Try your enhanced extractor (preferred)
def _extract_tables_cascade(
    pdf_bytes: bytes, pages: Optional[str]
) -> List[Dict[str, Any]]:
    try:
        from .pdf_extract import (
            extract_pdf_tables,
        )  # your cascade (Camelot → OCR fallback)

        out_tables = extract_pdf_tables(pdf_bytes, pages=pages)
        print(f"[ETL:BRONZE] - Extracted {len(out_tables)} tables using cascade")
        return out_tables
    except Exception:
        return _camelot_only_tables(pdf_bytes, pages)


def _camelot_only_tables(
    pdf_bytes: bytes, pages: Optional[str]
) -> List[Dict[str, Any]]:
    try:
        import camelot
    except Exception:
        return []
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(pdf_bytes)
        pages = pages or "1-end"
        tables = camelot.read_pdf(path, pages=pages, flavor="lattice")
        out = []
        for i, t in enumerate(tables or []):
            df = t.df
            # light cleanup
            df = (
                df.replace(r"^\s*$", None, regex=True)
                .dropna(how="all")
                .dropna(axis=1, how="all")
            )
            out.append(
                {"df": df, "meta": {"page": t.page, "flavor": "lattice", "index": i}}
            )
        return out
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


# Use your OpenAI extractor
def _extract_entities_mentions(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    from .extract_with_openai import (
        openai_extract_nodes_rels_mentions,
        openai_extract_nodes_rels,
    )

    return openai_extract_nodes_rels(chunks)
    # return openai_extract_nodes_rels_mentions(chunks)


def _mention_id(
    chunk_id: str, entity_id: str, span_start, span_end, surface: Optional[str]
) -> str:
    s0 = "" if span_start is None else str(span_start)
    s1 = "" if span_end is None else str(span_end)
    surf = (surface or "").strip().lower()
    key = f"mention|{chunk_id}|{entity_id}|{s0}|{s1}|{surf}"
    return str(uuid.uuid5(NAMESPACE, key))


def make_table_id(doc_id: str, page: int, index: int) -> str:
    return f"tbl::{doc_id}::p{page}::{index}"


def make_row_id(table_id: str, row_idx: int) -> str:
    return f"row::{table_id}::{row_idx}"


@router_vault_data.post("/etl_ingest_tables")
def etl_ingest_tables(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    project_id: str = Form(...),
    pages: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    data_type: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
):
    """Ingest tables from a PDF into Bronze: tables/rows only."""
    ensure_bronze_indexes()

    print(
        f"Processing vault data file for user_id: {user_id}, project_id: {project_id}"
    )

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    # 1) Light text extract to get doc_id
    doc_id, file_sha, pages_raw, pages_clean = extract_and_clean(pdf_bytes, filename)

    # 2) Extract tables
    table_results = _extract_tables_cascade(pdf_bytes, pages)
    tables_written, rows_written = 0, 0

    for t in table_results:
        df: pd.DataFrame = t["df"]
        meta = t.get("meta", {})
        meta.update(
            {
                "user_id": user_id,
                "project_id": project_id,
                "description": description,
                "data_type": data_type,
                "sheet_name": sheet_name,
            }
        )

        page = int(meta.get("page") or 1)
        index = int(meta.get("index") or 0)
        table_id = make_table_id(doc_id, page, index)

        # Ensure all column names are strings
        df.columns = [str(c) for c in df.columns]

        # Create the preview
        preview = df.head(5).to_dict(orient="records")

        # Upsert the table
        try:
            upsert_table(doc_id, table_id, meta, preview, df.shape[1])
        except Exception as e:
            print(f"[ETL:BRONZE] - Failed to upsert table {table_id}: {e}")
            continue
        tables_written += 1

        # Upsert rows
        row_docs: List[Dict[str, Any]] = []
        cols = [str(c) for c in df.columns]
        for i, row in df.iterrows():
            i_num = (
                int(i)
                if isinstance(i, (int, float)) or (isinstance(i, str) and i.isdigit())
                else 0
            )
            row_id = make_row_id(table_id, i_num)
            cells = []
            for col in cols:
                raw = row.get(col)
                val = None if pd.isna(raw) else str(raw)
                cells.append({"col": col, "raw": val, "text": val})
            row_docs.append(
                {"_id": row_id, "table_id": table_id, "row_idx": i_num, "cells": cells}
            )
        if row_docs:
            bulk_upsert_rows(row_docs)
            rows_written += len(row_docs)

    # Store document metadata with proper error handling
    try:
        doc_metadata = store_document_metadata(
            doc_id=doc_id,
            filename=filename,
            project_id=project_id,
            user_id=user_id,
            artifact_type=data_type or "scenario",  # Fixed: use scenario for vault data
        )
        print(f"[ETL:BRONZE] - Stored document metadata: {doc_metadata}")
    except Exception as e:
        print(f"[ETL:BRONZE] - Failed to store document metadata: {e}")
        doc_metadata = None

    return {
        "doc_id": doc_id,
        "filename": filename,
        "pages": len(pages_clean),
        "tables_written": tables_written,
        "rows_written": rows_written,
        "user_id": user_id,
        "project_id": project_id,
        "document_metadata": doc_metadata,
    }
