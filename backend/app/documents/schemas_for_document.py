from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""

    file_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=200)
    project_id: str
    type: Optional[str] = Field(None, max_length=50)
    artifact_type: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    size: Optional[int] = None
    length: Optional[int] = None


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""

    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = Field(None, max_length=50)
    artifact_type: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    size: Optional[int] = None
    length: Optional[int] = None


class DocumentResponse(BaseModel):
    """Schema for document API responses"""

    id: str
    file_name: str
    title: str
    user_id: str
    project_id: str
    type: Optional[str]
    artifact_type: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    file_size: Optional[int] = None
    file_length: Optional[int] = None
    created_at: datetime
    status: str
    updated_at: datetime
    # return {
    #     "doc_id": doc_id,
    #     "filename": filename,
    #     "pages": len(pages_clean),
    #     "chunks_written": len(chunks),
    #     "entities_written": len(nodes),
    #     "relations_written": len(edges),
    #     # "mentions_written": len(mentions),
    #     "user_id": user_id,
    #     "project_id": project_id,
    #     "document_metadata": doc_metadata,
    # }

    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode in v1)
        json_schema_extra = {
            "example": {
                "id": "5f8d0d55-3c6a-4f8b-9f1e-2b8c9e4d5f6a",
                "file_name": "mining_report_2024.pdf",
                "title": "Mining Report 2024",
                "user_id": "0d249345-350a-4a09-9bd1-0dcd79723919",
                "project_id": "3d8c8b09-4c52-4fd2-ae87-29ef4c5ded65",
                "type": "report",
                "artifact_type": "base_case",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "tags": ["sample", "document"],
                "metadata": {"source": "user_upload", "format": "text"},
                "file_size": 1024,
                "file_length": 250,
                "status": "processed",
            }
        }
