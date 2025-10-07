"""
Costing result schemas.

Defines structures for cost estimation results with full provenance.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


class CostProvenance(BaseModel):
    """
    Provenance information for a cost value.
    
    Tracks where the cost came from and how confident we are.
    """
    
    source: str = Field(
        ...,
        description="Source of cost (e.g., 'vendor_quote', 'cost_table', 'escalated_estimate')"
    )
    source_id: Optional[str] = Field(
        None,
        description="ID of source document/table"
    )
    source_name: Optional[str] = Field(
        None,
        description="Name/description of source"
    )
    
    # Temporal context
    cost_year: int = Field(
        ...,
        description="Year cost is from"
    )
    escalated_to_year: Optional[int] = Field(
        None,
        description="Year cost was escalated to (if applicable)"
    )
    escalation_factor: Optional[float] = Field(
        None,
        description="Escalation factor applied"
    )
    escalation_index: Optional[str] = Field(
        None,
        description="Index used for escalation (e.g., 'CEPCI')"
    )
    
    # Confidence
    confidence: Literal["high", "medium", "low"] = Field(
        "medium",
        description="Confidence in this cost"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about this cost"
    )


class CostBreakdownItem(BaseModel):
    """
    Single line item in cost breakdown.
    """
    
    category: str = Field(
        ...,
        description="Cost category (e.g., 'Equipment', 'Civil & Structural')"
    )
    wbs_code: Optional[str] = Field(
        None,
        description="WBS code if applicable"
    )
    
    amount: float = Field(..., description="Cost amount")
    currency: str = Field("USD", description="Currency")
    
    # Calculation method
    calculation_method: Optional[str] = Field(
        None,
        description="How this was calculated (e.g., 'lang_factor', 'direct_quote')"
    )
    calculation_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Details of calculation"
    )
    
    # Provenance
    provenance: Optional[CostProvenance] = None


class CostBreakdown(BaseModel):
    """
    Complete cost breakdown with provenance.
    
    This is a key USP feature - full traceability of where every
    dollar in the estimate came from.
    """
    
    # Purchase cost
    purchase_cost_base: float = Field(
        ...,
        description="Base equipment purchase cost"
    )
    purchase_cost_base_year: int = Field(
        ...,
        description="Year of base cost"
    )
    purchase_cost_escalated: float = Field(
        ...,
        description="Escalated equipment purchase cost"
    )
    escalation_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Details of escalation calculation"
    )
    
    # Installed cost breakdown
    installed_cost_items: List[CostBreakdownItem] = Field(
        default_factory=list,
        description="Breakdown of installed cost components"
    )
    
    # Totals
    total_direct_cost: float = Field(
        ...,
        description="Total direct cost"
    )
    total_indirect_cost: float = Field(
        0.0,
        description="Total indirect cost"
    )
    installed_equipment_cost: float = Field(
        ...,
        description="Total installed equipment cost (TIC)"
    )
    
    # Factors used
    lang_factor_applied: Optional[float] = Field(
        None,
        description="Overall lang factor applied"
    )
    lang_factor_source: Optional[str] = Field(
        None,
        description="Source of lang factor"
    )
    
    # Provenance
    cost_sources: List[CostProvenance] = Field(
        default_factory=list,
        description="All cost data sources used"
    )
    
    # Confidence
    overall_confidence: Literal["high", "medium", "low"] = Field(
        "medium",
        description="Overall confidence in cost estimate"
    )
    
    # Currency and date
    currency: str = Field("USD", description="Currency")
    cost_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date of cost estimate"
    )


class AffectedEntity(BaseModel):
    """
    Entity affected by a change.
    """
    
    entity_id: str
    entity_name: str
    entity_type: str
    
    # Nature of impact
    impact_type: Literal[
        "capacity_change",
        "replacement_required",
        "modification_required",
        "no_change"
    ]
    impact_description: str
    
    # Cost impact
    capex_delta: float = Field(
        0.0,
        description="Change in CAPEX for this entity"
    )
    opex_delta_annual: float = Field(
        0.0,
        description="Change in annual OPEX"
    )
    
    # Confidence
    confidence: Literal["high", "medium", "low"] = Field(
        "medium",
        description="Confidence in impact assessment"
    )


class DownstreamImpact(BaseModel):
    """
    Analysis of downstream impacts of a change.
    
    This is a CORE USP feature - automatically analyzing how changing
    one piece of equipment affects everything downstream.
    """
    
    # Summary
    total_entities_analyzed: int = Field(
        0,
        description="Number of downstream entities analyzed"
    )
    entities_affected: int = Field(
        0,
        description="Number of entities impacted"
    )
    
    # Detailed impacts
    affected_entities: List[AffectedEntity] = Field(
        default_factory=list,
        description="List of affected entities with impact details"
    )
    
    # Cost summary
    total_capex_delta: float = Field(
        0.0,
        description="Total downstream CAPEX impact"
    )
    total_opex_delta_annual: float = Field(
        0.0,
        description="Total annual OPEX impact"
    )
    
    # Analysis metadata
    analysis_method: Optional[str] = Field(
        None,
        description="Method used for impact analysis"
    )
    analysis_assumptions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assumptions used in analysis"
    )
    analysis_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When analysis was performed"
    )
    
    # Confidence
    overall_confidence: Literal["high", "medium", "low"] = Field(
        "medium",
        description="Overall confidence in impact assessment"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about the analysis"
    )


class NPVAnalysis(BaseModel):
    """
    Net present value analysis for an option.
    """
    
    # Inputs
    initial_capex: float
    annual_opex: float
    annual_revenue_benefit: float = Field(
        0.0,
        description="Annual revenue benefit (e.g., from increased throughput)"
    )
    discount_rate: float = Field(
        0.10,
        description="Discount rate"
    )
    project_life_years: int = Field(
        20,
        description="Project life in years"
    )
    
    # Outputs
    npv: float = Field(
        ...,
        description="Net present value"
    )
    irr: Optional[float] = Field(
        None,
        description="Internal rate of return"
    )
    payback_years: Optional[float] = Field(
        None,
        description="Simple payback period in years"
    )
    
    # Sensitivity
    npv_at_discount_rates: Dict[str, float] = Field(
        default_factory=dict,
        description="NPV at different discount rates"
    )
    
    # Cash flow
    annual_cash_flows: List[float] = Field(
        default_factory=list,
        description="Annual cash flows"
    )
    cumulative_cash_flows: List[float] = Field(
        default_factory=list,
        description="Cumulative cash flows"
    )


class CostComparisonResponse(BaseModel):
    """
    Response for cost comparison endpoint.
    
    Simplified view for charts and visualizations.
    """
    
    scenario_id: str
    options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of options with key cost metrics"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "scenario_id": "507f1f77bcf86cd799439012",
                "options": [
                    {
                        "option_id": "507f1f77bcf86cd799439013",
                        "name": "Metso Superior MKII 54-75",
                        "purchase_cost": 2750000,
                        "installed_cost": 9625000,
                        "total_capex": 9625000,
                        "downstream_capex": 1625000,
                        "total_capex_with_downstream": 11250000,
                        "annual_opex": 450000,
                        "npv": 15000000
                    }
                ]
            }
        }