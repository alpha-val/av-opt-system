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


@router_projects.get("/projects/{project_id}/documents/debug")
async def debug_project_documents(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """Debug endpoint to see what's actually in the documents collection"""
    try:
        print(f"Debug - Looking for documents with:")
        print(f"  project_id: {project_id}")
        print(f"  user_id: {current_user['user_id']}")

        # Check all collections that might contain documents
        collections_info = {}

        # Check documents collection
        all_docs = list(db().documents.find({}, {"_id": 0}).limit(10))
        user_project_docs = list(
            db().documents.find(
                {"project_id": project_id, "user_id": current_user["user_id"]},
                {"_id": 0},
            )
        )
        project_only_docs = list(
            db().documents.find({"project_id": project_id}, {"_id": 0})
        )

        collections_info["documents"] = {
            "total_count": db().documents.count_documents({}),
            "sample_docs": all_docs,
            "user_project_docs": user_project_docs,
            "project_only_docs": project_only_docs,
        }

        # Check if documents might be in a different collection
        # Common alternatives: files, uploads, doc_metadata, etc.
        potential_collections = ["files", "uploads", "doc_metadata", "file_uploads"]
        for coll_name in potential_collections:
            try:
                collection = getattr(db(), coll_name)
                count = collection.count_documents({})
                if count > 0:
                    sample = list(collection.find({}, {"_id": 0}).limit(3))
                    collections_info[coll_name] = {"count": count, "sample": sample}
            except:
                pass

        # Also check what collections exist in the database
        try:
            db_instance = db()
            all_collections = db_instance.list_collection_names()
        except:
            all_collections = ["Unable to list collections"]

        return {
            "debug_info": {
                "project_id": project_id,
                "user_id": current_user["user_id"],
                "all_collections": all_collections,
                "collections_data": collections_info,
            }
        }

    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}


# Comprehensive debug function
def debug_document_query(project_id):
    try:
        print(f"\n=== DEBUGGING DOCUMENT QUERY ===")
        print(f"Looking for project_id: {repr(project_id)} (type: {type(project_id)})")

        # Test database connection
        db_instance = db()
        print(f"Database: {db_instance.name}")

        # Test collections
        collections = db_instance.list_collection_names()
        print(f"Collections: {collections}")

        if "documents" not in collections:
            print("ERROR: 'documents' collection does not exist!")
            return None

        # Count total documents
        total_count = db().documents.count_documents({})
        print(f"Total documents: {total_count}")

        if total_count == 0:
            print("ERROR: No documents in collection!")
            return None

        # Get sample document to check structure
        sample = db().documents.find_one({})
        print(f"Sample document keys: {list(sample.keys()) if sample else 'None'}")

        # Try exact query
        exact_result = db().documents.find_one({"project_id": project_id})
        print(f"Exact query result: {exact_result}")

        # Try case-insensitive query
        regex_result = db().documents.find_one(
            {"project_id": {"$regex": f"^{project_id}$", "$options": "i"}}
        )
        print(f"Case-insensitive result: {regex_result}")

        # Count matches
        match_count = db().documents.count_documents({"project_id": project_id})
        print(f"Matching documents: {match_count}")

        # List all unique project_ids to compare
        unique_projects = db().documents.distinct("project_id")
        print(
            f"All project_ids in collection: {unique_projects[:5]}..."
        )  # Show first 5

        print(f"=== END DEBUG ===\n")
        return exact_result

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return None


@router_projects.get("/projects/{project_id}/documents")
async def get_project_documents(
    project_id: str,
    document_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """
    Get all documents related to a specific project
    Supports filtering by document type and status with pagination
    """
    try:
        # First verify the project exists and belongs to the user
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

        # Build query filter for documents
        query_filter = {
            "project_id": project_id,
            "user_id": current_user["user_id"],
            "active": True,  # Only get active documents
        }

        # Add optional filters
        if document_type:
            query_filter["document_type"] = document_type

        if status_filter:
            query_filter["processing_status"] = status_filter

        # Calculate pagination
        skip = (page - 1) * limit

        # Get total count
        total_documents = db().documents.count_documents(query_filter)

        # Get documents with pagination
        documents_cursor = (
            db()
            .documents.find(query_filter, {"_id": 0})
            .sort("created_at", -1)  # Most recent first
            .skip(skip)
            .limit(limit)
        )

        documents = list(documents_cursor)

        print(f"[DEBUG] Retrieved {len(documents)} documents for project {project_id}")

        # Add related data counts for each document
        for doc in documents:
            doc_id = doc.get("doc_id")
            if doc_id:
                # Count related tables and chunks
                doc["tables_count"] = db().tables.count_documents({"doc_id": doc_id})
                doc["chunks_count"] = db().chunks.count_documents({"doc_id": doc_id})

        # Simplified response - just return documents array
        return {
            "project_id": project_id,
            "documents": documents,
            "total_documents": total_documents,
            "page": page,
            "limit": limit,
            "total_pages": (total_documents + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router_projects.get("/projects/{project_id}/documents/{doc_id}")
async def get_project_document(
    project_id: str, doc_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get a specific document by doc_id within a project
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

        # Get the specific document
        document = db().documents.find_one(
            {
                "doc_id": doc_id,
                "project_id": project_id,
                "user_id": current_user["user_id"],
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
            # Hard delete - remove document and all related data
            db().documents.delete_one({"doc_id": doc_id})
            tables_deleted = db().tables.delete_many({"doc_id": doc_id})
            chunks_deleted = db().chunks.delete_many({"doc_id": doc_id})

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
