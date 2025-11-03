# Document schemas
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
    size: Optional[int] = None
    length: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=200)