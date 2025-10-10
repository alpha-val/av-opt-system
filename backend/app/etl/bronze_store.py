# bronze_store.py
from __future__ import annotations
from typing import List, Dict, Any
import os
from datetime import datetime, timezone  # Add timezone import
from pymongo import MongoClient, UpdateOne, ASCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "alpha_val")

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]


def db():
    return _db


def clear_all_collections():
    """
    Clears all collections in the MongoDB database except users.
    WARNING: Use this only in development or testing environments.
    """
    D = db()  # Get the database instance
    try:
        collections = D.list_collection_names()

        # Collections to skip (preserve users)
        skip_collections = ["users", "projects", "orgs"]

        for collection in collections:
            if collection not in skip_collections:
                D[collection].delete_many({})  # Clear all documents in the collection
                print(f"[CLEAR] Cleared all documents from collection: {collection}")
            else:
                print(f"[SKIP] Preserved collection: {collection}")

        return {"status": "success", "message": "All collections cleared except users."}
    except Exception as e:
        print(f"[CLEAR:ERROR] Failed to clear collections: {e}")
        return {"status": "error", "message": str(e)}


def ensure_bronze_indexes():
    print("[DEBUG] Ensuring indexes on Bronze collections...")

    # Document indexes
    _db.documents.create_index([("_id", ASCENDING)])
    _db.documents.create_index([("sha256", ASCENDING)])

    # Chunk indexes
    _db.chunks.create_index([("_id", ASCENDING)])
    _db.chunks.create_index([("doc_id", ASCENDING), ("seq", ASCENDING)])
    _db.chunks.create_index([("doc_id", ASCENDING), ("page", ASCENDING)])

    # Table indexes
    _db.tables.create_index([("_id", ASCENDING)])
    _db.tables.create_index(
        [("doc_id", ASCENDING), ("page", ASCENDING), ("index", ASCENDING)]
    )

    # Entity indexes
    _db.entities.create_index([("_id", ASCENDING)])
    _db.entities.create_index([("properties.canonical_key", ASCENDING)])
    _db.entities.create_index([("sources.doc_id", ASCENDING)])

    # Relation indexes
    _db.relations.create_index(
        [("source", ASCENDING), ("target", ASCENDING), ("type", ASCENDING)]
    )

    # Project indexes
    _db.projects.create_index([("_id", ASCENDING)])

    # Scenario indexes
    _db.scenarios.create_index([("_id", ASCENDING)])
    _db.scenarios.create_index("project_id")
    _db.scenarios.create_index("created_by")
    _db.scenarios.create_index("status")
    _db.scenarios.create_index([("project_id", 1), ("status", 1)])

    # Option indexes
    _db.options.create_index("id", unique=True)
    _db.options.create_index("scenario_id")
    _db.options.create_index("created_by")
    _db.options.create_index([("scenario_id", 1), ("selected", 1)])

    # User and Org indexes
    _db.users.create_index([("_id", ASCENDING)])
    _db.orgs.create_index([("_id", ASCENDING)])

    # clear_all_collections()  # WARNING: Disable this line in production!


def upsert_document(doc_id: str, payload: Dict[str, Any]):
    payload = dict(payload)
    payload.setdefault("_id", doc_id)
    payload.setdefault("ingested_at", datetime.now(timezone.utc).isoformat())  # Fixed
    _db.documents.replace_one({"_id": doc_id}, payload, upsert=True)


# In etl_base_case.py, add this after the ETL processing:
def store_document_metadata(
    doc_id, filename, project_id, user_id, artifact_type="project_description"
):
    """Store document metadata in the documents collection"""
    try:
        document_metadata = {
            "properties": {
                "doc_id": doc_id,
                "project_id": project_id,
                "user_id": user_id,
                "fileName": filename,
                "originalName": filename,
                "fileType": "pdf",
                "artifact_type": artifact_type,
                "processing_status": "completed",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "active": True,
            }
        }

        # Insert or update document metadata
        _db.documents.update_one(
            {"doc_id": doc_id}, {"$set": document_metadata}, upsert=True
        )

        print(f"Stored document metadata: {document_metadata}")
        return document_metadata

    except Exception as e:
        print(f"Error storing document metadata: {e}")
        return None


def bulk_upsert_chunks(chunks: List[Dict[str, Any]]):
    if not chunks:
        return
    ops = []
    for c in chunks:
        d = {
            "_id": c["chunk_id"],
            "properties": c["properties"],
            "seq": c["seq"],
            "page": c.get("page"),
            "text_raw": c.get("text_raw"),
            "text_clean": c.get("text"),
            "source": "pdf",
        }
        ops.append(UpdateOne({"_id": d["_id"]}, {"$set": d}, upsert=True))
    _db.chunks.bulk_write(ops, ordered=False)


def upsert_table(
    doc_id: str,
    table_id: str,
    meta: Dict[str, Any],
    preview_rows: List[Dict[str, Any]],
    n_cols: int,
    properties: Dict[str, Any] = None,
):
    rec = {
        "_id": table_id,
        "doc_id": doc_id,
        "page": meta.get("page"),
        "index": meta.get("index"),
        "flavor": meta.get("flavor"),
        "n_rows": len(preview_rows),
        "n_cols": n_cols,
        "preview": preview_rows[:5],
        "properties": properties or {},
    }
    _db.tables.replace_one({"_id": table_id}, rec, upsert=True)


def bulk_upsert_rows(rows: List[Dict[str, Any]]):
    if not rows:
        return
    ops = [UpdateOne({"_id": r["_id"]}, {"$set": r}, upsert=True) for r in rows]
    _db.rows.bulk_write(ops, ordered=False)


def bulk_upsert_entities(nodes: List[Dict[str, Any]]):
    if not nodes:
        return
    ops = []
    for n in nodes:
        n = dict(n)
        _id = n.get("id") or n.get("_id")
        if not _id:
            continue
        n["_id"] = _id
        n.pop("id", None)
        ops.append(UpdateOne({"_id": _id}, {"$set": n}, upsert=True))
    _db.entities.bulk_write(ops, ordered=False)


def bulk_upsert_relations(edges: List[Dict[str, Any]]):
    if not edges:
        return
    ops = []
    for e in edges:
        if not e.get("source") or not e.get("target") or not e.get("type"):
            continue
        filt = {"source": e["source"], "target": e["target"], "type": e["type"]}
        ops.append(UpdateOne(filt, {"$set": e}, upsert=True))
    if ops:
        _db.relations.bulk_write(ops, ordered=False)


def bulk_upsert_mentions(mentions: List[Dict[str, Any]]):
    if not mentions:
        return
    ops = []
    for m in mentions:
        _id = m.get("_id")
        if not _id:
            _id = f"{m.get('chunk_id')}|{m.get('entity_id')}|{m.get('span_start')}|{m.get('span_end')}"
            m["_id"] = _id
        ops.append(UpdateOne({"_id": _id}, {"$set": m}, upsert=True))
    if ops:
        _db.mentions.bulk_write(ops, ordered=False)
