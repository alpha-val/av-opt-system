"""
Document ingestion endpoints for the new parsing pipeline.

Provides endpoints for ingesting base case and tabular data documents
with full MSIO ontology validation and vectorization.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
import logging

from ....domain.parsing.services import DocumentProcessingService
from ....domain.documents.schemas import DocumentCreate
from ....domain.documents import services
from ....domain.documents.repository import create_document
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Initialize processing service
processing_service = DocumentProcessingService()

etl_router = APIRouter(prefix="/api/v1/etl", tags=["etl"])


@etl_router.post("/base-case", status_code=status.HTTP_201_CREATED)
async def ingest_base_case_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    projectId: Optional[str] = Form(
        None
    ),  # Alternative name for frontend compatibility
    user_id: Optional[str] = Form(None),
    userId: Optional[str] = Form(None),  # Alternative name for frontend compatibility
    artifact_type: Optional[str] = Form(None),  # Frontend sends this
    metadata: Optional[str] = Form(None),  # Frontend sends metadata as JSON string
    doc_id: Optional[str] = Form(None),
    chunking_strategy: str = Form("character"),
    char_limit: int = Form(5000),
    pages: Optional[str] = Form(None),
    validate_msio: bool = Form(True),
    strict_validation: bool = Form(False),
):
    """
    Ingest a base case document through the complete ETL pipeline.

    Pipeline stages:
    1. Extract and clean text from PDF
    2. Chunk text (character/page/byte strategy)
    3. Extract entities and edges using LLM with MSIO ontology
    4. Validate entities against MSIO ontology
    5. Normalize and deduplicate entities
    6. Store chunks in Pinecone (vectorized for similarity search)
    7. Store entities and edges in MongoDB

    Args:
        file: PDF file to process
        project_id: Project identifier
        user_id: User identifier
        doc_id: Optional document identifier (generated if not provided)
        chunking_strategy: "character" (default), "page", or "byte"
        char_limit: Character limit for character-based chunking (default: 5000)
        pages: Optional page range filter (e.g., "1-5,10")
        validate_msio: Whether to validate entities against MSIO ontology (default: True)
        strict_validation: If True, invalid entities are excluded (default: False)

    Returns:
        Processing results with statistics
    """
    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate chunking strategy
    valid_strategies = ["character", "page", "byte"]
    if chunking_strategy not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunking_strategy. Must be one of: {', '.join(valid_strategies)}",
        )

    try:
        # Handle alternative field names from frontend
        actual_project_id = project_id or projectId or ""
        actual_user_id = user_id or userId or ""

        if not actual_project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required"
            )

        # If user_id is not provided, use empty string (will be set by auth if needed)
        if not actual_user_id:
            actual_user_id = ""
            logger.warning(
                f"user_id not provided for document upload, using empty string"
            )

        # Read file content
        pdf_bytes = await file.read()
        filename = file.filename or "uploaded.pdf"

        logger.info(
            f"Received base case document upload: {filename} "
            f"(project_id: {actual_project_id}, user_id: {actual_user_id})"
        )

        # Process document
        result = processing_service.process_base_case_document(
            pdf_bytes=pdf_bytes,
            filename=filename,
            doc_id=doc_id or "",
            project_id=actual_project_id,
            user_id=actual_user_id,
            chunking_strategy=chunking_strategy,
            char_limit=char_limit,
            pages=pages,
            validate_msio=validate_msio,
            strict_validation=strict_validation,
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error occurred"),
            )

        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                import json

                metadata_dict = json.loads(metadata)
            except Exception as e:
                logger.warning(f"Failed to parse metadata JSON: {e}")
                metadata_dict = {}

        # Create document in MongoDB
        document_data = DocumentCreate(
            file_name=filename,
            title=filename,
            project_id=actual_project_id,
            artifact_type=artifact_type or "base_case",
            tags=[],
            metadata=metadata_dict,
            size=len(pdf_bytes),
            length=len(pdf_bytes),
        )
        # Create document - repository will set default user_id to ""
        document = await create_document(document_data)

        # Update user_id if we have one (repository sets default to "")
        if actual_user_id:
            from ....adapters.mongo.client import db
            from bson import ObjectId

            doc_id = (
                document.id
                if hasattr(document, "id")
                else getattr(document, "id", None)
            )
            if doc_id:
                try:
                    db().documents.update_one(
                        {"_id": ObjectId(doc_id)}, {"$set": {"user_id": actual_user_id}}
                    )
                    # Update the document object for return
                    if hasattr(document, "user_id"):
                        document.user_id = actual_user_id
                except Exception as e:
                    logger.warning(
                        f"Failed to update user_id for document {doc_id}: {e}"
                    )

        # Return combined result with processing stats and document metadata
        return {
            "document": (
                document.model_dump() if hasattr(document, "model_dump") else document
            ),
            "processing": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting base case document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@etl_router.post("/tabular-data", status_code=status.HTTP_201_CREATED)
async def ingest_tabular_data_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    user_id: str = Form(...),
    doc_id: Optional[str] = Form(None),
    pages: Optional[str] = Form(None),
    max_rows_per_chunk: int = Form(50),
    validate_msio: bool = Form(True),
    strict_validation: bool = Form(False),
):
    """
    Ingest a tabular data document through the complete ETL pipeline.

    Pipeline stages:
    1. Extract and clean text from PDF
    2. Extract tables (lattice and stream types)
    3. Create table chunks for LLM processing
    4. Extract entities from tables using LLM with MSIO ontology
    5. Validate entities against MSIO ontology
    6. Normalize and deduplicate entities
    7. Store entities in MongoDB and Pinecone (vectorized)
    8. Store table metadata in MongoDB

    Note: For tabular data, only entities (not text chunks) are vectorized and stored
    in Pinecone for entity similarity search.

    Args:
        file: PDF file to process
        project_id: Project identifier
        user_id: User identifier
        doc_id: Optional document identifier (generated if not provided)
        pages: Optional page range filter (e.g., "1-5,10")
        max_rows_per_chunk: Maximum rows per table chunk (default: 50)
        validate_msio: Whether to validate entities against MSIO ontology (default: True)
        strict_validation: If True, invalid entities are excluded (default: False)

    Returns:
        Processing results with statistics
    """
    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    try:
        # Read file content
        pdf_bytes = await file.read()
        filename = file.filename or "uploaded.pdf"

        logger.info(
            f"Received tabular data document upload: {filename} "
            f"(project_id: {project_id}, user_id: {user_id})"
        )

        # Process document
        result = processing_service.process_tabular_data_document(
            pdf_bytes=pdf_bytes,
            filename=filename,
            doc_id=doc_id or "",
            project_id=project_id,
            user_id=user_id,
            pages=pages,
            max_rows_per_chunk=max_rows_per_chunk,
            validate_msio=validate_msio,
            strict_validation=strict_validation,
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error occurred"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting tabular data document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )
