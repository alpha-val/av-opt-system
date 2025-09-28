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


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    limit: int


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


@router_projects.get("/projects", response_model=ProjectListResponse)
async def get_projects(
    page: int = 1,
    limit: int = 10,
    status_filter: Optional[str] = None,
    project_type: Optional[str] = None,
    search: Optional[str] = None,
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

        # Convert to response model
        project_responses = [ProjectResponse(**project) for project in projects]

        return ProjectListResponse(
            projects=project_responses, total=total, page=page, limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get a specific project by ID (must belong to authenticated user)
    """
    try:
        project = db().projects.find_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],  # Ensure user owns project
                "active": True,
            },
            {"_id": 0},
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        return ProjectResponse(**project)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update a project (must belong to authenticated user)
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

        # Build update data (only include non-None fields)
        update_data = {}
        for field, value in project_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        # Add updated timestamp
        update_data["updated_at"] = datetime.datetime.utcnow()

        # Update project
        result = db().projects.update_one(
            {"project_id": project_id, "user_id": current_user["user_id"]},
            {"$set": update_data},
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to project",
            )

        # Get updated project
        updated_project = db().projects.find_one(
            {"project_id": project_id, "user_id": current_user["user_id"]}, {"_id": 0}
        )

        return ProjectResponse(**updated_project)

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


# Additional utility endpoints


@router_projects.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a specific project
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

        # Get project statistics (you can expand this based on your data model)
        stats = {
            "project_id": project_id,
            "project_name": project["name"],
            "created_at": project["created_at"],
            "days_active": (datetime.datetime.utcnow() - project["created_at"]).days,
            "last_updated": project["updated_at"],
            "status": project["status"],
            "project_type": project["project_type"],
            "tags_count": len(project.get("tags", [])),
            # Add more stats based on related collections
            # "documents_count": db().documents.count_documents({"project_id": project_id}),
            # "chunks_count": db().chunks.count_documents({"project_id": project_id}),
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Archive a project (set status to 'archived')
    """
    try:
        result = db().projects.update_one(
            {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "active": True,
            },
            {
                "$set": {
                    "status": "archived",
                    "archived_at": datetime.datetime.utcnow(),
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        return {
            "message": "Project archived successfully",
            "project_id": project_id,
            "archived_at": datetime.datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.post("/projects/{project_id}/restore")
async def restore_project(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Restore an archived or soft-deleted project
    """
    try:
        result = db().projects.update_one(
            {"project_id": project_id, "user_id": current_user["user_id"]},
            {
                "$set": {
                    "status": "active",
                    "active": True,
                    "updated_at": datetime.datetime.utcnow(),
                },
                "$unset": {"archived_at": "", "deleted_at": ""},
            },
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        return {
            "message": "Project restored successfully",
            "project_id": project_id,
            "restored_at": datetime.datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
