# bronze_store.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timezone  # Add timezone import
from pymongo import MongoClient, UpdateOne, ASCENDING
import uuid

# Load MongoDB configuration from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "alpha_val")

# Initialize MongoDB client with SSL/TLS support for Atlas connections
# For mongodb+srv://, pymongo automatically handles SSL/TLS - don't override
# For mongodb:// with Atlas, ensure SSL is enabled
_client_kwargs = {}
if "mongodb+srv" in MONGO_URI:
    # mongodb+srv automatically handles SSL/TLS, just add connection options
    _client_kwargs = {
        "retryWrites": True,
        "w": "majority",
    }
elif "mongodb.net" in MONGO_URI:
    # For mongodb:// with Atlas, explicitly enable TLS
    # Note: mongodb+srv:// is recommended for Atlas
    _client_kwargs = {
        "tls": True,
        "retryWrites": True,
        "w": "majority",
    }

# Initialize MongoDB client and database
_client = MongoClient(MONGO_URI, **_client_kwargs)
_db = _client[MONGO_DB]


def db():
    try:
        return _db
    except Exception as e:
        print(f"[ERROR : client.py] Failed to connect to the database: {e}")
        raise


def ensure_bronze_indexes():
    try:
        print("[DEBUG : client.py] Ensuring indexes on Bronze collections...")

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
        _db.scenarios.create_index("id", unique=True)
        _db.scenarios.create_index("properties.project_id")
        _db.scenarios.create_index("properties.created_by")
        _db.scenarios.create_index("properties.status")
        _db.scenarios.create_index(
            [("properties.project_id", 1), ("properties.status", 1)]
        )

        # Cost Estimate indexes
        _db.cost_estimates.create_index("id", unique=True)
        _db.cost_estimates.create_index("estimate_id")
        _db.cost_estimates.create_index("created_by")
        _db.cost_estimates.create_index([("estimate_id", 1), ("selected", 1)])

        # User and Org indexes
        _db.users.create_index([("_id", ASCENDING)])
        _db.orgs.create_index([("_id", ASCENDING)])

        print("[DEBUG : client.py] Indexes ensured on Bronze collections.")
    except Exception as e:
        print(f"[ERROR : client.py] Failed to ensure indexes: {e}")
        raise
