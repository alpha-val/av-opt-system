from __future__ import annotations
from typing import Dict, Optional, List
from datetime import datetime, timezone
from bson import ObjectId  # For MongoDB ObjectId handling
from ...adapters.mongo.client import db  # Import the MongoDB client
from .schemas import ProjectCreate, ProjectUpdate, ProjectOut

# Get the MongoDB projects collection
_projects_collection = db().projects


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
