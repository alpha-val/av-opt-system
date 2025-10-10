"""
Option request/response schemas.

Defines API contracts for option operations.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .costing import CostBreakdown, DownstreamImpact, NPVAnalysis


class EquipmentSummary(BaseModel):
    """
    Summary of equipment for an option.
    """
    
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity_tph: Optional[float] = None
    power_kw: Optional[float] = None
    
    # Key specifications
    specifications: Dict[str, Any] = Field(default_factory=dict)


class OptionResponse(BaseModel):
    """
    Response schema for option data.
    
    Contains complete option information including cost breakdown
    and downstream analysis.
    """
    
    id: str = Field(..., alias="_id", description="Option ID")
    scenario_id: str
    project_id: str
    
    name: str
    description: Optional[str]
    
    # Equipment summary
    equipment: EquipmentSummary
    
    # Cost data (complete breakdown)
    cost_data: CostBreakdown
    
    # CAPEX/OPEX totals
    total_capex: float = Field(
        ...,
        description="Total capital expenditure"
    )
    total_capex_with_downstream: float = Field(
        ...,
        description="Total CAPEX including downstream impacts"
    )
    
    opex: Dict[str, float] = Field(
        default_factory=dict,
        description="Operating expenditure breakdown"
    )
    
    # Downstream analysis (USP)
    downstream_impact: DownstreamImpact
    total_downstream_capex_delta: float = Field(
        0.0,
        description="Total downstream CAPEX impact"
    )
    
    # NPV analysis
    npv_analysis: Optional[NPVAnalysis] = None
    
    # Ranking
    rank: Optional[int] = Field(
        None,
        description="Rank within scenario (1 = best)"
    )
    selected: bool = Field(
        False,
        description="Whether this option is selected"
    )
    
    # Source entity reference
    source_entity_id: Optional[str] = Field(
        None,
        description="ID of entity this option modifies"
    )
    
    # Data provenance
    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used for this option"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this option (0-1)"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439013",
                "scenario_id": "507f1f77bcf86cd799439012",
                "project_id": "507f1f77bcf86cd799439011",
                "name": "Metso Superior MKII 54-75 Gyratory",
                "description": "Primary gyratory crusher option",
                "equipment": {
                    "manufacturer": "Metso",
                    "model": "Superior MKII 54-75",
                    "capacity_tph": 4500,
                    "power_kw": 750,
                    "specifications": {
                        "feed_opening_in": 54.0,
                        "closed_side_setting_in": 6.0
                    }
                },
                "cost_data": {
                    "purchase_cost_base": 2500000,
                    "purchase_cost_escalated": 2750000,
                    "installed_equipment_cost": 9625000
                },
                "total_capex": 9625000,
                "total_capex_with_downstream": 11250000,
                "downstream_impact": {
                    "affected_entities": [],
                    "capex_delta": 1625000
                },
                "rank": 1,
                "selected": False,
                "created_at": "2025-10-01T11:00:00Z",
                "updated_at": "2025-10-01T11:00:00Z"
            }
        }


class OptionListResponse(BaseModel):
    """
    Response schema for option list.
    """
    
    options: List[OptionResponse]
    total: int
    skip: int
    limit: int


class OptionComparisonItem(BaseModel):
    """
    Single option data in comparison view.
    """
    
    option_id: str
    name: str
    rank: Optional[int]
    selected: bool
    
    # Equipment
    manufacturer: Optional[str]
    model: Optional[str]
    capacity_tph: Optional[float]
    power_kw: Optional[float]
    
    # Costs
    purchase_cost: Optional[float]
    installed_cost: Optional[float]
    total_capex: Optional[float]
    annual_opex: Optional[float]
    
    # Downstream
    downstream_capex_delta: Optional[float]
    downstream_entities_affected: int
    
    # Metrics
    npv: Optional[float]
    payback_years: Optional[float]


class OptionComparisonResponse(BaseModel):
    """
    Response schema for option comparison.
    
    Provides side-by-side comparison of multiple options.
    """
    
    scenario_id: str
    options_compared: int
    options: List[OptionComparisonItem]
    
    class Config:
        schema_extra = {
            "example": {
                "scenario_id": "507f1f77bcf86cd799439012",
                "options_compared": 3,
                "options": [
                    {
                        "option_id": "507f1f77bcf86cd799439013",
                        "name": "Metso Superior MKII 54-75",
                        "rank": 1,
                        "selected": False,
                        "manufacturer": "Metso",
                        "model": "Superior MKII 54-75",
                        "capacity_tph": 4500,
                        "power_kw": 750,
                        "purchase_cost": 2750000,
                        "installed_cost": 9625000,
                        "total_capex": 9625000,
                        "annual_opex": 450000,
                        "downstream_capex_delta": 1625000,
                        "downstream_entities_affected": 2,
                        "npv": 15000000,
                        "payback_years": 3.2
                    }
                ]
            }
        }


class OptionSelectionRequest(BaseModel):
    """
    Request schema for selecting an option.
    """
    
    reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Reason for selection"
    )
    
    selected_by: Optional[str] = Field(
        None,
        description="User who made the selection"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "reason": "Lowest total CAPEX with acceptable NPV",
                "selected_by": "john.engineer@mining.com"
            }
        }