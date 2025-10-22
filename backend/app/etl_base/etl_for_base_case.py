# etl_bronze.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
import os, tempfile, uuid, datetime
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.text_clean import extract_and_clean, chunk_by_page, process_extracted_nodes, NAMESPACE
from app.bronze_store import (
    bulk_upsert_chunks,
    bulk_upsert_entities,
    bulk_upsert_relations,
)
from app.vector_db.vector_operations import upsert_entities_to_pinecone
from .extract_with_openai import openai_extract_nodes_rels


def etl_base_case(
    file: UploadFile = File(...),
    pages: Optional[str] = Form(None),
    project_id: str = Form(...),
    doc_id: str = Form(...),
    user_id: str = Form(...),
    artifact_type: str = Form("base_case"),
):
    """Ingest a PDF into Bronze: text chunks, tables/rows, entities/relations/mentions."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"
    file_size = len(pdf_bytes)

    # 1) Text extract + clean
    some_id, file_sha, pages_raw, pages_clean = extract_and_clean(pdf_bytes, filename)

    # 2) Build page chunks (Bronze)
    chunks = chunk_by_page(pages_clean, doc_id)
    raw_by_page = {p: t for p, t in pages_raw}
    for c in chunks:
        c["text_raw"] = raw_by_page.get(c["page"])
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in c or not isinstance(c["properties"], dict):
            c["properties"] = {}
        c["properties"]["artifact_type"] = artifact_type
        c["properties"]["project_id"] = project_id
        c["properties"]["user_id"] = user_id
        c["properties"]["doc_id"] = doc_id

    # 3) Entities/relations/mentions from free text (Bronze)
    # kg = _extract_entities_mentions(chunks)
    kg = openai_extract_nodes_rels(chunks, rules=["Units_Normalization", "Cost_Rule"])
    nodes = list(kg.get("nodes", []) or [])
    edges = list(kg.get("edges", []) or [])

    # Attach simple source back-pointer to each node
    for n in nodes:
        srcs = n.get("sources") or []
        if not any(isinstance(s, dict) and s.get("doc_id") == doc_id for s in srcs):
            srcs.append({"doc_id": doc_id})
        n["sources"] = srcs
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in n or not isinstance(n["properties"], dict):
            n["properties"] = {}
        n["properties"]["artifact_type"] = artifact_type
        n["properties"]["project_id"] = project_id
        n["properties"]["user_id"] = user_id
        n["properties"]["doc_id"] = doc_id
        
    # Apply additional processing to nodes if needed
    nodes = process_extracted_nodes(nodes)

    for e in edges:
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in e or not isinstance(e["properties"], dict):
            e["properties"] = {}
        e["properties"]["artifact_type"] = artifact_type
        e["properties"]["project_id"] = project_id
        e["properties"]["user_id"] = user_id
        e["properties"]["doc_id"] = doc_id

    # 4) Store in MongoDB
    bulk_upsert_chunks(chunks)
    bulk_upsert_entities(nodes)
    bulk_upsert_relations(edges)

    # ========== NEW: Store in Vector Database ==========
    vectors_upserted = 0
    try:
        vectors_upserted = upsert_entities_to_pinecone(
            entities=nodes, project_id=project_id, artifact_type=artifact_type
        )
        print(f"[INFO] Upserted {vectors_upserted} vectors to Pinecone")
    except Exception as e:
        print(f"[ERROR] Failed to upsert to Pinecone: {e}")
        # Don't fail the entire ETL if vector upsert fails
        # Vector DB can be rebuilt later from MongoDB
    # ===================================================

    return {
        "filename": filename,
        "file_size": file_size,
        "file_sha256": file_sha,
        "pages": len(pages_clean),
        "chunks_written": len(chunks),
        "entities_written": len(nodes),
        "relations_written": len(edges),
        "vectors_upserted": vectors_upserted,  # NEW: Return vector count
    }
