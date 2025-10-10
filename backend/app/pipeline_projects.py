from __future__ import annotations
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Body, Depends, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .bronze_store import db
from .pipeline_users import get_current_user  # Import auth dependency

# Create API router
router_projects = APIRouter()


# Pydantic models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Project description"
    )
    project_type: str = Field(
        default="mining", description="Type of project (mining, analysis, etc.)"
    )
    status: str = Field(default="active", description="Project status")
    tags: Optional[List[str]] = Field(default=[], description="Project tags")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional project metadata"
    )


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    project_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: Optional[str]
    project_type: str
    status: str
    tags: List[str]
    metadata: Dict[str, Any]
    user_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    active: bool

    # Add optional count fields
    counts: Optional[Dict[str, Any]] = None
    total_documents: Optional[int] = None
    base_case_documents: Optional[int] = None
    tabular_documents: Optional[int] = None
    scenarios: Optional[int] = None
    entities: Optional[int] = None
    relations: Optional[int] = None
    tables: Optional[int] = None
    chunks: Optional[int] = None
    has_data: Optional[bool] = None
    has_base_case: Optional[bool] = None
    has_scenarios: Optional[bool] = None
    processing_progress: Optional[Dict[str, int]] = None


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    limit: int
    total_pages: Optional[int] = None
    includes_counts: Optional[bool] = None


# CRUD Endpoints


@router_projects.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    project_data: ProjectCreate, current_user: dict = Depends(get_current_user)
):
    """
    Create a new project associated with the authenticated user
    """
    try:
        # Generate unique project ID
        project_id = str(uuid.uuid4())

        # Create project document
        project_document = {
            "project_id": project_id,
            "name": project_data.name,
            "description": project_data.description,
            "project_type": project_data.project_type,
            "status": project_data.status,
            "tags": project_data.tags or [],
            "metadata": project_data.metadata or {},
            "user_id": current_user["user_id"],  # Associate with authenticated user
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "active": True,
        }

        # Insert project into database
        result = db().projects.insert_one(project_document)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        # Return created project
        return ProjectResponse(**project_document)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )

@router_projects.get("/projects/{project_id}/counts")
async def get_project_data_counts(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive data counts for a project
    """
    try:
        # Verify project ownership
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )

        # Get all counts using the helper function
        counts = await get_project_counts(project_id, current_user["user_id"])

        # Add project metadata
        counts["project_name"] = project["name"]
        counts["project_status"] = project["status"]
        counts["project_type"] = project["project_type"]
        counts["created_at"] = project["created_at"]
        counts["updated_at"] = project["updated_at"]

        return counts

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a specific project (enhanced version)
    """
    try:
        # Verify project ownership
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Get comprehensive counts
        counts = await get_project_counts(project_id, current_user["user_id"])

        # Build enhanced stats
        stats = {
            "project_id": project_id,
            "project_name": project["name"],
            "created_at": project["created_at"],
            "days_active": (datetime.datetime.utcnow() - project["created_at"]).days,
            "last_updated": project["updated_at"],
            "status": project["status"],
            "project_type": project["project_type"],
            "tags_count": len(project.get("tags", [])),
            # Data counts from helper function
            **counts,
            # Additional calculated stats
            "data_completeness": {
                "has_documents": counts["total_documents"] > 0,
                "has_base_case": counts["base_case_documents"] > 0,
                "has_scenarios": counts["tabular_documents"] > 0,
                "has_entities": counts["entities"] > 0,
                "has_relations": counts["relations"] > 0,
                "has_structured_data": counts["tables"] > 0,
            },
            "processing_summary": {
                "documents_processed": counts["total_documents"],
                "tables_extracted": counts["tables"],
                "text_chunks": counts["chunks"],
                "entities_identified": counts["entities"],
                "relationships_mapped": counts["relations"],
            },
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.get("/projects/get-docs/{project_id}/documents/{doc_id}")
async def get_project_document(
    project_id: str, doc_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get a specific document by doc_id within a project
    """
    print(f"[DEBUG] Fetching document {doc_id} in project {project_id}")
    try:
        # Verify project ownership
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )

        # Get the specific document
        document = db().documents.find_one(
            {
                "properties.doc_id": doc_id,
                "properties.project_id": project_id,
                "properties.user_id": current_user["user_id"],
            },
            {"_id": 0},
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this project",
            )

        # Get related tables
        tables = list(db().tables.find({"doc_id": doc_id}, {"_id": 0}).sort("page", 1))

        # Get related chunks
        chunks = list(
            db().chunks.find({"doc_id": doc_id}, {"_id": 0}).limit(100)
        )  # Limit chunks to avoid too much data

        # Add related data to document
        document["tables"] = tables
        document["chunks"] = chunks
        document["tables_count"] = len(tables)
        document["chunks_count"] = len(chunks)

        return {"project_id": project_id, "document": document}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.delete("/projects/{project_id}/documents/{doc_id}")
async def delete_project_document(
    project_id: str,
    doc_id: str,
    hard_delete: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a document and all its related data (tables, chunks)
    """
    try:
        # Verify project ownership
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )

        # Check if document exists
        document = db().documents.find_one(
            {
                "doc_id": doc_id,
                "project_id": project_id,
                "user_id": current_user["user_id"],
            }
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this project",
            )

        if hard_delete:
            print(f"[DEBUG] Performing hard delete for doc_id: {doc_id}")
            # Hard delete - remove document and all related data
            db().documents.delete_one({"doc_id": doc_id})
            tables_deleted = db().tables.delete_many({"properties.doc_id": doc_id})
            chunks_deleted = db().chunks.delete_many({"properties.doc_id": doc_id})
            entities_deleted = db().entities.delete_many({"properties.doc_id": doc_id})
            relations_deleted = db().relations.delete_many(
                {"properties.doc_id": doc_id}
            )

            message = "Document and all related data permanently deleted"
        else:
            # Soft delete - mark as inactive
            db().documents.update_one(
                {"doc_id": doc_id},
                {
                    "$set": {
                        "active": False,
                        "deleted_at": datetime.datetime.utcnow(),
                        "updated_at": datetime.datetime.utcnow(),
                    }
                },
            )
            message = "Document marked as deleted (soft delete)"

        return {
            "message": message,
            "project_id": project_id,
            "doc_id": doc_id,
            "deleted_at": datetime.datetime.utcnow().isoformat(),
            **(
                {
                    "tables_deleted": tables_deleted.deleted_count,
                    "chunks_deleted": chunks_deleted.deleted_count,
                    "entities_deleted": entities_deleted.deleted_count,
                    "relations_deleted": relations_deleted.deleted_count,
                }
                if hard_delete
                else {}
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    hard_delete: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a project (soft delete by default, hard delete if specified)
    Must belong to authenticated user
    """
    try:
        # Check if project exists and belongs to user
        existing_project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        if hard_delete:
            # Hard delete - permanently remove from database
            result = db().projects.delete_one(
                {"project_id": project_id, "user_id": current_user["user_id"]}
            )
            message = "Project permanently deleted"
        else:
            # Soft delete - mark as inactive
            result = db().projects.update_one(
                {"project_id": project_id, "user_id": current_user["user_id"]},
                {
                    "$set": {
                        "active": False,
                        "deleted_at": datetime.datetime.utcnow(),
                        "updated_at": datetime.datetime.utcnow(),
                    }
                },
            )
            message = "Project deleted (soft delete)"

        if (hard_delete and result.deleted_count == 0) or (
            not hard_delete and result.modified_count == 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete project",
            )

        return {
            "message": message,
            "project_id": project_id,
            "deleted_at": datetime.datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.delete("/projects/{project_id}/clear-all-data")
def clear_all_project_data(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Clear all data for a project including:
    - Documents
    - Tables
    - Chunks
    - Entities (silver_nodes)
    - Relations (silver_edges)
    - Scenarios

    This is a hard delete operation that cannot be undone.
    The project itself is NOT deleted, only its associated data.
    """
    try:
        # Verify project ownership
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            }
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )

        # Build base filter
        base_filter = {
            "properties.project_id": project_id,
            "properties.user_id": current_user["user_id"],
        }

        # Get document IDs before deleting for additional cleanup
        documents = list(db().documents.find(base_filter, {"doc_id": 1, "_id": 0}))
        doc_ids = [doc["doc_id"] for doc in documents]

        # Delete all data
        documents_deleted = db().documents.delete_many(base_filter).deleted_count
        entities_deleted = db().entities.delete_many(base_filter).deleted_count
        relations_deleted = db().relations.delete_many(base_filter).deleted_count
        scenarios_deleted = db().scenarios.delete_many(base_filter).deleted_count

        # Delete by doc_id (for tables and chunks that may not have project_id)
        tables_deleted = 0
        chunks_deleted = 0
        if doc_ids:
            tables_deleted = (
                db()
                .tables.delete_many({"properties.doc_id": {"$in": doc_ids}})
                .deleted_count
            )
            chunks_deleted = (
                db()
                .chunks.delete_many({"properties.doc_id": {"$in": doc_ids}})
                .deleted_count
            )

        # Update project's updated_at timestamp
        db().projects.update_one(
            {"project_id": project_id, "user_id": current_user["user_id"]},
            {"$set": {"updated_at": datetime.datetime.utcnow()}},
        )

        print(
            f"[CLEAR_ALL_DATA] Cleared all data for project {project_id}: "
            f"{documents_deleted} documents, {entities_deleted} entities, "
            f"{relations_deleted} relations, {tables_deleted} tables, "
            f"{chunks_deleted} chunks, {scenarios_deleted} scenarios"
        )

        return {
            "message": "All project data cleared successfully",
            "project_id": project_id,
            "project_name": project["name"],
            "deleted_counts": {
                "documents": documents_deleted,
                "entities": entities_deleted,
                "relations": relations_deleted,
                "tables": tables_deleted,
                "chunks": chunks_deleted,
                "scenarios": scenarios_deleted,
                "total_items": (
                    documents_deleted
                    + entities_deleted
                    + relations_deleted
                    + tables_deleted
                    + chunks_deleted
                    + scenarios_deleted
                ),
            },
            "doc_ids_cleared": doc_ids,
            "cleared_at": datetime.datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CLEAR_ALL_DATA] Error clearing project data: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Additional utility endpoints


async def get_project_counts(project_id: str, user_id: str) -> Dict[str, int]:
    """
    Helper function to get comprehensive counts for a project

    Args:
        project_id: The project ID to get counts for
        user_id: The user ID for access control

    Returns:
        Dictionary with counts for all project-related data
    """
    try:
        # Base filter for project and user
        base_filter = {"project_id": project_id, "user_id": user_id}

        # Get document counts
        documents_filter = {**base_filter, "active": True}
        total_documents = db().documents.count_documents(documents_filter)

        # Count base case documents
        base_case_filter = {**documents_filter, "artifact_type": "base_case"}
        base_case_documents = db().documents.count_documents(base_case_filter)

        # Count scenario documents
        scenario_filter = {**documents_filter, "artifact_type": "scenario"}
        tabular_documents = db().documents.count_documents(scenario_filter)

        # Get entities count
        entities_count = db().entities.count_documents(base_filter)

        # Get relations count
        relations_count = db().relations.count_documents(base_filter)

        # Get tables count
        tables_count = db().tables.count_documents(base_filter)

        # Get scenario count
        scenario_count = db().scenarios.count_documents(base_filter)

        # Get chunks count
        chunks_count = db().chunks.count_documents(base_filter)

        # Get document IDs for this project to count related data
        project_docs = db().documents.find(documents_filter, {"doc_id": 1, "_id": 0})
        doc_ids = [doc["doc_id"] for doc in project_docs]

        # Count tables by doc_id (alternative counting method)
        tables_by_doc = 0
        chunks_by_doc = 0

        if doc_ids:
            tables_by_doc = db().tables.count_documents({"doc_id": {"$in": doc_ids}})
            chunks_by_doc = db().chunks.count_documents({"doc_id": {"$in": doc_ids}})

        return {
            "project_id": project_id,
            "total_documents": total_documents,
            "base_case_documents": base_case_documents,
            "tabular_documents": tabular_documents,
            "scenarios": scenario_count,
            "entities": entities_count,
            "relations": relations_count,
            "tables": max(tables_count, tables_by_doc),  # Use higher count
            "chunks": max(chunks_count, chunks_by_doc),  # Use higher count
            "document_ids": doc_ids,
            "counts_by_project_filter": {
                "tables": tables_count,
                "chunks": chunks_count,
            },
            "counts_by_doc_ids": {
                "tables": tables_by_doc,
                "chunks": chunks_by_doc,
            },
        }

    except Exception as e:
        print(f"Error getting project counts: {e}")
        return {
            "project_id": project_id,
            "error": str(e),
            "total_documents": 0,
            "base_case_documents": 0,
            "tabular_documents": 0,
            "entities": 0,
            "relations": 0,
            "tables": 0,
            "chunks": 0,
        }


@router_projects.get("/projects", response_model=ProjectListResponse)
async def get_projects(
    page: int = 1,
    limit: int = 10,
    status_filter: Optional[str] = None,
    project_type: Optional[str] = None,
    search: Optional[str] = None,
    include_counts: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """
    Get projects for the authenticated user with pagination and filtering
    """
    try:
        # Build query filter
        query_filter = {
            "user_id": current_user["user_id"],  # Only user's projects
            "active": True,
        }

        # Add optional filters
        if status_filter:
            query_filter["status"] = status_filter

        if project_type:
            query_filter["project_type"] = project_type

        if search:
            query_filter["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search]}},
            ]

        # Calculate skip for pagination
        skip = (page - 1) * limit

        # Get total count
        total = db().projects.count_documents(query_filter)

        # Get projects with pagination
        projects_cursor = (
            db()
            .projects.find(query_filter, {"_id": 0})  # Exclude MongoDB _id field
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        projects = list(projects_cursor)

        # Process projects with or without counts
        processed_projects = []

        for project in projects:
            if include_counts:
                # Get counts for this project
                counts = await get_project_counts(
                    project["project_id"], current_user["user_id"]
                )
                print(f"[DEBUG] Counts for project {project['project_id']}: {counts}")

                # Add counts to the project data
                project_with_counts = {
                    **project,
                    "counts": counts,
                    "total_documents": counts["total_documents"],
                    "base_case_documents": counts["base_case_documents"],
                    "tabular_documents": counts["tabular_documents"],
                    "scenarios": counts["scenarios"],
                    "entities": counts["entities"],
                    "relations": counts["relations"],
                    "tables": counts["tables"],
                    "chunks": counts["chunks"],
                    "has_data": counts["total_documents"] > 0,
                    "has_base_case": counts["base_case_documents"] > 0,
                    "has_scenarios": counts["tabular_documents"] > 0,
                    "processing_progress": {
                        "documents_uploaded": counts["total_documents"],
                        "tables_extracted": counts["tables"],
                        "entities_identified": counts["entities"],
                        "relations_mapped": counts["relations"],
                    },
                }
                processed_projects.append(project_with_counts)
            else:
                processed_projects.append(project)

        # Convert to response models
        project_responses = [
            ProjectResponse(**project) for project in processed_projects
        ]

        # Calculate total pages
        total_pages = (total + limit - 1) // limit

        # Return consistent response structure
        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            includes_counts=include_counts,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
