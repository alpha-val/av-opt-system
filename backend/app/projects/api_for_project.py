from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, List, Any
from datetime import datetime

from ..bronze_store import db
from ..pipeline_users import get_current_user
from .schemas_for_project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.vector_db.vector_operations import pc
from app.vector_db.vector_operations import index_name

router_for_projects = APIRouter()

# ============================================================================
# ENDPOINTS
# ============================================================================


# Create a new project
@router_for_projects.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
def create_project(
    project_data: ProjectCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        # Debug: print current_user to see what keys exist
        print(f"[DEBUG] current_user: {current_user}")
        print(f"[DEBUG] current_user type: {type(current_user)}")

        project_dict = project_data.model_dump()

        # Try multiple possible keys for user_id
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            print(
                f"[ERROR] Could not extract user_id from current_user: {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not extract user_id from authentication token. Available keys: {list(current_user.keys()) if isinstance(current_user, dict) else 'not a dict'}",
            )

        print(f"[DEBUG] Extracted user_id: {user_id}")

        # Set all required fields
        project_dict["user_id"] = user_id
        project_dict["created_at"] = datetime.now()
        project_dict["updated_at"] = datetime.now()

        # Generate ID
        import uuid

        project_dict["id"] = str(uuid.uuid4())

        # Ensure tags and metadata have defaults
        if "status" not in project_dict or project_dict["status"] is None:
            project_dict["status"] = "active"
        if "tags" not in project_dict or project_dict["tags"] is None:
            project_dict["tags"] = []
        if "metadata" not in project_dict or project_dict["metadata"] is None:
            project_dict["metadata"] = {}

        print(f"[DEBUG] project_dict before insert: {project_dict}")

        # Insert into database
        result = db().projects.insert_one(project_dict)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        print(f"[DEBUG] Successfully inserted project with id: {project_dict['id']}")
        return ProjectResponse(**project_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Create project failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# List projects with optional status filter
@router_for_projects.get(
    "/projects/all",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
)
def list_projects(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
):
    """List projects for the current user, with optional status filter"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        query = {"user_id": user_id}
        if status:
            query["status"] = status

        projects_cursor = db().projects.find(query, {"_id": 0}).skip(skip).limit(limit)
        projects = list(projects_cursor)

        return [ProjectResponse(**proj) for proj in projects]

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] List projects failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Get a single project by ID
@router_for_projects.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a project by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        project_data = db().projects.find_one(
            {"id": project_id, "user_id": user_id}, {"_id": 0}
        )
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        return ProjectResponse(**project_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Get project failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Delete a project
@router_for_projects.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_200_OK,  # ✅ Changed from 204 to 200
)
def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project by ID and all its related data"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # First, verify the project exists and belongs to the user
        project = db().projects.find_one(
            {"id": project_id, "user_id": user_id}, {"_id": 0, "name": 1}
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Get all document IDs for this project
        docs_cursor = db().documents.find(
            {"project_id": project_id, "user_id": user_id}, {"doc_id": 1, "_id": 0}
        )
        docs = list(docs_cursor)
        doc_ids = [doc.get("doc_id") for doc in docs if doc.get("doc_id")]

        print(f"[DEBUG] Deleting project {project_id} with {len(doc_ids)} documents")

        # Delete all project-related data from all collections

        documents_deleted = (
            db()
            .documents.delete_many({"project_id": project_id, "user_id": user_id})
            .deleted_count
        )

        base_filter = {
            "properties.project_id": project_id,
            "properties.user_id": user_id,
        }
        chunks_deleted = db().chunks.delete_many(base_filter).deleted_count

        # Use correct collection names
        entities_deleted = db().entities.delete_many(base_filter).deleted_count
        relations_deleted = db().relations.delete_many(base_filter).deleted_count

        scenarios_deleted = db().scenarios.delete_many(base_filter).deleted_count

        cost_estimates_deleted = (
            db().cost_estimates.delete_many(base_filter).deleted_count
        )

        # Delete tables by doc_id
        tables_deleted = 0
        if doc_ids:
            tables_deleted = (
                db().tables.delete_many({"doc_id": {"$in": doc_ids}}).deleted_count
            )

        # Clear vectors from Pinecone index for the specific project namespace
        try:
            # Initialize the Pinecone index
            pinecone_index = pc.Index(index_name)

            # Check if the namespace exists
            index_stats = pinecone_index.describe_index_stats()
            namespaces = index_stats.get("namespaces", {}).keys()

            if project_id not in namespaces:
                print(
                    f"[WARN] Namespace '{project_id}' does not exist in Pinecone. Skipping deletion."
                )
            else:
                # Delete all vectors for the namespace corresponding to the project_id
                pinecone_index.delete(namespace=project_id)
                print(
                    f"[INFO] Successfully deleted vectors from Pinecone for namespace '{project_id}'"
                )

        except Exception as e:
            print(
                f"[ERROR] Failed to delete vectors from Pinecone for namespace '{project_id}' - {e}"
            )

        # Finally, delete the project itself
        result = db().projects.delete_one({"id": project_id, "user_id": user_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete project {project_id}",
            )

        total_items_deleted = (
            documents_deleted
            + chunks_deleted
            + entities_deleted
            + relations_deleted
            + tables_deleted
            + scenarios_deleted
            + cost_estimates_deleted
            + 1  # The project itself
        )

        print(
            f"[DEBUG] Deleted project {project_id}: "
            f"{documents_deleted} documents, "
            f"{chunks_deleted} chunks, "
            f"{entities_deleted} entities, "
            f"{relations_deleted} relations, "
            f"{tables_deleted} tables, "
            f"{scenarios_deleted} scenarios"
        )

        return {
            "message": f"Project '{project.get('name', project_id)}' and all associated data deleted successfully",
            "project_id": project_id,
            "project_name": project.get("name"),
            "deleted_counts": {
                "documents": documents_deleted,
                "chunks": chunks_deleted,
                "entities": entities_deleted,
                "relations": relations_deleted,
                "tables": tables_deleted,
                "scenarios": scenarios_deleted,
                "total_items": total_items_deleted,
            },
            "doc_ids_deleted": doc_ids,
            "deleted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete project failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Delete a project's data
@router_for_projects.delete(
    "/projects/{project_id}/data",
    status_code=status.HTTP_200_OK,  # ✅ Changed from 204 to 200
)
def delete_project_data(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete all data associated with a project by ID, but not the project itself"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # First verify the project exists and belongs to the user
        project = db().projects.find_one(
            {"id": project_id, "user_id": user_id}, {"_id": 0, "name": 1}
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Get all document IDs for this project
        docs_cursor = db().documents.find(
            {"project_id": project_id, "user_id": user_id}, {"doc_id": 1, "_id": 0}
        )
        docs = list(docs_cursor)
        doc_ids = [doc.get("doc_id") for doc in docs if doc.get("doc_id")]

        print(
            f"[DEBUG] Deleting data for project {project_id} with {len(doc_ids)} documents"
        )

        # Delete all project-related data from all collections

        documents_deleted = (
            db()
            .documents.delete_many({"project_id": project_id, "user_id": user_id})
            .deleted_count
        )

        base_filter = {
            "properties.project_id": project_id,
            "properties.user_id": user_id,
        }
        chunks_deleted = db().chunks.delete_many(base_filter).deleted_count

        # Use correct collection names
        entities_deleted = db().entities.delete_many(base_filter).deleted_count
        relations_deleted = db().relations.delete_many(base_filter).deleted_count

        scenarios_deleted = db().scenarios.delete_many(base_filter).deleted_count
        cost_estimates_deleted = (
            db().cost_estimates.delete_many(base_filter).deleted_count
        )

        # Clear vectors from Pinecone index for the specific project namespace
        try:
            # Initialize the Pinecone index
            pinecone_index = pc.Index(index_name)

            # Check if the namespace exists
            index_stats = pinecone_index.describe_index_stats()
            namespaces = index_stats.get("namespaces", {}).keys()

            if project_id not in namespaces:
                print(
                    f"[WARN] Namespace '{project_id}' does not exist in Pinecone. Skipping deletion."
                )
            else:
                # Delete all vectors for the namespace corresponding to the project_id
                pinecone_index.delete(delete_all=True, namespace=project_id)
                print(
                    f"[INFO] Successfully deleted vectors from Pinecone for namespace '{project_id}'"
                )

        except Exception as e:
            print(
                f"[ERROR] Failed to delete vectors from Pinecone for namespace '{project_id}' - {e}"
            )

        # Delete tables by doc_id (if tables don't have project_id)
        tables_deleted = 0
        if doc_ids:
            tables_deleted = (
                db().tables.delete_many({"doc_id": {"$in": doc_ids}}).deleted_count
            )

        total_items_deleted = (
            documents_deleted
            + chunks_deleted
            + entities_deleted
            + relations_deleted
            + tables_deleted
            + scenarios_deleted
            + cost_estimates_deleted
        )

        print(
            f"[DEBUG] Deleted data for project {project_id}: "
            f"{documents_deleted} documents, "
            f"{chunks_deleted} chunks, "
            f"{entities_deleted} entities, "
            f"{relations_deleted} relations, "
            f"{tables_deleted} tables, "
            f"{scenarios_deleted} scenarios, "
            f"{cost_estimates_deleted} cost estimates"
        )

        return {
            "message": f"Successfully deleted all data for project '{project.get('name', project_id)}'",
            "project_id": project_id,
            "project_name": project.get("name"),
            "deleted_counts": {
                "documents": documents_deleted,
                "chunks": chunks_deleted,
                "entities": entities_deleted,
                "relations": relations_deleted,
                "tables": tables_deleted,
                "scenarios": scenarios_deleted,
                "total_items": total_items_deleted,
            },
            "doc_ids_deleted": doc_ids,
            "deleted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete project data failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Delete all projects for the current user - USE WITH CAUTION
@router_for_projects.delete("/projects/clear_all", status_code=status.HTTP_200_OK)
def clear_all_projects(current_user: dict = Depends(get_current_user)):
    """Delete all projects and all related data for the current user - USE WITH CAUTION"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Get all project IDs for this user first
        user_projects_cursor = db().projects.find(
            {"user_id": user_id}, {"id": 1, "_id": 0}
        )
        user_projects = list(user_projects_cursor)
        project_ids = [p["id"] for p in user_projects]

        print(f"[DEBUG] Found {len(project_ids)} projects to delete for user {user_id}")

        # Delete all project-related data
        base_filter = {"user_id": user_id}

        # Delete data by user_id and project_id
        documents_deleted = db().documents.delete_many(base_filter).deleted_count
        chunks_deleted = db().chunks.delete_many(base_filter).deleted_count
        entities_deleted = db().entities.delete_many(base_filter).deleted_count
        relations_deleted = db().relations.delete_many(base_filter).deleted_count
        scenarios_deleted = db().scenarios.delete_many(base_filter).deleted_count
        cost_estimates_deleted = (
            db().cost_estimates.delete_many(base_filter).deleted_count
        )

        # Delete tables by project_id (if tables have project_id field)
        tables_deleted = 0
        if project_ids:
            tables_deleted = (
                db()
                .tables.delete_many({"project_id": {"$in": project_ids}})
                .deleted_count
            )

        # Delete all projects
        projects_deleted = db().projects.delete_many({"user_id": user_id}).deleted_count

        total_items_deleted = (
            documents_deleted
            + chunks_deleted
            + entities_deleted
            + relations_deleted
            + tables_deleted
            + scenarios_deleted
            + projects_deleted
            + cost_estimates_deleted
        )

        print(
            f"[DEBUG] Deleted all data for user {user_id}: "
            f"{projects_deleted} projects, "
            f"{documents_deleted} documents, "
            f"{chunks_deleted} chunks, "
            f"{entities_deleted} entities, "
            f"{relations_deleted} relations, "
            f"{tables_deleted} tables, "
            f"{scenarios_deleted} scenarios"
        )

        return {
            "message": f"Successfully deleted all projects and related data for user",
            "user_id": user_id,
            "deleted_counts": {
                "projects": projects_deleted,
                "documents": documents_deleted,
                "chunks": chunks_deleted,
                "entities": entities_deleted,
                "relations": relations_deleted,
                "tables": tables_deleted,
                "scenarios": scenarios_deleted,
                "total_items": total_items_deleted,
            },
            "project_ids_deleted": project_ids,
            "deleted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Clear all projects failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Fetch entities and relations for a document and add metadata
@router_for_projects.get(
    "/projects/{project_id}/entities_relations", status_code=status.HTTP_200_OK
)
def get_entities_relations_for_project(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """Fetch entities and relations for a document and add project metadata"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Fetch entities (nodes) for the document
        nodes_cursor = db().entities.find(
            {
                "properties.project_id": project_id,
                "properties.user_id": user_id,
            },
        )
        nodes = list(nodes_cursor)

        # Fetch relations (edges) for the document
        edges_cursor = db().relations.find(
            {
                "properties.project_id": project_id,
                "properties.user_id": user_id,
            },
        )
        edges = list(edges_cursor)

        # Add metadata to each node and edge
        for n in nodes:
            if "properties" not in n or not isinstance(n["properties"], dict):
                n["properties"] = {}

            n["id"] = (
                n.get("id")  # Check root level id first
                or n.get("properties", {}).get("id")  # Check properties.id
                or str(n.get("_id"))  # Fall back to MongoDB _id
            )

            n["properties"]["project_id"] = project_id
            n["properties"]["user_id"] = user_id

            if "_id" in n:
                del n["_id"]  # Remove MongoDB _id to avoid confusion

        for e in edges:
            if "properties" not in e or not isinstance(e["properties"], dict):
                e["properties"] = {}

            e["id"] = (
                e.get("id")  # Check root level id first
                or e.get("properties", {}).get("id")  # Check properties.id
                or str(e.get("_id"))  # Fall back to MongoDB _id
            )

            e["properties"]["project_id"] = project_id
            e["properties"]["user_id"] = user_id

            if "_id" in e:
                del e["_id"]  # Remove MongoDB _id to avoid confusion

        # Add summary statistics
        summary = {
            "entity_count": len(nodes),
            "relation_count": len(edges),
            "project_id": project_id,
        }

        return {
            "project_id": project_id,
            "entities": nodes,
            "relations": edges,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Fetch entities and relations failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
