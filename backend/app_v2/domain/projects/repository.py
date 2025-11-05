from __future__ import annotations
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from bson import ObjectId  # For MongoDB ObjectId handling
from ...adapters.mongo.client import db  # Import the MongoDB client
from .schemas import ProjectCreate, ProjectUpdate, ProjectOut, EntityOut, RelationOut, ProjectEntitiesRelationsOut
import logging

logger = logging.getLogger(__name__)

# Get the MongoDB projects collection
_projects_collection = db().projects
_documents_collection = db().documents
_chunks_collection = db().chunks
_entities_collection = db().entities
_relations_collection = db().relations
_tables_collection = db().tables
_scenarios_collection = db().scenarios
_cost_estimates_collection = db().cost_estimates


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_project(data: ProjectCreate) -> ProjectOut:
    """Create a new project in the MongoDB collection."""
    doc = {
        "name": data.name,
        "description": data.description,
        "tags": data.tags or [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = _projects_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)  # Convert ObjectId to string
    return ProjectOut(**doc)


async def list_projects() -> List[ProjectOut]:
    """List all projects from the MongoDB collection."""
    projects = _projects_collection.find()
    return [ProjectOut(**{**p, "id": str(p["_id"])}) for p in projects]


async def get_project(project_id: str) -> Optional[ProjectOut]:
    """Get a project by its ID from the MongoDB collection."""
    project = _projects_collection.find_one({"_id": ObjectId(project_id)})
    if not project:
        return None
    project["id"] = str(project["_id"])  # Convert ObjectId to string
    return ProjectOut(**project)


async def update_project(project_id: str, patch: ProjectUpdate) -> Optional[ProjectOut]:
    """Update a project in the MongoDB collection."""
    data = patch.model_dump(exclude_unset=True)
    data["updated_at"] = _now()
    result = _projects_collection.find_one_and_update(
        {"_id": ObjectId(project_id)},
        {"$set": data},
        return_document=True,
    )
    if not result:
        return None
    result["id"] = str(result["_id"])  # Convert ObjectId to string
    return ProjectOut(**result)


async def delete_project(project_id: str) -> bool:
    """Delete a project from the MongoDB collection."""
    result = _projects_collection.delete_one({"_id": ObjectId(project_id)})
    return result.deleted_count > 0

async def clear_project_data(project_id: str) -> Dict[str, Any]:
    """
    Clear all data associated with a project by ID, but not the project itself.
    
    Returns dictionary with deletion counts for each collection and Pinecone cleanup status.
    """
    # Delete from MongoDB collections
    documents_deleted = _documents_collection.delete_many({"project_id": project_id}).deleted_count
    chunks_deleted = _chunks_collection.delete_many({"properties.project_id": project_id}).deleted_count
    entities_deleted = _entities_collection.delete_many({"properties.project_id": project_id}).deleted_count
    relations_deleted = _relations_collection.delete_many({"properties.project_id": project_id}).deleted_count
    tables_deleted = _tables_collection.delete_many({"properties.project_id": project_id}).deleted_count
    scenarios_deleted = _scenarios_collection.delete_many({"properties.project_id": project_id}).deleted_count
    cost_estimates_deleted = _cost_estimates_collection.delete_many({"properties.project_id": project_id}).deleted_count
    
    # Clear Pinecone vectors for this project namespace
    vectors_cleared = False
    try:
        from app_v2.domain.parsing.storage.vector_store import _get_pinecone_index
        index = _get_pinecone_index()
        # Delete all vectors in the project namespace
        index.delete(delete_all=True, namespace=project_id)
        vectors_cleared = True
        logger.info(f"Cleared Pinecone vectors for project {project_id}")
    except Exception as e:
        logger.warning(f"Failed to clear Pinecone vectors for project {project_id}: {e}")
    
    total_deleted = (
        documents_deleted + chunks_deleted + entities_deleted + 
        relations_deleted + tables_deleted + scenarios_deleted + 
        cost_estimates_deleted
    )
    
    return {
        "project_id": project_id,
        "deleted_counts": {
            "documents": documents_deleted,
            "chunks": chunks_deleted,
            "entities": entities_deleted,
            "relations": relations_deleted,
            "tables": tables_deleted,
            "scenarios": scenarios_deleted,
            "cost_estimates": cost_estimates_deleted,
            "vectors_cleared": vectors_cleared,
        },
        "total_items": total_deleted,
    }
    
    
def _normalize_entity_for_output(entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize entity from MongoDB format to EntityOut format.
    
    Ensures required fields (name, type) are at top level, extracting from
    properties if needed.
    """
    props = entity.get("properties", {})
    
    # Extract name from properties if not at top level
    name = entity.get("name") or props.get("name") or entity.get("id", "Unknown")
    
    # Extract type from properties if not at top level
    entity_type = entity.get("type") or props.get("type") or "Entity"
    
    # Ensure properties dict exists
    if not isinstance(props, dict):
        props = {}
    
    # Build normalized entity
    normalized = {
        "id": str(entity.get("_id") or entity.get("id", "")),
        "name": name,
        "type": entity_type,
        "properties": props,
        "created_at": entity.get("created_at") or _now(),
        "updated_at": entity.get("updated_at") or _now(),
    }
    
    return normalized


def _normalize_relation_for_output(relation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize relation from MongoDB format to RelationOut format.
    
    Ensures required fields (source, target, type) are at top level, extracting from
    properties if needed.
    """
    props = relation.get("properties", {})
    
    # Extract source from properties if not at top level or is None
    source = relation.get("source") or props.get("source") or ""
    
    # Extract target from properties if not at top level or is None
    target = relation.get("target") or props.get("target") or ""
    
    # Extract type from properties if not at top level or is None
    relation_type = relation.get("type") or props.get("type") or "RELATED_TO"
    
    # Ensure properties dict exists
    if not isinstance(props, dict):
        props = {}
    
    # Build normalized relation
    normalized = {
        "id": str(relation.get("_id") or relation.get("id", "")),
        "source": str(source) if source is not None else "",
        "target": str(target) if target is not None else "",
        "type": str(relation_type) if relation_type is not None else "RELATED_TO",
        "properties": props,
        "created_at": relation.get("created_at") or _now(),
        "updated_at": relation.get("updated_at") or _now(),
    }
    
    return normalized


async def get_project_entities_relations(project_id: str) -> ProjectEntitiesRelationsOut:
    """Get entities and relations for a project from the MongoDB collection."""
    entities = list(_entities_collection.find({"properties.project_id": project_id}))
    relations = list(_relations_collection.find({"properties.project_id": project_id}))
    
    # Normalize entities and relations before creating output objects
    normalized_entities = [_normalize_entity_for_output(e) for e in entities]
    normalized_relations = [_normalize_relation_for_output(r) for r in relations]
    
    return ProjectEntitiesRelationsOut(
        entities=[EntityOut(**e) for e in normalized_entities],
        relations=[RelationOut(**r) for r in normalized_relations],
        summary={
            "entity_count": len(entities),
            "relation_count": len(relations),
        },
        project_id=project_id,
    )