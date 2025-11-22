"""
Cost estimate schemas for Pydantic models.

This module defines the data models for cost estimates, which represent
different cost estimation scenarios within a project scenario.
"""
from typing import Optional, List, Dict, Any
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
    # Optional fields for cost calculation
    scenario_description: Optional[str] = Field(
        None, description="Description of the scenario for cost calculation"
    )
    selected_entities: Optional[List[str]] = Field(
        None, description="List of base case entity IDs to calculate costs for"
    )
    entity_selection_state: Optional[Dict[str, bool]] = Field(
        None, description="Checkbox selections for entity inclusion (entity_id -> bool)"
    )
    top_k: Optional[int] = Field(
        3, description="Number of top matching tabular entities to return per base entity"
    )


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
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata including cost comparison report"
    )

