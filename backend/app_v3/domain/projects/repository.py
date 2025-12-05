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
from pymongo import ASCENDING
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
_base_case_summaries_collection = db().base_case_summaries
_base_case_recommendations_collection = db().base_case_recommendations
_chunks_collection = db().chunks
_cost_estimates_collection = db().cost_estimates
_documents_collection = db().documents
_entities_collection = db().entities
_relations_collection = db().relations
_scenarios_collection = db().scenarios
_tables_collection = db().tables
_users_collection = db().users
_orgs_collection = db().orgs


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
        data: ProjectCreate schema with project data (only name is required)

    Returns:
        ProjectOut: Created project with generated ID and timestamps

    Raises:
        ValueError: If required fields (name) are missing
        Exception: If database operation fails
    """
    try:
        # Build document for insertion
        doc = {
            "name": data.name,
            "description": data.description,
            "tags": data.tags or [],  # Default to empty list if None
            "status": (
                data.status.value if hasattr(data.status, "value") else data.status
            ),
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

    This deletes all related data including:
    - Scenarios and their cost estimates
    - Scenario analysis results
    - Documents, chunks, tables
    - Entities and relations
    - Base case summaries and recommendations
    - Files in GridFS

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
        from ...domain.projects.file_storage import FileStorageService
        
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

        deleted_counts = {
            "scenarios": 0,
            "cost_estimates": 0,
            "scenario_analysis_results": 0,
            "files": 0,
            "documents": 0,
            "chunks": 0,
            "tables": 0,
            "entities": 0,
            "relations": 0,
            "base_case_summaries": 0,
            "base_case_recommendations": 0,
            "vectors": 0,
        }

        # Delete all scenarios for this project
        scenario_docs = list(_scenarios_collection.find(
            {"project_id": project_id},
            {"_id": 1}
        ))
        scenario_ids = [str(s["_id"]) for s in scenario_docs]
        
        scenarios_deleted = _scenarios_collection.delete_many(
            {"project_id": project_id}
        ).deleted_count
        deleted_counts["scenarios"] = scenarios_deleted

        # Delete cost estimates and scenario analysis results by scenario_id
        scenario_analysis_results_collection = db().scenario_analysis_results
        for scenario_id in scenario_ids:
            cost_estimates_deleted = _cost_estimates_collection.delete_many(
                {"scenario_id": scenario_id}
            ).deleted_count
            deleted_counts["cost_estimates"] += cost_estimates_deleted
            
            analysis_results_deleted = scenario_analysis_results_collection.delete_many(
                {"scenario_id": scenario_id}
            ).deleted_count
            deleted_counts["scenario_analysis_results"] += analysis_results_deleted
            
            # Delete scenario cost estimates
            scenario_cost_estimates_collection = db().scenario_cost_estimates
            scenario_cost_estimates_deleted = scenario_cost_estimates_collection.delete_many(
                {"scenario_id": scenario_id}
            ).deleted_count
            deleted_counts.setdefault("scenario_cost_estimates", 0)
            deleted_counts["scenario_cost_estimates"] += scenario_cost_estimates_deleted

        # Get all document IDs for this project BEFORE deleting documents
        # (needed for deleting related chunks and tables)
        project_doc_docs = list(_documents_collection.find(
            {"project_id": project_id},
            {"_id": 1}
        ))
        project_doc_ids = [str(doc["_id"]) for doc in project_doc_docs]
        project_doc_object_ids = [doc["_id"] for doc in project_doc_docs]

        documents_deleted = _documents_collection.delete_many(
            {"project_id": project_id}
        ).deleted_count
        deleted_counts["documents"] = documents_deleted

        # Delete chunks - check both root level and nested in properties, and by doc_id
        # Handle both string and ObjectId formats for doc_id
        chunks_deleted = _chunks_collection.delete_many(
            {
                "$or": [
                    {"properties.project_id": project_id},
                    {"project_id": project_id},
                    {"doc_id": {"$in": project_doc_ids}},  # String format
                    {"doc_id": {"$in": project_doc_object_ids}}  # ObjectId format
                ]
            }
        ).deleted_count
        deleted_counts["chunks"] = chunks_deleted

        # Delete tables - check doc_id and properties.project_id
        # Handle both string and ObjectId formats for doc_id
        tables_deleted = _tables_collection.delete_many(
            {
                "$or": [
                    {"doc_id": {"$in": project_doc_ids}},  # String format
                    {"doc_id": {"$in": project_doc_object_ids}},  # ObjectId format
                    {"properties.project_id": project_id}  # New format with properties
                ]
            }
        ).deleted_count
        deleted_counts["tables"] = tables_deleted

        # Delete entities - check both root level and nested in properties
        entities_deleted = _entities_collection.delete_many(
            {
                "$or": [
                    {"properties.project_id": project_id},
                    {"project_id": project_id}
                ]
            }
        ).deleted_count
        deleted_counts["entities"] = entities_deleted

        # Delete relations - check both root level and nested in properties
        relations_deleted = _relations_collection.delete_many(
            {
                "$or": [
                    {"properties.project_id": project_id},
                    {"project_id": project_id}
                ]
            }
        ).deleted_count
        deleted_counts["relations"] = relations_deleted

        # Delete base case summaries
        base_case_summaries_deleted = _base_case_summaries_collection.delete_many(
            {"project_id": project_id}
        ).deleted_count
        deleted_counts["base_case_summaries"] = base_case_summaries_deleted

        # Delete base case recommendations
        base_case_recommendations_deleted = _base_case_recommendations_collection.delete_many(
            {"project_id": project_id}
        ).deleted_count
        deleted_counts["base_case_recommendations"] = base_case_recommendations_deleted

        # Delete all files from GridFS
        file_storage = FileStorageService()
        files_deleted = 0
        project_files = file_storage.list_project_files(project_id)
        for file_meta in project_files:
            if file_storage.delete_file(file_meta["file_id"]):
                files_deleted += 1
        deleted_counts["files"] = files_deleted

        # Delete all vectors from Pinecone namespace
        try:
            from ...domain.parsing.storage.vector_store import delete_vectors_by_namespace
            vectors_deleted = delete_vectors_by_namespace(project_id)
            deleted_counts["vectors"] = vectors_deleted if vectors_deleted > 0 else 0
        except Exception as e:
            logger.warning(
                f"Failed to delete Pinecone vectors for project {project_id}: {e}. "
                f"Continuing with other cleanup operations."
            )
            deleted_counts["vectors"] = 0

        logger.info(
            f"Cleared project data for {project_id}: "
            f"{scenarios_deleted} scenarios, {deleted_counts['cost_estimates']} cost estimates, "
            f"{deleted_counts.get('scenario_cost_estimates', 0)} scenario cost estimates, "
            f"{deleted_counts['scenario_analysis_results']} scenario analysis results, "
            f"{files_deleted} files, {documents_deleted} documents, "
            f"{chunks_deleted} chunks, {tables_deleted} tables, "
            f"{entities_deleted} entities, {relations_deleted} relations, "
            f"{deleted_counts['base_case_summaries']} base case summaries, "
            f"{deleted_counts['base_case_recommendations']} base case recommendations, "
            f"{deleted_counts['vectors']} vectors"
        )

        return {
            "project_id": project_id,
            "deleted_counts": deleted_counts,
            "total_items": sum(deleted_counts.values()),
        }
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error clearing project data {project_id}: {e}", exc_info=True)
        raise


async def delete_all_user_data(user_id: str) -> Dict[str, Any]:
    """
    Delete all data associated with a user.

    This includes:
    - All projects (and their associated files)
    - All scenarios for those projects
    - All files in GridFS associated with the user

    Args:
        user_id: User identifier

    Returns:
        Dictionary with deletion counts
    """
    try:
        from ...domain.scenarios import repository as scenario_repo
        from ...domain.projects.file_storage import FileStorageService

        deleted_counts = {
            "projects": 0,
            "scenarios": 0,
            "files": 0,
            "documents": 0,
            "chunks": 0,
            "tables": 0,
            "cost_estimates": 0,
            "scenario_cost_estimates": 0,
            "scenario_analysis_results": 0,
            "entities": 0,
            "relations": 0,
            "base_case_summaries": 0,
            "base_case_recommendations": 0,
            "vectors": 0,
        }

        # Get all projects (for now, we delete all since projects don't have user_id)
        # TODO: Add user_id field to projects schema and filter by user_id
        all_projects = list(_projects_collection.find({}, {"_id": 1}))
        project_ids = [str(p["_id"]) for p in all_projects]

        # Delete all scenarios for these projects
        scenarios_collection = db().scenarios
        for project_id in project_ids:
            # Get all scenario IDs for this project before deleting scenarios
            scenario_docs = list(scenarios_collection.find(
                {"project_id": project_id},
                {"_id": 1}
            ))
            scenario_ids = [str(s["_id"]) for s in scenario_docs]
            
            scenarios_deleted = scenarios_collection.delete_many(
                {"project_id": project_id}
            ).deleted_count
            deleted_counts["scenarios"] += scenarios_deleted

            # Delete cost estimates and scenario analysis results by scenario_id (not project_id)
            scenario_analysis_results_collection = db().scenario_analysis_results
            for scenario_id in scenario_ids:
                cost_estimates_deleted = _cost_estimates_collection.delete_many(
                    {"scenario_id": scenario_id}
                ).deleted_count
                deleted_counts["cost_estimates"] += cost_estimates_deleted
                
                analysis_results_deleted = scenario_analysis_results_collection.delete_many(
                    {"scenario_id": scenario_id}
                ).deleted_count
                deleted_counts["scenario_analysis_results"] += analysis_results_deleted
                
                # Delete scenario cost estimates
                scenario_cost_estimates_collection = db().scenario_cost_estimates
                scenario_cost_estimates_deleted = scenario_cost_estimates_collection.delete_many(
                    {"scenario_id": scenario_id}
                ).deleted_count
                deleted_counts["scenario_cost_estimates"] += scenario_cost_estimates_deleted

            # Get all document IDs for this project BEFORE deleting documents
            # (needed for deleting related chunks and tables)
            project_doc_docs = list(_documents_collection.find(
                {"project_id": project_id},
                {"_id": 1}
            ))
            project_doc_ids = [str(doc["_id"]) for doc in project_doc_docs]
            project_doc_object_ids = [doc["_id"] for doc in project_doc_docs]

            documents_deleted = _documents_collection.delete_many(
                {"project_id": project_id}
            ).deleted_count
            deleted_counts["documents"] += documents_deleted

            # Delete chunks - check both root level and nested in properties, and by doc_id
            # Handle both string and ObjectId formats for doc_id
            chunks_deleted = _chunks_collection.delete_many(
                {
                    "$or": [
                        {"properties.project_id": project_id},
                        {"project_id": project_id},
                        {"doc_id": {"$in": project_doc_ids}},  # String format
                        {"doc_id": {"$in": project_doc_object_ids}}  # ObjectId format
                    ]
                }
            ).deleted_count
            deleted_counts["chunks"] += chunks_deleted

            # Delete tables - check doc_id and properties.project_id
            # Handle both string and ObjectId formats for doc_id
            tables_deleted = _tables_collection.delete_many(
                {
                    "$or": [
                        {"doc_id": {"$in": project_doc_ids}},  # String format
                        {"doc_id": {"$in": project_doc_object_ids}},  # ObjectId format
                        {"properties.project_id": project_id}  # New format with properties
                    ]
                }
            ).deleted_count
            deleted_counts["tables"] += tables_deleted

            # Delete entities - check both root level and nested in properties
            entities_deleted = _entities_collection.delete_many(
                {
                    "$or": [
                        {"properties.project_id": project_id},
                        {"project_id": project_id}
                    ]
                }
            ).deleted_count
            deleted_counts["entities"] += entities_deleted

            # Delete relations - check both root level and nested in properties
            relations_deleted = _relations_collection.delete_many(
                {
                    "$or": [
                        {"properties.project_id": project_id},
                        {"project_id": project_id}
                    ]
                }
            ).deleted_count
            deleted_counts["relations"] += relations_deleted

            base_case_summaries_deleted = _base_case_summaries_collection.delete_many(
                {"project_id": project_id}
            ).deleted_count
            deleted_counts["base_case_summaries"] += base_case_summaries_deleted

            base_case_recommendations_deleted = _base_case_recommendations_collection.delete_many(
                {"project_id": project_id}
            ).deleted_count
            deleted_counts["base_case_recommendations"] += base_case_recommendations_deleted

        # Delete all files from GridFS
        # Note: Files may have user_id in metadata, but we'll delete all files
        # associated with the projects
        file_storage = FileStorageService()
        files_deleted = 0
        for project_id in project_ids:
            # Get all files for this project
            project_files = file_storage.list_project_files(project_id)
            for file_meta in project_files:
                if file_storage.delete_file(file_meta["file_id"]):
                    files_deleted += 1
        deleted_counts["files"] = files_deleted

        # Clear all vectors from Pinecone index (all namespaces)
        try:
            from ...domain.parsing.storage.vector_store import _get_pinecone_index
            
            index = _get_pinecone_index()
            
            # Enumerate all namespaces
            logger.info("Enumerating Pinecone namespaces for deletion")
            stats = index.describe_index_stats()
            namespaces = list(stats.get("namespaces", {}).keys())
            
            # If no explicit namespaces exist, Pinecone implicitly uses "__default__"
            if not namespaces:
                namespaces = ["__default__"]
                logger.info("No explicit namespaces found, using default namespace")
            
            logger.info(f"Found {len(namespaces)} namespace(s) to clear: {namespaces}")
            
            # Delete all vectors from each namespace
            namespaces_cleared = []
            total_vectors_deleted = 0
            for ns in namespaces:
                try:
                    logger.info(f"Deleting all vectors from namespace: {ns}")
                    index.delete(delete_all=True, namespace=ns)
                    namespaces_cleared.append(ns)
                    
                    # Try to get vector count before deletion for logging
                    try:
                        ns_stats = stats.get("namespaces", {}).get(ns, {})
                        vector_count = ns_stats.get("vector_count", 0)
                        if vector_count > 0:
                            total_vectors_deleted += vector_count
                    except Exception:
                        # If we can't get the count, that's okay
                        pass
                    
                    logger.info(f"Successfully deleted all vectors from namespace: {ns}")
                except Exception as e:
                    logger.warning(
                        f"Failed to delete vectors from namespace {ns}: {e}. "
                        f"Continuing with other namespaces."
                    )
                    # Continue with other namespaces even if one fails
                    continue
            
            deleted_counts["vectors"] = total_vectors_deleted if total_vectors_deleted > 0 else len(namespaces_cleared)
            logger.info(
                f"Cleared {len(namespaces_cleared)}/{len(namespaces)} Pinecone namespaces "
                f"during user data deletion"
            )
        except Exception as e:
            logger.warning(
                f"Failed to clear Pinecone index during user data cleanup: {e}. "
                f"Continuing with other cleanup operations."
            )
            deleted_counts["vectors"] = 0

        # Delete all projects
        projects_deleted = _projects_collection.delete_many({}).deleted_count
        deleted_counts["projects"] = projects_deleted

        logger.info(
            f"Deleted all user data for user {user_id}: "
            f"{projects_deleted} projects, {deleted_counts['scenarios']} scenarios, "
            f"{deleted_counts['cost_estimates']} cost estimates, "
            f"{deleted_counts['scenario_cost_estimates']} scenario cost estimates, "
            f"{files_deleted} files, {deleted_counts['base_case_summaries']} base case summaries, "
            f"{deleted_counts['base_case_recommendations']} base case recommendations, "
            f"{deleted_counts['vectors']} vectors"
        )

        return {
            "user_id": user_id,
            "deleted_counts": deleted_counts,
            "total_items": sum(deleted_counts.values()),
        }
    except Exception as e:
        logger.error(f"Error deleting all user data for {user_id}: {e}", exc_info=True)
        raise
