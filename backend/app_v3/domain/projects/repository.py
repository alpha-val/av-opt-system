"""
Project repository for MongoDB operations.

This module handles all database operations for projects, including CRUD operations.
It abstracts MongoDB-specific details and provides a clean interface for the service layer.
"""

from __future__ import annotations
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from bson import ObjectId  # For MongoDB ObjectId handling
from bson.errors import InvalidId  # For handling invalid ObjectId strings
from ...adapters.mongo.client import db  # Import the MongoDB client
from .schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectStatus,
)
import logging

logger = logging.getLogger(__name__)

# Get the MongoDB projects collection
# This collection stores all project documents
_projects_collection = db().projects

# Related collections for project data
# These are used when clearing project data
_entities_collection = db().entities
_relations_collection = db().relations


def _now() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)


def _validate_object_id(project_id: str) -> ObjectId:
    """
    Validate and convert string ID to MongoDB ObjectId.
    
    Args:
        project_id: String representation of MongoDB ObjectId
        
    Returns:
        ObjectId instance
        
    Raises:
        ValueError: If project_id is not a valid ObjectId string
    """
    try:
        return ObjectId(project_id)
    except (InvalidId, TypeError) as e:
        logger.warning(f"Invalid project_id format: {project_id}")
        raise ValueError(f"Invalid project_id format: {project_id}") from e


async def create_project(data: ProjectCreate) -> ProjectOut:
    """
    Create a new project in the MongoDB collection.
    
    Args:
        data: ProjectCreate schema with project data
        
    Returns:
        ProjectOut: Created project with generated ID and timestamps
        
    Raises:
        ValueError: If required fields (global_objective_type, global_objective_target) are missing
        Exception: If database operation fails
    """
    try:
        # Validate required fields
        if not data.global_objective_type:
            raise ValueError("global_objective_type is required")
        if not data.global_objective_target:
            raise ValueError("global_objective_target is required")
        
        # Build document for insertion
        doc = {
            "name": data.name,
            "description": data.description,
            "tags": data.tags or [],  # Default to empty list if None
            "global_objective_type": data.global_objective_type,
            "global_objective_target": data.global_objective_target,
            "objective_description": data.objective_description,
            "status": data.status.value if hasattr(data.status, 'value') else data.status,
            "base_case_documents": data.base_case_documents or [],
            "tabular_data_documents": data.tabular_data_documents or [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        
        # Insert into MongoDB (MongoDB will generate _id automatically)
        result = _projects_collection.insert_one(doc)
        
        # Convert ObjectId to string for output
        doc["id"] = str(result.inserted_id)
        
        logger.info(f"Created project: {doc['id']} - {doc['name']}")
        
        return ProjectOut(**doc)
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise


async def list_projects() -> List[ProjectOut]:
    """
    List all projects from the MongoDB collection.
    
    Returns:
        List[ProjectOut]: List of all projects
        
    Note:
        For large datasets, consider adding pagination support.
    """
    try:
        # Fetch all projects from collection
        projects = _projects_collection.find()
        
        # Convert MongoDB documents to ProjectOut schemas
        # MongoDB uses _id, we convert it to id (string)
        # Also convert status string to enum if needed
        # Provide defaults for new required fields if missing (backward compatibility)
        result = []
        for p in projects:
            doc = {**p, "id": str(p["_id"])}
            # Provide defaults for new required fields if missing (backward compatibility)
            if "global_objective_type" not in doc:
                doc["global_objective_type"] = "not specified"
            if "global_objective_target" not in doc:
                doc["global_objective_target"] = "not specified"
            if "base_case_documents" not in doc:
                doc["base_case_documents"] = []
            if "tabular_data_documents" not in doc:
                doc["tabular_data_documents"] = []
            # Convert status string to enum if it's a string
            if "status" in doc and isinstance(doc["status"], str):
                try:
                    doc["status"] = ProjectStatus(doc["status"])
                except ValueError:
                    # Invalid status, use default
                    doc["status"] = ProjectStatus.DRAFT
            elif "status" not in doc:
                doc["status"] = ProjectStatus.DRAFT
            result.append(ProjectOut(**doc))
        
        logger.info(f"Listed {len(result)} projects")
        return result
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        raise


async def get_project(project_id: str) -> Optional[ProjectOut]:
    """
    Get a project by its ID from the MongoDB collection.
    
    Args:
        project_id: String representation of MongoDB ObjectId
        
    Returns:
        ProjectOut if found, None otherwise
        
    Raises:
        ValueError: If project_id is not a valid ObjectId format
    """
    try:
        # Validate and convert ID
        obj_id = _validate_object_id(project_id)
        
        # Find project by _id
        project = _projects_collection.find_one({"_id": obj_id})
        
        if not project:
            logger.debug(f"Project not found: {project_id}")
            return None
        
        # Convert ObjectId to string for output
        project["id"] = str(project["_id"])
        
        # Provide defaults for new required fields if missing (backward compatibility)
        if "global_objective_type" not in project:
            project["global_objective_type"] = "not specified"
        if "global_objective_target" not in project:
            project["global_objective_target"] = "not specified"
        if "base_case_documents" not in project:
            project["base_case_documents"] = []
        if "tabular_data_documents" not in project:
            project["tabular_data_documents"] = []
        
        # Convert status string to enum if needed
        if "status" in project and isinstance(project["status"], str):
            try:
                project["status"] = ProjectStatus(project["status"])
            except ValueError:
                # Invalid status, use default
                project["status"] = ProjectStatus.DRAFT
        elif "status" not in project:
            project["status"] = ProjectStatus.DRAFT
        
        return ProjectOut(**project)
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}", exc_info=True)
        raise


async def update_project(project_id: str, patch: ProjectUpdate) -> Optional[ProjectOut]:
    """
    Update a project in the MongoDB collection.
    
    Only fields provided in the patch will be updated (partial update).
    The updated_at timestamp is automatically updated.
    
    Args:
        project_id: String representation of MongoDB ObjectId
        patch: ProjectUpdate schema with fields to update
        
    Returns:
        ProjectOut if project found and updated, None if project not found
        
    Raises:
        ValueError: If project_id is not a valid ObjectId format
    """
    try:
        # Validate and convert ID
        obj_id = _validate_object_id(project_id)
        
        # Build update document (only include fields that are set)
        # model_dump(exclude_unset=True) only includes fields that were explicitly set
        data = patch.model_dump(exclude_unset=True)
        
        # Convert status enum to string if present
        if "status" in data and hasattr(data["status"], "value"):
            data["status"] = data["status"].value
        
        # Always update the updated_at timestamp
        data["updated_at"] = _now()
        
        # Update document and return updated version
        # return_document=True returns the updated document instead of the original
        result = _projects_collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": data},  # $set operator updates only specified fields
            return_document=True,  # Return updated document
        )
        
        if not result:
            logger.debug(f"Project not found for update: {project_id}")
            return None
        
        # Convert ObjectId to string for output
        result["id"] = str(result["_id"])
        
        # Provide defaults for new required fields if missing (backward compatibility)
        if "global_objective_type" not in result:
            result["global_objective_type"] = "not specified"
        if "global_objective_target" not in result:
            result["global_objective_target"] = "not specified"
        if "base_case_documents" not in result:
            result["base_case_documents"] = []
        if "tabular_data_documents" not in result:
            result["tabular_data_documents"] = []
        
        # Convert status string to enum if needed
        if "status" in result and isinstance(result["status"], str):
            try:
                result["status"] = ProjectStatus(result["status"])
            except ValueError:
                # Invalid status, use default
                result["status"] = ProjectStatus.DRAFT
        elif "status" not in result:
            result["status"] = ProjectStatus.DRAFT
        
        logger.info(f"Updated project: {project_id}")
        return ProjectOut(**result)
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}", exc_info=True)
        raise


async def delete_project(project_id: str) -> bool:
    """
    Delete a project from the MongoDB collection.
    
    Args:
        project_id: String representation of MongoDB ObjectId
        
    Returns:
        True if project was deleted, False if project not found
        
    Raises:
        ValueError: If project_id is not a valid ObjectId format
        
    Note:
        This only deletes the project document. Associated data (entities,
        relations, etc.) are not automatically deleted. Use clear_project_data()
        if you need to clean up related data.
    """
    try:
        # Validate and convert ID
        obj_id = _validate_object_id(project_id)
        
        # Delete project document
        result = _projects_collection.delete_one({"_id": obj_id})
        
        deleted = result.deleted_count > 0
        
        if deleted:
            logger.info(f"Deleted project: {project_id}")
        else:
            logger.debug(f"Project not found for deletion: {project_id}")
        
        return deleted
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}", exc_info=True)
        raise


async def clear_project_data(project_id: str) -> Dict[str, Any]:
    """
    Clear all data associated with a project, but keep the project itself.
    
    This deletes entities, relations, and other related data for a project.
    The project document itself is not deleted.
    
    Args:
        project_id: String representation of MongoDB ObjectId
        
    Returns:
        Dictionary with deletion counts for each collection
        
    Note:
        This is a destructive operation. Use with caution.
        Consider adding user confirmation or soft-delete patterns.
    """
    try:
        # Validate project exists
        obj_id = _validate_object_id(project_id)
        project = _projects_collection.find_one({"_id": obj_id})
        
        if not project:
            logger.warning(f"Project not found for data clearing: {project_id}")
            return {
                "project_id": project_id,
                "error": "Project not found",
                "deleted_counts": {},
            }
        
        # Delete related data from various collections
        # All related data should have project_id in properties
        entities_deleted = _entities_collection.delete_many(
            {"properties.project_id": project_id}
        ).deleted_count
        
        relations_deleted = _relations_collection.delete_many(
            {"properties.project_id": project_id}
        ).deleted_count
        
        logger.info(
            f"Cleared project data for {project_id}: "
            f"{entities_deleted} entities, {relations_deleted} relations"
        )
        
        return {
            "project_id": project_id,
            "deleted_counts": {
                "entities": entities_deleted,
                "relations": relations_deleted,
            },
            "total_items": entities_deleted + relations_deleted,
        }
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error clearing project data {project_id}: {e}", exc_info=True)
        raise



