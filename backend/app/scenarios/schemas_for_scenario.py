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

    # target: TargetModel
    # constraints: Optional[ConstraintsModel] = None

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
    goal: Optional[str] = None
    change_type: Optional[str] = None
    status: Optional[str] = None
    compute_state: Optional[str] = None
    # target: Optional[Dict[str, Any]] = None
    # constraints: Optional[Dict[str, Any]] = None
    cost_estimate_id: Optional[str] = None

    class Config:
        extra = "forbid"


class ScenarioInDB(ScenarioBase):
    """Scenario model as stored in database"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioResponse(ScenarioInDB):
    """Scenario model for API responses"""

    pass
