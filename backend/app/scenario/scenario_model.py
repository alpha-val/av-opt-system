from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid

# ============================================================================
# SCENARIO MODELS
# ============================================================================


class TargetModel(BaseModel):
    """Target for a scenario"""

    metric: str  # "throughput", "cost", "quality_score"
    value: float  # 10
    unit: str  # "%", "USD", "units/day"
    baseline: Optional[float] = None  # current value from base case
    target_absolute: Optional[float] = None  # calculated target


class ConstraintsModel(BaseModel):
    """Constraints for scenario"""

    budget_capex: Optional[float] = None
    budget_opex: Optional[float] = None
    timeline_months: Optional[int] = None
    use_existing_equipment_only: Optional[bool] = False
    # Allow additional custom constraints
    additional: Optional[Dict[str, Any]] = None


class ScenarioBase(BaseModel):
    """Base scenario model"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: str
    base_case_reference_id: Optional[str] = None

    change_type: Literal["equipment", "process", "capacity", "location", "technology"]
    goal: Literal[
        "increase_production",
        "reduce_cost",
        "improve_quality",
        "change_technology",
        "other",
    ]

    target: TargetModel
    constraints: Optional[ConstraintsModel] = None

    status: Literal["draft", "analyzing", "ready", "archived"] = "draft"
    compute_state: Optional[
        Literal["idle", "queued", "running", "failed", "succeeded"]
    ] = "idle"

    option_count: int = 0


class ScenarioCreate(ScenarioBase):
    """Model for creating a scenario"""

    pass


class ScenarioUpdate(BaseModel):
    """Model for updating a scenario"""

    name: Optional[str] = None
    description: Optional[str] = None
    change_type: Optional[
        Literal["equipment", "process", "capacity", "location", "technology"]
    ] = None
    goal: Optional[
        Literal[
            "increase_production",
            "reduce_cost",
            "improve_quality",
            "change_technology",
            "other",
        ]
    ] = None
    target: Optional[TargetModel] = None
    constraints: Optional[ConstraintsModel] = None
    status: Optional[Literal["draft", "analyzing", "ready", "archived"]] = None
    compute_state: Optional[
        Literal["idle", "queued", "running", "failed", "succeeded"]
    ] = None
    option_count: Optional[int] = None


class ScenarioInDB(ScenarioBase):
    """Scenario model as stored in database"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioResponse(ScenarioInDB):
    """Scenario model for API responses"""

    pass


# ============================================================================
# OPTION MODELS
# ============================================================================


class ValueUnit(BaseModel):
    """Generic value with unit"""

    value: Optional[float] = None
    unit: Optional[str] = None


class EquipmentChange(BaseModel):
    """Equipment change specification"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: Literal["add", "resize", "replace", "retune"]
    ref_id: Optional[str] = None  # equipment catalog id
    entity_id: Optional[str] = None  # link to base case entity
    from_spec: Optional[ValueUnit] = Field(None, alias="from")
    to: Optional[ValueUnit] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class MaterialChange(BaseModel):
    """Material change specification"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: Literal["add", "replace", "adjust_rate"]
    ref_id: Optional[str] = None
    entity_id: Optional[str] = None
    from_spec: Optional[ValueUnit] = Field(None, alias="from")
    to: Optional[ValueUnit] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class ProcessChange(BaseModel):
    """Process change specification"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    step_id: Optional[str] = None
    change_type: str  # "debottleneck", "re-sequence", "setpoint"
    details: Optional[str] = None


class LayoutChange(BaseModel):
    """Layout change specification"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    details: Optional[str] = None


class LocationChange(BaseModel):
    """Location change specification"""

    region_code: Optional[str] = None


class OptionSpecs(BaseModel):
    """Specifications for an option"""

    equipment_changes: Optional[List[EquipmentChange]] = None
    material_changes: Optional[List[MaterialChange]] = None
    process_changes: Optional[List[ProcessChange]] = None
    layout_changes: Optional[List[LayoutChange]] = None
    location_change: Optional[LocationChange] = None


class CostEstimate(BaseModel):
    """Cost estimate with optional breakdown"""

    value: float
    currency: str = "USD"
    breakdown: Optional[Dict[str, Any]] = None


class TimelineEstimate(BaseModel):
    """Timeline estimate"""

    value: float
    unit: Literal["months", "weeks"] = "months"


class OptionEstimates(BaseModel):
    """Estimates for an option"""

    capex: Optional[CostEstimate] = None
    opex_per_year: Optional[CostEstimate] = None
    timeline: Optional[TimelineEstimate] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None


class OptionDeltas(BaseModel):
    """Changes vs base case"""

    throughput_change: Optional[ValueUnit] = None
    cost_change: Optional[ValueUnit] = None
    # Allow additional custom deltas
    additional: Optional[Dict[str, Any]] = None


class OptionBase(BaseModel):
    """Base option model"""

    scenario_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    strategy: Optional[
        Literal["lowest_capex", "lowest_opex", "fastest", "balanced", "custom"]
    ] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)

    specs: Optional[OptionSpecs] = None
    estimates: Optional[OptionEstimates] = None
    deltas: Optional[OptionDeltas] = None

    selected: bool = False


class OptionCreate(OptionBase):
    """Model for creating an option"""

    pass


class OptionUpdate(BaseModel):
    """Model for updating an option"""

    name: Optional[str] = None
    description: Optional[str] = None
    strategy: Optional[
        Literal["lowest_capex", "lowest_opex", "fastest", "balanced", "custom"]
    ] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    specs: Optional[OptionSpecs] = None
    estimates: Optional[OptionEstimates] = None
    deltas: Optional[OptionDeltas] = None
    selected: Optional[bool] = None


class OptionInDB(OptionBase):
    """Option model as stored in database"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OptionResponse(OptionInDB):
    """Option model for API responses"""

    pass


# ============================================================================
# COMBINED RESPONSE MODELS
# ============================================================================


class ScenarioWithOptions(ScenarioResponse):
    """Scenario with its options"""

    options: List[OptionResponse] = []


class ScenarioListResponse(BaseModel):
    """Response for list of scenarios"""

    scenarios: List[ScenarioResponse]
    total: int
