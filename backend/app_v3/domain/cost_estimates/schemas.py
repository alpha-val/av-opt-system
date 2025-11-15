"""
Cost estimate schemas for Pydantic models.

This module defines the data models for cost estimates, which represent
different cost estimation scenarios within a project scenario.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CostEstimateBase(BaseModel):
    """
    Base cost estimate model with common fields.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Cost estimate name")
    description: Optional[str] = Field(None, max_length=500, description="Cost estimate description")
    scenario_id: str = Field(..., description="Scenario ID this cost estimate belongs to")


class CostEstimateCreate(CostEstimateBase):
    """
    Schema for creating a new cost estimate.
    """
    pass


class CostEstimateUpdate(BaseModel):
    """
    Schema for updating an existing cost estimate.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Cost estimate name")
    description: Optional[str] = Field(None, max_length=500, description="Cost estimate description")


class CostEstimateOut(CostEstimateBase):
    """
    Schema for cost estimate output/response.
    """
    id: str = Field(..., description="Unique cost estimate identifier (MongoDB ObjectId as string)")
    created_at: datetime = Field(..., description="Cost estimate creation timestamp")
    updated_at: datetime = Field(..., description="Cost estimate last update timestamp")

