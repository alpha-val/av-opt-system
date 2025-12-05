"""
Schemas for component-based cost estimates.

This module defines Pydantic schemas for cost estimates created from
SystemDesign component selections.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ComponentCostEstimateBase(BaseModel):
    """Base schema for component cost estimates."""
    name: str = Field(..., min_length=1, max_length=200, description="Cost estimate name")
    description: Optional[str] = Field(None, max_length=500, description="Cost estimate description")
    scenario_id: str = Field(..., description="Scenario ID this cost estimate belongs to")


class ComponentLeverConfig(BaseModel):
    """Configuration for a single component's levers."""
    component_id: str = Field(..., description="Component identifier")
    lever_values: Dict[str, Any] = Field(
        ..., description="Decision lever values for this component (lever_id -> value)"
    )
    lever_types: Dict[str, str] = Field(
        ..., description="Decision lever types for this component (lever_id -> 'Fixed' | 'Floating')"
    )


class ComponentCostEstimateCreate(ComponentCostEstimateBase):
    """
    Schema for creating a component-based cost estimate.
    
    Includes SystemDesign configuration data for cost calculation.
    Components are organized with their own lever values and types.
    """
    # SystemDesign configuration - components organized by component_id
    components: List[ComponentLeverConfig] = Field(
        ..., description="List of selected components with their lever configurations"
    )
    # Optional calculation parameters
    top_k: Optional[int] = Field(
        3, description="Number of top matching tabular entities per component"
    )
    cutoff: Optional[float] = Field(
        0.5, description="Minimum similarity score threshold for semantic search"
    )


class ComponentCostEstimateOut(ComponentCostEstimateBase):
    """
    Schema for component cost estimate output/response.
    """
    id: str = Field(..., description="Unique cost estimate identifier")
    project_id: Optional[str] = Field(None, description="Project ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    components_config: Optional[Dict[str, Any]] = Field(
        None, description="Original SystemDesign configuration"
    )
    cost_report: Optional[Dict[str, Any]] = Field(
        None, description="Cost comparison report (baseline vs redesigned)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata including calculation results"
    )

