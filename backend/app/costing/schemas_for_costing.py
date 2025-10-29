from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class CostBreakdown(BaseModel):
    """Cost breakdown for base case, proposed, and delta."""

    capital: Optional[float] = Field(None, description="Capital cost")
    installation: Optional[float] = Field(None, description="Installation cost")
    operating_annual: Optional[float] = Field(None, description="Annual operating cost")
    maintenance_annual: Optional[float] = Field(
        None, description="Annual maintenance cost"
    )
    total: Optional[float] = Field(None, description="Total cost")
    cost_calculation_details: Optional[str] = None


class CostEstimateRequest(BaseModel):
    """Request to estimate costs for a scenario."""

    project_id: str = Field(..., description="Project identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    cost_id: Optional[str] = Field(
        None, description="Cost estimate identifier (auto-generated if not provided)"
    )
    scenario_description: str = Field(
        ..., description="Description of what user wants to change"
    )
    entity_types: Optional[List[str]] = Field(
        default=["Equipment", "Material", "Process"],
        description="Types of entities to consider for costing",
    )
    uncertainties: Optional[Dict[str, Any]] = Field(
        None, description="Uncertainty parameters for cost estimation"
    )

    # Optional fields for enhanced filtering
    goal: Optional[str] = Field(
        None, description="Scenario goal (increase_production, reduce_capex, etc.)"
    )
    change_type: Optional[str] = Field(
        None, description="Type of change (equipment, process, etc.)"
    )
    equipment_types: Optional[List[str]] = Field(
        None, description="Specific equipment types to filter"
    )
    capacity_range: Optional[List[float]] = Field(
        None, description="Capacity range [min, max] for filtering"
    )
    selected_entities: Optional[List[str]] = Field(
        None, description="List of user-selected entity IDs"
    )


class CostEstimateResponse(BaseModel):
    estimate_id: str = Field(..., description="Cost estimate identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    project_id: str = Field(..., description="Project identifier")
    scenario_description: str = Field(..., description="Original scenario description")
    status: str = Field(..., description="Status (completed, failed, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CostEstimateResponse2(BaseModel):
    """Response with cost estimate results."""

    estimate_id: str = Field(..., description="Cost estimate identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    project_id: str = Field(..., description="Project identifier")
    scenario_description: str = Field(..., description="Original scenario description")
    status: str = Field(..., description="Status (completed, failed, etc.)")
    confidence: Optional[str] = Field(
        None, description="Confidence level (low, medium, high)"
    )

    cost_breakdown: Optional[Dict[str, CostBreakdown]] = Field(
        None,
        description="Cost breakdown with keys: base_case_total, proposed_total, delta",
    )

    relevant_entities: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None, description="Relevant entities with keys: base_case, tabular, proposed"
    )

    entity_types: Optional[List[str]] = Field(
        None, description="Entity types used in estimation"
    )
    uncertainties: Optional[Dict[str, Any]] = Field(
        None, description="Uncertainty parameters used"
    )
    retrieval_method: Optional[str] = Field(
        None, description="Method used to retrieve entities"
    )
    entity_counts: Optional[Dict[str, int]] = Field(
        None, description="Count of entities retrieved"
    )

    assumptions: Optional[List[str]] = Field(
        None, description="List of assumptions made"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    confidence_explanation: Optional[str] = Field(
        None, description="Explanation of confidence level"
    )

    estimated_at: datetime = Field(..., description="When estimate was created")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")


class CostEstimateListResponse(BaseModel):
    """List of cost estimates."""

    estimates: List[CostEstimateResponse]
    total: int
