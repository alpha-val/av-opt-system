"""
Scenario request/response schemas.

Defines API contracts for scenario operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


class ParameterChange(BaseModel):
    """
    A single parameter change in a scenario.
    
    Example:
        parameter_name: "primary_crusher_product_size"
        original_value: 8.0
        new_value: 6.0
        unit: "inches"
    """
    
    parameter_name: str = Field(
        ...,
        description="Name of parameter being changed"
    )
    original_value: Any = Field(
        ...,
        description="Original value from base case"
    )
    new_value: Any = Field(
        ...,
        description="New value for this scenario"
    )
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement"
    )
    
    # Context about the change
    affected_entity_id: Optional[str] = Field(
        None,
        description="ID of entity being modified (if applicable)"
    )
    affected_entity_name: Optional[str] = Field(
        None,
        description="Name of entity being modified"
    )
    rationale: Optional[str] = Field(
        None,
        description="Why this change is being considered"
    )


class ScenarioCreate(BaseModel):
    """
    Request schema for creating a scenario.
    """
    
    project_id: str = Field(
        ...,
        description="Parent project ID"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Scenario name"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed description of scenario"
    )
    
    parameter_changes: List[ParameterChange] = Field(
        ...,
        min_items=1,
        description="List of parameter changes defining this scenario"
    )
    
    # Analysis configuration
    max_options_to_generate: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of options to generate"
    )
    
    analysis_assumptions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assumptions for cost/NPV analysis"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    
    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "507f1f77bcf86cd799439011",
                "name": "Reduce Primary Crusher Product Size",
                "description": "Evaluate impact of reducing primary crusher product size from 8\" to 6\" to improve SAG mill performance",
                "parameter_changes": [
                    {
                        "parameter_name": "product_p80",
                        "original_value": 8.0,
                        "new_value": 6.0,
                        "unit": "inches",
                        "affected_entity_name": "Primary Gyratory Crusher",
                        "rationale": "Finer feed to SAG mill expected to improve throughput"
                    }
                ],
                "max_options_to_generate": 15,
                "analysis_assumptions": {
                    "discount_rate": 0.10,
                    "project_life_years": 20,
                    "escalation_rate": 0.03
                },
                "tags": ["crushing", "optimization", "throughput"]
            }
        }


class ScenarioUpdate(BaseModel):
    """
    Request schema for updating a scenario.
    
    All fields are optional - only provided fields will be updated.
    """
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200
    )
    
    description: Optional[str] = Field(
        None,
        max_length=2000
    )
    
    parameter_changes: Optional[List[ParameterChange]] = None
    
    analysis_assumptions: Optional[Dict[str, Any]] = None
    
    tags: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Scenario Name",
                "description": "Updated description",
                "tags": ["crushing", "optimization"]
            }
        }


class ScenarioStatusUpdate(BaseModel):
    """
    Request schema for updating scenario status.
    """
    
    status: Literal["draft", "processing", "completed", "error"] = Field(
        ...,
        description="Scenario status"
    )
    
    compute_state: Optional[Literal[
        "not_started",
        "equipment_selection",
        "cost_estimation",
        "downstream_analysis",
        "completed",
        "failed"
    ]] = Field(
        None,
        description="Detailed compute state"
    )


class ScenarioResponse(BaseModel):
    """
    Response schema for scenario data.
    
    Returned by GET /scenarios/{id} and POST /scenarios
    """
    
    id: str = Field(..., alias="_id", description="Scenario ID")
    project_id: str
    name: str
    description: Optional[str]
    
    # Parameter changes
    parameter_changes: List[ParameterChange]
    
    # Status
    status: str
    compute_state: Optional[str]
    
    # Options
    option_count: int = Field(0, description="Number of generated options")
    selected_option_id: Optional[str] = Field(
        None,
        description="ID of selected option (if any)"
    )
    
    # Analysis config
    max_options_to_generate: int
    analysis_assumptions: Dict[str, Any]
    
    # Base case snapshot (simplified for response)
    base_case_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of base case configuration"
    )
    
    # Metadata
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439012",
                "project_id": "507f1f77bcf86cd799439011",
                "name": "Reduce Primary Crusher Product Size",
                "description": "Evaluate impact of reducing primary crusher product size from 8\" to 6\"",
                "parameter_changes": [
                    {
                        "parameter_name": "product_p80",
                        "original_value": 8.0,
                        "new_value": 6.0,
                        "unit": "inches",
                        "affected_entity_name": "Primary Gyratory Crusher"
                    }
                ],
                "status": "completed",
                "compute_state": "completed",
                "option_count": 12,
                "selected_option_id": None,
                "max_options_to_generate": 15,
                "analysis_assumptions": {
                    "discount_rate": 0.10,
                    "project_life_years": 20
                },
                "base_case_summary": {
                    "total_entities": 45,
                    "total_installed_cost": 250000000
                },
                "tags": ["crushing", "optimization"],
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-10-01T11:30:00Z"
            }
        }


class ScenarioListResponse(BaseModel):
    """
    Response schema for scenario list.
    """
    
    scenarios: List[ScenarioResponse]
    total: int = Field(..., description="Total number of scenarios")
    skip: int = Field(..., description="Number skipped")
    limit: int = Field(..., description="Maximum returned")
    
    class Config:
        schema_extra = {
            "example": {
                "scenarios": [],
                "total": 25,
                "skip": 0,
                "limit": 20
            }
        }


class ScenarioGenerateOptionsRequest(BaseModel):
    """
    Request schema for triggering option generation.
    """
    
    max_options: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Override max options to generate"
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional filters for equipment selection"
    )
    
    force_regenerate: bool = Field(
        False,
        description="Force regeneration even if options exist"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "max_options": 20,
                "filters": {
                    "manufacturer": "Metso",
                    "min_capacity_tph": 1000
                },
                "force_regenerate": False
            }
        }