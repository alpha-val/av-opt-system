# etl_bronze.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
import os, tempfile, uuid, datetime
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .text_clean import extract_and_clean, chunk_by_page, NAMESPACE
from .bronze_store import (
    bulk_upsert_chunks,
    bulk_upsert_entities,
    bulk_upsert_mentions,
    bulk_upsert_relations,
    bulk_upsert_rows,
    clear_all_collections,
    db,
    ensure_bronze_indexes,
    upsert_document,
    upsert_table,
)

router = APIRouter()


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
    from .extract_with_openai import openai_extract_nodes_rels_mentions, openai_extract_nodes_rels
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


@router.get("/test-mongo-connection")
def test_mongo_connection():
    try:
        # Attempt to connect to the database
        # REMEMBER - NO VPN !!!
        D = db()
        # Check if the connection is successful by listing collections
        collections = D.list_collection_names()
        return {
            "status": "success",
            "message": "Successfully connected to MongoDB",
            "collections": collections,
            "date": datetime.datetime.utcnow(),
        }
    except Exception as e:
        # Handle connection errors
        return {
            "status": "error",
            "message": f"Failed to connect to MongoDB: {str(e)}",
        }


@router.post("/etl_base_case")
def etl_bronze(file: UploadFile = File(...), pages: Optional[str] = Form(None)):
    """Ingest a PDF into Bronze: text chunks, tables/rows, entities/relations/mentions."""
    ensure_bronze_indexes()
    # clear_all_collections()  # WARNING: Disable this line in production!
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    # 1) Text extract + clean
    doc_id, file_sha, pages_raw, pages_clean = extract_and_clean(pdf_bytes, filename)

    # 2) Build page chunks (Bronze)
    chunks = chunk_by_page(pages_clean, doc_id)
    raw_by_page = {p: t for p, t in pages_raw}
    for c in chunks:
        c["text_raw"] = raw_by_page.get(c["page"])

    # 3) Entities/relations/mentions from free text (Bronze)
    kg = _extract_entities_mentions(chunks)
    nodes = list(kg.get("nodes", []) or [])
    edges = list(kg.get("edges", []) or [])
    mentions = list(kg.get("mentions", []) or [])

    # Attach simple source back-pointer to each node; ensure deterministic mention IDs
    for n in nodes:
        srcs = n.get("sources") or []
        if not any(isinstance(s, dict) and s.get("doc_id") == doc_id for s in srcs):
            srcs.append({"doc_id": doc_id})
        n["sources"] = srcs

    for m in mentions:
        m["_id"] = _mention_id(
            chunk_id=m.get("chunk_id"),
            entity_id=m.get("entity_id"),
            span_start=m.get("span_start"),
            span_end=m.get("span_end"),
            surface=m.get("surface"),
        )

    # 4) Persist all Bronze artifacts
    upsert_document(
        doc_id,
        {
            "filename": filename,
            "sha256": file_sha,
            "mime": "application/pdf",
            "pages": len(pages_clean),
            "status": "bronze",
        },
    )
    bulk_upsert_chunks(chunks)
    bulk_upsert_entities(nodes)
    bulk_upsert_relations(edges)
    bulk_upsert_mentions(mentions)

    return {
        "doc_id": doc_id,
        "filename": filename,
        "pages": len(pages_clean),
        "chunks_written": len(chunks),
        "entities_written": len(nodes),
        "relations_written": len(edges),
        "mentions_written": len(mentions),
    }

@router.post("/etl_ingest_tables")
def etl_ingest_tables(file: UploadFile = File(...), pages: Optional[str] = Form(None)):
    """Ingest tables from a PDF into Bronze: tables/rows only."""
    ensure_bronze_indexes()
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    # 1) Light text extract to get doc_id
    doc_id, file_sha, pages_raw, pages_clean = extract_and_clean(pdf_bytes, filename)

    # 2) Extract tables (your cascade → fallback Camelot-only)
    table_results = _extract_tables_cascade(pdf_bytes, pages)
    tables_written, rows_written = 0, 0
    for t in table_results:
        df: pd.DataFrame = t["df"]
        meta = t.get("meta", {})
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

        # Upsert rows (cells embedded in 'rows' for Bronze)
        row_docs: List[Dict[str, Any]] = []
        cols = [str(c) for c in df.columns]
        for i, row in df.iterrows():
            # Some Camelot tables use string indexes; coerce if needed
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

    return {
        "doc_id": doc_id,
        "filename": filename,
        "pages": len(pages_clean),
        "tables_written": tables_written,
        "rows_written": rows_written,
    }


# -----------------------
# Bonus QA endpoints
# -----------------------


@router.get("/documents/{doc_id}/summary")
def get_doc_summary(doc_id: str):
    D = db()
    doc = D.documents.find_one({"_id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Document not found")
    chunk_count = D.chunks.count_documents({"doc_id": doc_id})
    tables = list(
        D.tables.find(
            {"doc_id": doc_id},
            {"_id": 1, "page": 1, "index": 1, "n_rows": 1, "n_cols": 1},
        )
    )
    return {"document": doc, "chunk_count": chunk_count, "tables": tables}


@router.get("/documents/{doc_id}/chunks")
def get_doc_chunks(doc_id: str):
    D = db()
    cur = D.chunks.find({"doc_id": doc_id}, {"_id": 1, "seq": 1, "page": 1}).sort(
        [("seq", 1)]
    )
    return {
        "chunks": [
            {"chunk_id": c["_id"], "seq": c["seq"], "page": c.get("page")} for c in cur
        ]
    }
