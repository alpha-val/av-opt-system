from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid

from ..bronze_store import db
from ..pipeline_users import get_current_user
from .schemas_for_document import DocumentCreate, DocumentUpdate, DocumentResponse

# ETL
from ..etl_base.etl_for_base_case import etl_base_case
from ..etl_tables.etl_for_tabular_data import map_tables_to_entities

router_for_documents = APIRouter()

# ============================================================================
# ENDPOINTS
# ============================================================================


# Create a new document (handles file uploads like etl_base_case)
@router_for_documents.post(
    "/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
def create_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    artifact_type: str = Form("base_case"),
    description: Optional[str] = Form(None),
    pages: Optional[str] = Form(None),
    type: Optional[str] = Form("report"),
    tags: Optional[str] = Form(None),
    title: Optional[str] = Form("File upload"),
    current_user: dict = Depends(get_current_user),
):
    """Create a new document with file upload"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        # Validate file type
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )

        # Generate unique document ID
        doc_id = str(uuid.uuid4())

        etl_result: Dict[str, Any] = {}
        if artifact_type == "base_case":
            etl_result = etl_base_case(
                file=file,
                pages=pages,
                project_id=project_id,
                user_id=user_id,
                artifact_type=artifact_type,
                doc_id=doc_id,
            )
        elif artifact_type == "tabular_data":
            etl_result = map_tables_to_entities(
                file=file,
                pages=pages,
                project_id=project_id,
                user_id=user_id,
                artifact_type=artifact_type,
                doc_id=doc_id,
            )


        # Parse tags if provided
        tags_list = []
        if tags:
            try:
                import json

                tags_list = json.loads(tags)
            except:
                # If not JSON, treat as comma-separated
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Create document metadata
        document_dict = {
            "id": doc_id,
            "upload_source": "web_interface",
            "artifact_type": artifact_type,
            "created_at": datetime.now(),
            "description": description
            or f"Uploaded document: {etl_result.get('filename')}",
            "file_size": etl_result.get("file_size"),
            "file_type": file.content_type,
            "file_name": etl_result.get("filename"),
            "file_sha256": etl_result.get("file_sha256"),
            "title": title,
            "type": type,
            "updated_at": datetime.now(),
            "user_id": user_id,
            "project_id": project_id,
            "tags": tags_list,
            "status": "uploaded",
            "metadata": {"source": "user_upload", "format": "text"},
            # From ETL result (these come from etl_base_case)
            "file_size": etl_result.get("file_size"),
            "num_chunks": etl_result.get("num_chunks"),
            "num_entities": etl_result.get("entities_written"),
            "num_relations": etl_result.get("relations_written"),
            "pages": etl_result.get("pages"),
            "scenarios": etl_result.get("scenarios", []),
        }

        # Insert into DB
        result = db().documents.insert_one(document_dict)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert document into database.",
            )

        print(f"[DEBUG] Created document {doc_id} for project {project_id}")

        # Return without _id
        document_dict.pop("_id", None)

        return DocumentResponse(**document_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create document: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


# Create document without file (metadata only)
@router_for_documents.post(
    "/documents/metadata",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_metadata(
    document_data: DocumentCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new document (metadata only, no file)"""
    try:
        document_dict = document_data.model_dump()

        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        # Set all required fields
        document_dict["user_id"] = user_id
        document_dict["created_at"] = datetime.now()
        document_dict["updated_at"] = datetime.now()
        document_dict["id"] = str(uuid.uuid4())

        # Ensure tags and metadata have defaults
        if "tags" not in document_dict or document_dict["tags"] is None:
            document_dict["tags"] = []
        if "metadata" not in document_dict or document_dict["metadata"] is None:
            document_dict["metadata"] = {}

        # Insert into DB
        result = db().documents.insert_one(document_dict)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert document into database.",
            )

        return DocumentResponse(**document_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create document: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


# Get all documents for a project - matches frontend fetchProjectDocuments thunk
@router_for_documents.get("/documents/project/{project_id}")
def get_all_documents(
    project_id: str,
    artifact_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve all documents for the specified project.
    Returns documents and total count matching frontend expectations.
    """
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        # Build query filter
        query_filter = {"user_id": user_id, "project_id": project_id}

        # Add artifact_type filter if provided
        if artifact_type:
            query_filter["artifact_type"] = artifact_type

        # Calculate skip for pagination
        skip = (page - 1) * limit

        # Get total count for this query
        total_count = db().documents.count_documents(query_filter)

        # Fetch documents with pagination
        documents_cursor = (
            db().documents.find(query_filter, {"_id": 0}).skip(skip).limit(limit)
        )

        documents = list(documents_cursor)

        print(
            f"[DEBUG] Found {len(documents)} documents (page {page}, limit {limit}) "
            f"for project {project_id}, total: {total_count}"
        )

        # Return format matching frontend expectations
        return {
            "documents": documents,
            "total_documents": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to retrieve documents: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


# Get a single document by ID
@router_for_documents.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve a specific document by its ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        document = db().documents.find_one(
            {"id": document_id, "user_id": user_id}, {"_id": 0}
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )

        return DocumentResponse(**document)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to retrieve document: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )


# Update a document
@router_for_documents.put("/documents/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a document by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        # Check if document exists
        existing_doc = db().documents.find_one(
            {"id": document_id, "user_id": user_id}, {"_id": 0}
        )

        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )

        # Prepare update data (exclude None values)
        update_dict = {
            k: v for k, v in document_data.model_dump().items() if v is not None
        }

        if not update_dict:
            return DocumentResponse(**existing_doc)

        update_dict["updated_at"] = datetime.now()

        # Update document
        result = db().documents.update_one(
            {"id": document_id, "user_id": user_id}, {"$set": update_dict}
        )

        if result.modified_count == 0:
            print(f"[WARNING] Document {document_id} was not modified")

        # Fetch updated document
        updated_doc = db().documents.find_one(
            {"id": document_id, "user_id": user_id}, {"_id": 0}
        )

        return DocumentResponse(**updated_doc)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to update document: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}",
        )


# Delete a document
@router_for_documents.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document by ID and all its related data"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token.",
            )

        # Verify document exists
        document = db().documents.find_one(
            {"id": document_id, "user_id": user_id}, {"_id": 0, "name": 1, "doc_id": 1}
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )

        doc_id = document.get("doc_id", document_id)

        # Delete all related data
        base_filter = {"doc_id": doc_id, "user_id": user_id}

        chunks_result = db().chunks.delete_many(base_filter)
        tables_result = db().tables.delete_many({"doc_id": doc_id})

        # Delete the document itself
        result = db().documents.delete_one({"id": document_id, "user_id": user_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document {document_id}",
            )

        print(
            f"[DEBUG] Deleted document {document_id}: "
            f"{chunks_result.deleted_count} chunks, "
            f"{tables_result.deleted_count} tables"
        )

        return {
            "message": f"Document '{document.get('name', document_id)}' deleted successfully",
            "document_id": document_id,
            "deleted_counts": {
                "chunks": chunks_result.deleted_count,
                "tables": tables_result.deleted_count,
                "total_items": chunks_result.deleted_count
                + tables_result.deleted_count
                + 1,
            },
            "deleted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete document: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
