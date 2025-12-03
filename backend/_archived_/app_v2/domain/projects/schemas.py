from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

class EntityOut(BaseModel):
    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RelationOut(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
class ProjectEntitiesRelationsOut(BaseModel):
    entities: List[EntityOut]
    relations: List[RelationOut]
    summary: Dict[str, Any]
    project_id: str