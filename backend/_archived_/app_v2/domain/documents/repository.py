# Document repository
from typing import List, Optional
from datetime import datetime, timezone
from .schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from ...adapters.mongo.client import db
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

_documents_collection = db().documents
_chunks_collection = db().chunks
_entities_collection = db().entities
_relations_collection = db().relations
_tables_collection = db().tables
_scenarios_collection = db().scenarios
_cost_estimates_collection = db().cost_estimates


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_document(data: DocumentCreate) -> DocumentResponse:
    """Create a new document in the MongoDB collection."""
    doc = data.model_dump()
    doc["created_at"] = _now()
    doc["updated_at"] = _now()
    # Ensure user_id is present (should come from auth, but provide default for now)
    if "user_id" not in doc:
        doc["user_id"] = ""  # Will be set by backend/auth

    result = _documents_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)  # Convert ObjectId to string
    return DocumentResponse(**doc)


async def list_all_documents() -> List[DocumentResponse]:
    """List all documents from the MongoDB collection."""
    documents = _documents_collection.find()
    result = []
    for doc in documents:
        doc["id"] = str(doc["_id"])  # Convert ObjectId to string
        # Ensure required fields have defaults
        if "user_id" not in doc:
            doc["user_id"] = ""
        if "tags" not in doc:
            doc["tags"] = []
        if "metadata" not in doc:
            doc["metadata"] = {}
        # Ensure required fields for DocumentResponse schema
        if "file_name" not in doc:
            doc["file_name"] = doc.get("filename", "unknown.pdf")  # Fallback to filename if exists
        if "title" not in doc:
            doc["title"] = doc.get("file_name", doc.get("filename", "Untitled Document"))
        if "type" not in doc:
            doc["type"] = None  # Optional field, but schema requires it (can be None)
        if "created_at" not in doc:
            doc["created_at"] = _now()  # Use current time as fallback
        if "updated_at" not in doc:
            doc["updated_at"] = _now()  # Use current time as fallback
        try:
            result.append(DocumentResponse(**doc))
        except Exception as e:
            # Log and skip invalid documents
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Skipping invalid document {doc.get('id')}: {e}")
            continue
    return result


async def get_document(document_id: str) -> Optional[DocumentResponse]:
    """Get a document by its ID from the MongoDB collection."""
    doc = _documents_collection.find_one({"_id": ObjectId(document_id)})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])  # Convert ObjectId to string
    # Ensure required fields have defaults
    if "user_id" not in doc:
        doc["user_id"] = ""
    if "tags" not in doc:
        doc["tags"] = []
    if "metadata" not in doc:
        doc["metadata"] = {}
    # Ensure required fields for DocumentResponse schema
    if "file_name" not in doc:
        doc["file_name"] = doc.get("filename", "unknown.pdf")
    if "title" not in doc:
        doc["title"] = doc.get("file_name", doc.get("filename", "Untitled Document"))
    if "type" not in doc:
        doc["type"] = None
    if "created_at" not in doc:
        doc["created_at"] = _now()
    if "updated_at" not in doc:
        doc["updated_at"] = _now()
    return DocumentResponse(**doc)


async def update_document(
    document_id: str, data: DocumentUpdate
) -> Optional[DocumentResponse]:
    """Update a document in the MongoDB collection."""
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = _now()
    result = _documents_collection.find_one_and_update(
        {"_id": ObjectId(document_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        return None
    result["id"] = str(result["_id"])  # Convert ObjectId to string
    # Ensure required fields have defaults
    if "user_id" not in result:
        result["user_id"] = ""
    if "tags" not in result:
        result["tags"] = []
    if "metadata" not in result:
        result["metadata"] = {}
    # Ensure required fields for DocumentResponse schema
    if "file_name" not in result:
        result["file_name"] = result.get("filename", "unknown.pdf")
    if "title" not in result:
        result["title"] = result.get("file_name", result.get("filename", "Untitled Document"))
    if "type" not in result:
        result["type"] = None
    if "created_at" not in result:
        result["created_at"] = _now()
    if "updated_at" not in result:
        result["updated_at"] = _now()
    return DocumentResponse(**result)


async def delete_document(document_id: str) -> bool:
    """Delete a document from the MongoDB collection."""
    result = _documents_collection.delete_one({"_id": ObjectId(document_id)})
    return result.deleted_count > 0


async def process_document(document_id: str) -> Optional[DocumentResponse]:
    """
    Process a document using the ETL pipeline.

    Note: This function is a placeholder. Actual document processing should be
    handled through the dedicated endpoints in documents_v2.py router which
    accept file uploads and use DocumentProcessingService directly.
    """
    # TODO: Implement document processing if needed
    # For now, document processing is handled via the /documents/v2/* endpoints
    print(f"[DEBUG : documents.repository.py] Processing document: {document_id}")
    document = await get_document(document_id)
    if not document:
        return None
    # Document processing is handled via dedicated endpoints
    return document
