"""
Project schemas for request/response models.

This module defines Pydantic models for project data validation and serialization.
All models follow the standard CRUD pattern: Create, Update, and Output models.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    DRAFT = "draft"
    PROCESSING = "processing"
    VALIDATION = "validation"
    COMPLETED = "completed"


class ProjectBase(BaseModel):
    """
    Base project model with common fields.

    This is the base class for all project-related models.
    Contains the core fields that are shared across create, update, and output models.
    """

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(
        None, max_length=500, description="Project description"
    )
    tags: Optional[List[str]] = Field(
        None, description="List of tags for categorization"
    )
    # Project status
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT, description="Current status of the project"
    )
    # Document references
    base_case_documents: List[str] = Field(
        default_factory=list, description="List of document IDs for base case reports"
    )
    tabular_data_documents: List[str] = Field(
        default_factory=list,
        description="List of document IDs for tabular data (vault)",
    )


class ProjectCreate(ProjectBase):
    """
    Schema for creating a new project.

    Inherits all fields from ProjectBase. This is used when creating
    a new project via POST /api/v1/projects
    """

    pass


class ProjectUpdate(BaseModel):
    """
    Schema for updating an existing project.

    All fields are optional to support partial updates (PATCH semantics).
    Only provided fields will be updated in the database.
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Project name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Project description"
    )
    tags: Optional[List[str]] = Field(
        None, description="List of tags for categorization"
    )
    status: Optional[ProjectStatus] = Field(
        None, description="Current status of the project"
    )
    base_case_documents: Optional[List[str]] = Field(
        None, description="List of document IDs for base case reports"
    )
    tabular_data_documents: Optional[List[str]] = Field(
        None, description="List of document IDs for tabular data"
    )


class ProjectOut(ProjectBase):
    """
    Schema for project output/response.

    Includes all base fields plus metadata fields (id, timestamps).
    This is returned when fetching projects from the API.
    """

    id: str = Field(
        ..., description="Unique project identifier (MongoDB ObjectId as string)"
    )
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")
