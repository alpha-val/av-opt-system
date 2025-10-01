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
    clear_all_collections,
    ensure_bronze_indexes,
    store_document_metadata,
    upsert_document,
)

# Create API router
router_base_case = APIRouter()


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


@router_base_case.post("/etl_base_case")
def etl_bronze(
    file: UploadFile = File(...),
    pages: Optional[str] = Form(None),
    project_id: str = Form(...),
    user_id: str = Form(...),
    artifact_type: str = Form("base_case"),
):
    """Ingest a PDF into Bronze: text chunks, tables/rows, entities/relations/mentions."""
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
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in c or not isinstance(c["properties"], dict):
            c["properties"] = {}
        c["properties"]["artifact_type"] = artifact_type
        c["properties"]["project_id"] = project_id
        c["properties"]["user_id"] = user_id
        c["properties"]["doc_id"] = doc_id

    # 3) Entities/relations/mentions from free text (Bronze)
    kg = _extract_entities_mentions(chunks)
    nodes = list(kg.get("nodes", []) or [])
    edges = list(kg.get("edges", []) or [])
    # mentions = list(kg.get("mentions", []) or [])

    # Attach simple source back-pointer to each node; ensure deterministic mention IDs
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

    for e in edges:
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in e or not isinstance(e["properties"], dict):
            e["properties"] = {}
        e["properties"]["artifact_type"] = artifact_type
        e["properties"]["project_id"] = project_id
        e["properties"]["user_id"] = user_id
        e["properties"]["doc_id"] = doc_id

    # for m in mentions:
    #     m["_id"] = _mention_id(
    #         chunk_id=m.get("chunk_id"),
    #         entity_id=m.get("entity_id"),
    #         span_start=m.get("span_start"),
    #         span_end=m.get("span_end"),
    #         surface=m.get("surface"),
    #     )
    #     # Add project_id, user_id to mentions
    #     m["project_id"] = project_id
    #     m["user_id"] = user_id

    # 4) Store document metadata in documents collection
    try:
        doc_metadata = store_document_metadata(
            doc_id=doc_id,
            filename=filename,
            project_id=project_id,
            user_id=user_id,
            artifact_type=artifact_type,
        )
        print(f"[ETL:BRONZE] - Stored document metadata: {doc_metadata}")
    except Exception as e:
        print(f"[ETL:BRONZE] - Failed to store document metadata: {e}")
        doc_metadata = None

    bulk_upsert_chunks(chunks)
    bulk_upsert_entities(nodes)
    bulk_upsert_relations(edges)
    # bulk_upsert_mentions(mentions)

    return {
        "doc_id": doc_id,
        "filename": filename,
        "pages": len(pages_clean),
        "chunks_written": len(chunks),
        "entities_written": len(nodes),
        "relations_written": len(edges),
        # "mentions_written": len(mentions),
        "user_id": user_id,
        "project_id": project_id,
        "document_metadata": doc_metadata,
    }
