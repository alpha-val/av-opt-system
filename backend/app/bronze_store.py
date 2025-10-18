# bronze_store.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timezone  # Add timezone import
from pymongo import MongoClient, UpdateOne, ASCENDING
import uuid

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "alpha_val")

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]


def db():
    return _db


# def clear_all_collections():
#     """
#     Clears all collections in the MongoDB database except users.
#     WARNING: Use this only in development or testing environments.
#     """
#     D = db()  # Get the database instance
#     try:
#         collections = D.list_collection_names()

#         # Collections to skip (preserve users)
#         skip_collections = ["users", "projects", "orgs"]

#         for collection in collections:
#             if collection not in skip_collections:
#                 D[collection].delete_many({})  # Clear all documents in the collection
#                 print(f"[CLEAR] Cleared all documents from collection: {collection}")
#             else:
#                 print(f"[SKIP] Preserved collection: {collection}")

#         return {"status": "success", "message": "All collections cleared except users."}
#     except Exception as e:
#         print(f"[CLEAR:ERROR] Failed to clear collections: {e}")
#         return {"status": "error", "message": str(e)}


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

    # Cost Estimate indexes
    _db.cost_estimates.create_index("id", unique=True)
    _db.cost_estimates.create_index("estimate_id")
    _db.cost_estimates.create_index("created_by")
    _db.cost_estimates.create_index([("estimate_id", 1), ("selected", 1)])

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
    """
    Bulk upsert chunks. Each chunk must have an id.
    """
    if not chunks:
        return

    for chunk in chunks:
        # Generate _id if it doesn't exist
        if "_id" not in chunk:
            if "id" in chunk:
                chunk["_id"] = chunk["id"]
            else:
                chunk["_id"] = str(uuid.uuid4())
                chunk["id"] = chunk["_id"]

        # Ensure id matches _id
        if "id" not in chunk:
            chunk["id"] = chunk["_id"]

        # Ensure timestamps
        if "created_at" not in chunk:
            chunk["created_at"] = datetime.utcnow()
        if "updated_at" not in chunk:
            chunk["updated_at"] = datetime.utcnow()

    # Upsert to MongoDB
    ops = []
    for chunk in chunks:
        ops.append(
            UpdateOne(
                {"_id": chunk["_id"]},
                {"$set": chunk},
                upsert=True,
            )
        )

    if ops:
        result = db().chunks.bulk_write(ops, ordered=False)
        print(
            f"[bulk_upsert_chunks] Matched: {result.matched_count}, "
            f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
        )


def upsert_table(
    doc_id: str,
    table_id: str,
    meta: Dict[str, Any],
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Upsert a table document in the 'tables' collection.

    Args:
        doc_id: Document ID
        table_id: Unique table ID
        meta: Table metadata (all fields to store)
        properties: Additional properties (optional, defaults to meta)

    Returns:
        The stored document
    """

    if properties is None:
        properties = meta

    # Build the document - meta contains everything
    doc = {
        "_id": table_id,
        "doc_id": doc_id,
        "table_id": table_id,
        "id": table_id,
        **meta,  # Spread all meta fields into doc
    }

    # Add properties if different from meta
    if properties != meta:
        doc["properties"] = properties

    _db.tables.replace_one(
        {"_id": table_id},
        doc,
        upsert=True,
    )

    return doc


def bulk_upsert_rows(rows: List[Dict[str, Any]]):
    if not rows:
        return
    ops = [
        UpdateOne({"_id": r["_id"]}, {"id": r["_id"]}, {"$set": r}, upsert=True)
        for r in rows
    ]
    _db.rows.bulk_write(ops, ordered=False)


def bulk_upsert_entities(entities: List[Dict[str, Any]]):
    """
    Bulk upsert entities. Each entity should have an id, name, type, etc.
    """
    if not entities:
        return

    for ent in entities:
        # Generate _id if it doesn't exist
        if "_id" not in ent:
            if "id" in ent:
                ent["_id"] = ent["id"]
            else:
                # Generate UUID if no id exists
                ent["_id"] = str(uuid.uuid4())
                ent["id"] = ent["_id"]

        # Ensure id matches _id
        if "id" not in ent:
            ent["id"] = ent["_id"]

        # Ensure timestamps
        if "created_at" not in ent:
            ent["created_at"] = datetime.utcnow()  # ✅ Now works
        if "updated_at" not in ent:
            ent["updated_at"] = datetime.utcnow()  # ✅ Now works

    # Upsert to MongoDB
    ops = []
    for ent in entities:
        ops.append(
            UpdateOne(
                {"_id": ent["_id"]},
                {"$set": ent},
                upsert=True,
            )
        )

    if ops:
        result = db().entities.bulk_write(ops, ordered=False)
        print(
            f"[bulk_upsert_entities] Matched: {result.matched_count}, "
            f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
        )


def bulk_upsert_relations(edges: List[Dict[str, Any]]):
    """
    Bulk upsert relations. Each edge must have source, target, type.
    """
    if not edges:
        return

    for e in edges:
        # Generate _id if it doesn't exist
        if "_id" not in e:
            e["_id"] = f"{e['source']}|{e['target']}|{e['type']}"

        # Set id to match _id
        e["id"] = e["_id"]

        # Ensure timestamps
        if "created_at" not in e:
            e["created_at"] = datetime.utcnow()  # ✅ Now works
        if "updated_at" not in e:
            e["updated_at"] = datetime.utcnow()  # ✅ Now works

    # Upsert to MongoDB
    ops = []
    for e in edges:
        ops.append(
            UpdateOne(
                {"_id": e["_id"]},
                {"$set": e},
                upsert=True,
            )
        )

    if ops:
        result = db().relations.bulk_write(ops, ordered=False)
        print(
            f"[bulk_upsert_relations] Matched: {result.matched_count}, "
            f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
        )


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


def get_tables(
    project_id: Optional[str] = None,
    doc_id: Optional[str] = None,
    table_ids: Optional[List[str]] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch table metadata from Bronze tables collection.

    Args:
        project_id: Filter by project
        doc_id: Filter by document
        table_ids: Filter by specific table IDs
        limit: Maximum tables to return

    Returns:
        List of table metadata dictionaries
    """
    query = {}

    if project_id:
        query["project_id"] = project_id

    if doc_id:
        query["doc_id"] = doc_id

    if table_ids:
        query["table_id"] = {"$in": table_ids}

    try:
        cursor = _db.tables.find(query).limit(limit)
        tables = list(cursor)
        return tables
    except Exception as e:
        print(f"[BRONZE_STORE] - Failed to fetch tables: {e}")
        return []


def get_rows_for_table(table_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch all rows for a specific table from Bronze rows collection.

    Args:
        table_id: Table identifier
        limit: Maximum rows to return

    Returns:
        List of row documents
    """
    try:
        cursor = _db.rows.find({"table_id": table_id}).sort("row_idx", 1).limit(limit)

        rows = list(cursor)
        return rows
    except Exception as e:
        print(f"[BRONZE_STORE] - Failed to fetch rows for table {table_id}: {e}")
        return []
