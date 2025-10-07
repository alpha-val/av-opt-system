"""
Option domain models.

An Option represents a specific equipment/design selection that satisfies
a Scenario's requirements.

For example, if a Scenario asks "what if we change crusher product size to 9 inches?",
an Option might be:
- Model: 54-75 Gyratory Crusher
- Purchase Cost: $4.382M (2015)
- Escalated Cost: $6.24M (2025)
- Installed Cost (with lang factors): $26.3M

Multiple Options are generated per Scenario and compared.
"""

from pydantic import Field
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime

from .base import BaseDBModel, PyObjectId


class EquipmentSelection(BaseDBModel):
    """
    Details of selected equipment.

    Contains all relevant specifications and sourcing information.
    """

    equipment_type: str = Field(
        ..., description="Type of equipment (e.g., 'gyratory_crusher', 'jaw_crusher')"
    )
    manufacturer: Optional[str] = Field(None, description="Equipment manufacturer")
    model: str = Field(..., description="Model designation (e.g., '54-75', '60x90')")

    # Capacity and specifications
    capacity_tph: Optional[float] = Field(
        None, description="Rated capacity in tonnes per hour"
    )
    power_kw: Optional[float] = Field(None, description="Installed power in kilowatts")
    specifications: Dict[str, Any] = Field(
        default_factory=dict, description="Additional specifications"
    )

    # Sizing rationale
    capacity_margin_pct: Optional[float] = Field(
        None, description="Capacity margin (% over required throughput)"
    )
    suitability_score: Optional[float] = Field(
        None, description="Suitability score (0-100)"
    )

    # Source tracking
    sizing_source_table_id: Optional[PyObjectId] = Field(
        None, description="ID of sizing table used"
    )
    sizing_source_row: Optional[str] = Field(
        None, description="Row reference in sizing table"
    )


class CostData(BaseDBModel):
    """
    Cost data with full provenance.

    Critical: Tracks WHERE the cost came from and HOW it was calculated.
    This is essential for audit trails and validation.
    """

    # Base cost
    purchase_cost_base: float = Field(..., description="Base equipment purchase cost")
    purchase_cost_currency: str = Field("USD", description="Currency")
    purchase_cost_year: int = Field(..., description="Year of base cost")

    # Escalated cost
    escalation_index: str = Field(
        ..., description="Index used for escalation (e.g., 'CEPCI', 'CPI')"
    )
    escalation_multiplier: float = Field(
        ..., description="Escalation multiplier applied"
    )
    purchase_cost_escalated: float = Field(..., description="Escalated purchase cost")
    escalation_target_year: int = Field(..., description="Year escalated to")

    # Installed cost
    lang_factor_category: str = Field(..., description="Lang factor category applied")
    equipment_multiplier: float = Field(
        ..., description="Total equipment multiplier (e.g., 3.5)"
    )
    installed_equipment_cost: float = Field(..., description="Installed equipment cost")

    # WBS breakdown
    wbs_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list, description="Breakdown by WBS code"
    )

    # Total
    total_installed_cost: float = Field(..., description="Total installed cost (TIC)")

    # Provenance (CRITICAL)
    cost_source_table_id: Optional[PyObjectId] = Field(
        None, description="ID of cost table used"
    )
    cost_source_row: Optional[str] = Field(
        None, description="Row reference in cost table"
    )
    lang_factor_source_table_id: Optional[PyObjectId] = Field(
        None, description="ID of lang factor table used"
    )
    escalation_source_table_id: Optional[PyObjectId] = Field(
        None, description="ID of escalation index table used"
    )

    # Confidence
    confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence level in cost estimate"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="List of assumptions made"
    )


class DownstreamImpact(BaseDBModel):
    """
    Impact on downstream equipment/processes.

    This is a KEY DIFFERENTIATOR that ChatGPT missed.

    Example:
        If primary crusher product size increases from 7" to 9":
        - Secondary crushing: Load DECREASES (cost savings)
        - Grinding circuit: Load INCREASES (cost increase)
        - Conveyors: May need upsizing (cost increase)
    """

    stage: str = Field(
        ...,
        description="Affected stage (e.g., 'secondary_crushing', 'grinding_circuit')",
    )
    impact_type: Literal[
        "increased_load", "reduced_load", "no_change", "eliminated"
    ] = Field(..., description="Type of impact")

    # Quantitative impacts
    work_change_pct: Optional[float] = Field(
        None, description="Change in work/duty (%)"
    )
    capacity_change_pct: Optional[float] = Field(
        None, description="Change in capacity requirement (%)"
    )

    # Cost impacts
    capex_delta: float = Field(
        0.0, description="Change in capital cost (negative = savings)"
    )
    opex_annual_delta: float = Field(
        0.0, description="Change in annual OPEX (negative = savings)"
    )

    # Explanation
    rationale: str = Field(..., description="Explanation of impact")
    confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence in impact estimate"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Assumptions made in analysis"
    )


class OPEXEstimate(BaseDBModel):
    """
    Annual operating cost estimate.
    """

    # Energy
    power_consumption_kwh_per_year: Optional[float] = Field(
        None, description="Annual power consumption"
    )
    power_cost_usd_per_year: Optional[float] = Field(
        None, description="Annual power cost"
    )
    power_rate_usd_per_kwh: Optional[float] = Field(
        None, description="Electricity rate used"
    )

    # Maintenance
    maintenance_cost_usd_per_year: Optional[float] = Field(
        None, description="Annual maintenance cost"
    )

    # Labor
    labor_cost_usd_per_year: Optional[float] = Field(
        None, description="Annual labor cost"
    )

    # Consumables
    consumables_cost_usd_per_year: Optional[float] = Field(
        None, description="Annual consumables cost"
    )

    # Total
    total_opex_per_year: float = Field(..., description="Total annual OPEX")

    # Provenance
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")


class NPVAnalysis(BaseDBModel):
    """
    Net Present Value analysis.
    """

    years: int = Field(..., description="Analysis period (years)")
    discount_rate: float = Field(..., description="Discount rate (e.g., 0.08 = 8%)")

    # Cash flows
    initial_capex: float = Field(..., description="Initial capital expenditure")
    annual_opex: float = Field(..., description="Annual operating cost")
    annual_revenue: Optional[float] = Field(
        None, description="Annual revenue (if applicable)"
    )

    # Results
    npv: float = Field(..., description="Net Present Value")
    irr: Optional[float] = Field(None, description="Internal Rate of Return")
    payback_period_years: Optional[float] = Field(None, description="Payback period")

    # Sensitivity
    sensitivity: Optional[Dict[str, Any]] = Field(
        None, description="Sensitivity analysis results"
    )


class Option(BaseDBModel):
    """
    Complete option model.

    Represents a fully costed alternative for a scenario.
    """

    # Core identification
    project_id: PyObjectId = Field(..., description="Parent project ID")
    scenario_id: PyObjectId = Field(..., description="Parent scenario ID")
    name: str = Field(..., description="Option name")
    description: Optional[str] = Field(None, description="Option description")

    # Selection status
    selected: bool = Field(False, description="Whether this option is selected")
    rank: Optional[int] = Field(None, description="Ranking (1=best)")

    # Equipment selection
    equipment: EquipmentSelection = Field(..., description="Selected equipment details")

    # Design parameters
    design_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Design parameters for this option"
    )

    # Cost analysis
    cost_data: CostData = Field(..., description="Complete cost breakdown")

    # Downstream impacts (CRITICAL - USP feature)
    downstream_impacts: List[DownstreamImpact] = Field(
        default_factory=list, description="Impacts on downstream equipment"
    )
    total_downstream_capex_delta: float = Field(
        0.0, description="Total downstream CAPEX impact"
    )

    # OPEX
    opex: Optional[OPEXEstimate] = Field(None, description="Annual OPEX estimate")

    # NPV
    npv_analysis: Optional[NPVAnalysis] = Field(None, description="NPV analysis")

    # Overall metrics
    total_capex: float = Field(..., description="Total CAPEX (equipment + downstream)")
    total_opex_annual: Optional[float] = Field(None, description="Total annual OPEX")

    # Validation
    feasibility_score: Optional[float] = Field(
        None, description="Feasibility score (0-100)"
    )
    validation_warnings: List[str] = Field(
        default_factory=list, description="Validation warnings"
    )

    # Metadata
    created_by: Optional[str] = Field(None, description="User who created option")
    rationale: Optional[str] = Field(None, description="Rationale for this option")


class OptionSummary(BaseDBModel):
    """
    Lightweight option summary for list views.
    """

    id: PyObjectId = Field(..., alias="_id")
    scenario_id: PyObjectId
    name: str
    selected: bool
    rank: Optional[int]

    # Key metrics
    model: str = Field(..., description="Equipment model")
    total_capex: float
    total_opex_annual: Optional[float]

    created_at: datetime
