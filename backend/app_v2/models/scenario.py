"""
Scenario domain models.

A Scenario represents a "what-if" question:
- What if we change crusher product size from 7" to 9"?
- What if we increase throughput by 20%?
- What if we use a jaw crusher instead of a gyratory?

Scenarios generate multiple Options (alternative equipment selections)
that are then costed and compared.
"""

from pydantic import Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

from .base import BaseDBModel, PyObjectId


class ParameterChange(BaseDBModel):
    """
    Represents a single parameter change in a scenario.

    Example:
        ParameterChange(
            parameter="crusher_product_size",
            from_value=7.0,
            to_value=9.0,
            unit="inches",
            affected_entity_ids=["507f1f77bcf86cd799439011"],
            rationale="Increase product size to reduce crushing load"
        )

    This is the KEY data structure that was missing in your original code.
    It captures WHAT changed, not just the goal.
    """

    parameter: str = Field(
        ..., description="Parameter name (e.g., 'crusher_product_size', 'throughput')"
    )
    from_value: float = Field(..., description="Original/baseline value")
    to_value: float = Field(..., description="New target value")
    unit: str = Field(..., description="Unit of measurement (e.g., 'inches', 'tph')")
    affected_entity_ids: List[PyObjectId] = Field(
        default_factory=list, description="IDs of entities affected by this change"
    )
    rationale: Optional[str] = Field(None, description="Why this change was made")


class ScenarioTarget(BaseDBModel):
    """
    Target metrics for the scenario.

    Example:
        ScenarioTarget(
            metric="TIC",
            operator="minimize",
            target_value=50000000,
            unit="USD"
        )
    """

    metric: str = Field(
        ..., description="Target metric (e.g., 'TIC', 'OPEX', 'NPV', 'throughput')"
    )
    operator: Literal["minimize", "maximize", "target"] = Field(
        "minimize", description="Optimization direction"
    )
    target_value: Optional[float] = Field(
        None, description="Specific target value (for 'target' operator)"
    )
    unit: str = Field(..., description="Unit of measurement")
    priority: int = Field(
        1, description="Priority (1=highest) for multi-objective optimization"
    )


class ScenarioConstraints(BaseDBModel):
    """
    Constraints that options must satisfy.

    Example:
        ScenarioConstraints(
            max_capex_usd=100000000,
            max_timeline_months=24,
            min_throughput_tph=1000,
            use_existing_equipment_only=False,
            technical_constraints=["same_footprint", "no_shutdown_required"]
        )
    """

    max_capex_usd: Optional[float] = Field(
        None, description="Maximum capital expenditure"
    )
    max_opex_annual_usd: Optional[float] = Field(
        None, description="Maximum annual operating expenditure"
    )
    max_timeline_months: Optional[int] = Field(
        None, description="Maximum project timeline"
    )
    min_throughput_tph: Optional[float] = Field(
        None, description="Minimum throughput requirement"
    )
    max_throughput_tph: Optional[float] = Field(
        None, description="Maximum throughput requirement"
    )
    max_feed_size_in: Optional[float] = Field(
        None, description="Maximum feed size constraint"
    )
    use_existing_equipment_only: bool = Field(
        False, description="Whether to only use existing equipment"
    )
    technical_constraints: List[str] = Field(
        default_factory=list, description="List of technical constraints"
    )


class AnalysisConfiguration(BaseDBModel):
    """
    Configuration for analysis to perform on this scenario.

    Controls which analyses are run:
    - Downstream impact analysis
    - OPEX estimation
    - NPV calculation
    - Sensitivity analysis
    """

    include_downstream_impact: bool = Field(
        True, description="Analyze impact on downstream equipment"
    )
    include_opex: bool = Field(True, description="Calculate annual OPEX")
    calculate_npv: bool = Field(False, description="Calculate Net Present Value")
    npv_years: int = Field(20, description="NPV calculation period (years)")
    discount_rate: float = Field(
        0.08, description="Discount rate for NPV (e.g., 0.08 = 8%)"
    )
    sensitivity_analysis: bool = Field(
        False, description="Perform sensitivity analysis"
    )

    # Cost estimation configuration
    cost_estimation_method: Literal["factored", "detailed"] = Field(
        "factored", description="Cost estimation method"
    )
    escalation_index: str = Field("CEPCI", description="Cost escalation index to use")
    lang_factor_source: Optional[str] = Field(
        None, description="Source document/table ID for lang factors"
    )


class Scenario(BaseDBModel):
    """
    Complete scenario model.

    A scenario represents a complete "what-if" analysis with:
    - What changed (parameter_changes)
    - What we're trying to achieve (targets)
    - What constraints must be met (constraints)
    - How to analyze it (analysis_config)
    - Data lineage (source_entity_ids, source_table_ids)
    """

    # Core identification
    project_id: PyObjectId = Field(..., description="Parent project ID")
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")

    # Status tracking
    status: Literal["draft", "analyzing", "ready", "archived"] = Field(
        "draft", description="Scenario status"
    )
    compute_state: Optional[
        Literal["idle", "queued", "running", "completed", "failed"]
    ] = Field(None, description="Computation state for async processing")

    # What changed (CRITICAL - missing in original)
    parameter_changes: List[ParameterChange] = Field(
        default_factory=list, description="List of parameter changes from base case"
    )

    # Goals and constraints
    targets: List[ScenarioTarget] = Field(
        default_factory=list, description="Target metrics to optimize"
    )
    constraints: ScenarioConstraints = Field(
        default_factory=ScenarioConstraints,
        description="Constraints that options must satisfy",
    )

    # Analysis configuration
    analysis_config: AnalysisConfiguration = Field(
        default_factory=AnalysisConfiguration, description="Analysis configuration"
    )

    # Data lineage (CRITICAL - for provenance tracking)
    source_entity_ids: List[PyObjectId] = Field(
        default_factory=list, description="IDs of entities used for this scenario"
    )
    source_table_ids: List[PyObjectId] = Field(
        default_factory=list, description="IDs of tables used for this scenario"
    )
    base_case_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of base case data at scenario creation",
    )

    # Results tracking
    option_count: int = Field(0, description="Number of options generated")
    selected_option_id: Optional[PyObjectId] = Field(
        None, description="ID of selected option"
    )

    # Metadata
    created_by: Optional[str] = Field(None, description="User who created scenario")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ScenarioSummary(BaseDBModel):
    """
    Lightweight scenario summary for list views.

    Contains only essential fields for displaying scenario lists.
    """

    id: PyObjectId = Field(..., alias="_id")
    project_id: PyObjectId
    name: str
    status: str
    option_count: int
    created_at: datetime

    # Summary of changes
    parameter_change_summary: str = Field(
        "", description="Human-readable summary of changes"
    )

    # Top-level target
    primary_target: Optional[str] = Field(
        None, description="Primary optimization target"
    )
