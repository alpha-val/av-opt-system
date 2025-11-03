# Document repository
from typing import List, Optional
from datetime import datetime, timezone
from .schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from ...adapters.mongo.client import db
from bson import ObjectId

_documents_collection = db().documents


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
        result.append(DocumentResponse(**doc))
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
    return DocumentResponse(**doc)


async def update_document(document_id: str, data: DocumentUpdate) -> Optional[DocumentResponse]:
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
    return DocumentResponse(**result)


async def delete_document(document_id: str) -> bool:
    """Delete a document from the MongoDB collection."""
    result = _documents_collection.delete_one({"_id": ObjectId(document_id)})
    return result.deleted_count > 0