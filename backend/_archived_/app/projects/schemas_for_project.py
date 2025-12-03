from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    project_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(default="active")
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    project_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Schema for project API responses"""

    id: str
    name: str
    description: Optional[str]
    user_id: str
    project_type: Optional[str]
    status: str = "active"
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode in v1)
        json_schema_extra = {
            "example": {
                "id": "3d8c8b09-4c52-4fd2-ae87-29ef4c5ded65",
                "name": "Mining Cost Analysis 2024",
                "description": "Comprehensive cost analysis for mining operations",
                "user_id": "0d249345-350a-4a09-9bd1-0dcd79723919",
                "project_type": "mining",
                "status": "active",
                "tags": ["cost", "analysis", "2024"],
                "metadata": {"region": "North America", "priority": "high"},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
