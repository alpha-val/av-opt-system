"""
Scenario schemas for Pydantic models.

This module defines the data models for scenarios, which represent
different analysis scenarios within a project.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ScenarioStatus(str, Enum):
    """Scenario status enumeration."""
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScenarioBase(BaseModel):
    """
    Base scenario model with common fields.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Scenario name")
    description: Optional[str] = Field(None, max_length=500, description="Scenario description")
    project_id: str = Field(..., description="Project ID this scenario belongs to")
    status: ScenarioStatus = Field(
        default=ScenarioStatus.DRAFT,
        description="Current status of the scenario"
    )
    # Global objective fields (optional - can be set later)
    global_objective_type: Optional[str] = Field(
        None,
        description="Type of global objective (e.g., 'increase production', 'reduce capex', 'reduce wastage')",
    )
    global_objective_target: Optional[str] = Field(
        None,
        description="Target magnitude of change (numeric value, e.g., '3', '5', '1000000')",
    )
    global_objective_unit: Optional[str] = Field(
        None,
        description="Unit of the global objective target (e.g., '%', '$', 'tpd', 'gpm')",
    )
    objective_description: Optional[str] = Field(
        None, max_length=500, description="Additional context on global objective"
    )
    # Scenario-specific configuration (flexible JSON field)
    configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Scenario configuration parameters"
    )


class ScenarioCreate(ScenarioBase):
    """
    Schema for creating a new scenario.
    """
    pass


class ScenarioUpdate(BaseModel):
    """
    Schema for updating an existing scenario.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Scenario name")
    description: Optional[str] = Field(None, max_length=500, description="Scenario description")
    status: Optional[ScenarioStatus] = Field(None, description="Current status of the scenario")
    global_objective_type: Optional[str] = Field(
        None, description="Type of global objective"
    )
    global_objective_target: Optional[str] = Field(
        None, description="Target magnitude of change (numeric value)"
    )
    global_objective_unit: Optional[str] = Field(
        None, description="Unit of the global objective target (e.g., '%', '$', 'tpd', 'gpm')"
    )
    objective_description: Optional[str] = Field(
        None, max_length=500, description="Additional context on global objective"
    )
    configuration: Optional[Dict[str, Any]] = Field(None, description="Scenario configuration parameters")


class ScenarioOut(ScenarioBase):
    """
    Schema for scenario output/response.
    """
    id: str = Field(..., description="Unique scenario identifier (MongoDB ObjectId as string)")
    created_at: datetime = Field(..., description="Scenario creation timestamp")
    updated_at: datetime = Field(..., description="Scenario last update timestamp")

