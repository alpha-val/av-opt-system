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
    cur = D.chunks.find(
        {"properties.doc_id": doc_id}, {"_id": 1, "seq": 1, "page": 1}
    ).sort([("seq", 1)])
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
        query["properties.project_id"] = project_id
    if type:
        query["type"] = type  # string match on the 'type' key in the document
    entities = list(D.entities.find(query, {"_id": 0}))
    return {"entities": entities}


@router_query_vault_data.get("/relations")
def get_entities(project_id: str = None, type: str = None):
    D = db()
    query = {}
    if project_id:
        query["properties.project_id"] = project_id
    if type:
        query["type"] = type  # string match on the 'type' key in the document
    entities = list(D.relations.find(query, {"_id": 0}))
    return {"entities": entities}


@router_query_vault_data.get("/projects/{project_id}/entities-relations")
def get_project_entities_relations(
    project_id: str,
    artifact_type: str = None,  # "base_case", "tabular_data", or "scenarios"
    entity_type: str = None,  # Optional filter by entity type
    relation_type: str = None,  # Optional filter by relation type
    include_metadata: bool = True,
):
    """
    Get entities and relations for a specific project and artifact type

    Args:
        project_id: The project ID to filter by
        artifact_type: Filter by artifact type ("base_case", "tabular_data", "scenarios")
        entity_type: Optional filter by specific entity type
        relation_type: Optional filter by specific relation type
        include_metadata: Whether to include full metadata or just essential fields

    Returns:
        Dictionary containing entities and relations arrays
    """
    try:
        D = db()

        # Build base query for project
        base_query = {"properties.project_id": project_id}

        # If artifact_type is specified, we need to filter by documents of that type first
        if artifact_type:
            # Get document IDs for this project and artifact type
            doc_filter = {
                "project_id": project_id,
                "artifact_type": artifact_type,
                "active": True,
            }

            # Get document IDs
            project_docs = list(D.documents.find(doc_filter, {"doc_id": 1, "_id": 0}))
            doc_ids = [doc["doc_id"] for doc in project_docs]

            if not doc_ids:
                # No documents found for this artifact type
                return {
                    "project_id": project_id,
                    "artifact_type": artifact_type,
                    "entities": [],
                    "relations": [],
                    "summary": {
                        "entity_count": 0,
                        "relation_count": 0,
                        "document_count": 0,
                    },
                }

            # # Update base query to include document filter
            # base_query["doc_id"] = {"$in": doc_ids}

        # Build entities query
        entities_query = base_query.copy()
        if entity_type:
            entities_query["type"] = entity_type

        # Build relations query
        relations_query = base_query.copy()
        if relation_type:
            relations_query["type"] = relation_type

        # Define fields to return
        if include_metadata:
            entity_fields = {"_id": 0}  # Return all fields except MongoDB _id
            relation_fields = {"_id": 0}
        else:
            entity_fields = {
                "_id": 0,
                "entity_id": 1,
                "name": 1,
                "type": 1,
                "doc_id": 1,
                "project_id": 1,
                "confidence": 1,
            }
            relation_fields = {
                "_id": 0,
                "relation_id": 1,
                "source_entity": 1,
                "target_entity": 1,
                "relation_type": 1,
                "doc_id": 1,
                "project_id": 1,
                "confidence": 1,
            }

        # Query entities
        entities_cursor = D.entities.find(entities_query, entity_fields)
        entities = list(entities_cursor)

        # Query relations
        relations_cursor = D.relations.find(relations_query, relation_fields)
        relations = list(relations_cursor)

        # Get entity types summary
        entity_types = {}
        for entity in entities:
            entity_type_key = entity.get("type", "unknown")
            entity_types[entity_type_key] = entity_types.get(entity_type_key, 0) + 1

        # Get relation types summary
        relation_types = {}
        for relation in relations:
            relation_type_key = relation.get(
                "relation_type", relation.get("type", "unknown")
            )
            relation_types[relation_type_key] = (
                relation_types.get(relation_type_key, 0) + 1
            )

        # Build response
        response = {
            "project_id": project_id,
            "artifact_type": artifact_type,
            "entities": entities,
            "relations": relations,
            "summary": {
                "entity_count": len(entities),
                "relation_count": len(relations),
                "entity_types": entity_types,
                "relation_types": relation_types,
            },
        }

        # Add document info if artifact_type was specified
        if artifact_type:
            response["summary"]["document_count"] = len(doc_ids)
            response["summary"]["document_ids"] = doc_ids

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving entities and relations: {str(e)}"
        )


@router_query_vault_data.get("/projects/{project_id}/entities")
def get_project_entities(
    project_id: str,
    artifact_type: str = None,
    entity_type: str = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Get entities for a specific project with optional filtering and pagination
    """
    try:
        D = db()

        # Build query
        query = {"project_id": project_id}

        # Filter by artifact type if specified
        if artifact_type:
            doc_filter = {
                "project_id": project_id,
                "artifact_type": artifact_type,
                "active": True,
            }
            project_docs = list(D.documents.find(doc_filter, {"doc_id": 1, "_id": 0}))
            doc_ids = [doc["doc_id"] for doc in project_docs]

            if doc_ids:
                query["doc_id"] = {"$in": doc_ids}
            else:
                return {"entities": [], "total": 0}

        # Filter by entity type if specified
        if entity_type:
            query["type"] = entity_type

        # Get total count
        total = D.entities.count_documents(query)

        # Get entities with pagination
        entities_cursor = D.entities.find(query, {"_id": 0}).skip(offset).limit(limit)
        entities = list(entities_cursor)

        return {
            "entities": entities,
            "total": total,
            "limit": limit,
            "offset": offset,
            "project_id": project_id,
            "artifact_type": artifact_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving entities: {str(e)}"
        )


@router_query_vault_data.get("/projects/{project_id}/relations")
def get_project_relations(
    project_id: str,
    artifact_type: str = None,
    relation_type: str = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Get relations for a specific project with optional filtering and pagination
    """
    try:
        D = db()

        # Build query
        query = {"project_id": project_id}

        # Filter by artifact type if specified
        if artifact_type:
            doc_filter = {
                "project_id": project_id,
                "artifact_type": artifact_type,
                "active": True,
            }
            project_docs = list(D.documents.find(doc_filter, {"doc_id": 1, "_id": 0}))
            doc_ids = [doc["doc_id"] for doc in project_docs]

            if doc_ids:
                query["doc_id"] = {"$in": doc_ids}
            else:
                return {"relations": [], "total": 0}

        # Filter by relation type if specified
        if relation_type:
            query["relation_type"] = relation_type

        # Get total count
        total = D.relations.count_documents(query)

        # Get relations with pagination
        relations_cursor = D.relations.find(query, {"_id": 0}).skip(offset).limit(limit)
        relations = list(relations_cursor)

        return {
            "relations": relations,
            "total": total,
            "limit": limit,
            "offset": offset,
            "project_id": project_id,
            "artifact_type": artifact_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving relations: {str(e)}"
        )
