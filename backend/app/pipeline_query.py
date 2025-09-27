# etl_bronze.py
from __future__ import annotations
import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .text_clean import extract_and_clean, chunk_by_page, NAMESPACE
from .bronze_store import (
    db,
)

# Create API router
router_query_vault_data = APIRouter()

# Utility to check MongoDB connection
@router_query_vault_data.get("/test-mongo-connection")
def test_mongo_connection():
    try:
        # Attempt to connect to the database
        # NOTE: DOES NOT WORK ON VPN !!!
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

# Get Document Summary
@router_query_vault_data.get("/documents/{doc_id}/summary")
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

# Get Document Chunks
@router_query_vault_data.get("/documents/{doc_id}/chunks")
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

@router_query_vault_data.get("/entities")
def get_entities(project_id: str = None, type: str = None):
    D = db()
    query = {}
    if project_id:
        query["project_id"] = project_id
    if type:
        query["type"] = type  # string match on the 'type' key in the document
    entities = list(D.entities.find(query, {"_id": 0}))
    return {"entities": entities}

@router_query_vault_data.get("/relations")
def get_entities(project_id: str = None, type: str = None):
    D = db()
    query = {}
    if project_id:
        query["project_id"] = project_id
    if type:
        query["type"] = type  # string match on the 'type' key in the document
    entities = list(D.relations.find(query, {"_id": 0}))
    return {"entities": entities}