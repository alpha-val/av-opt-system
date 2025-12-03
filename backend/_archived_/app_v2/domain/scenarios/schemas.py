"""
Pydantic schemas for scenario analysis.

Defines all data models for scenario creation, analysis, resizing, and reporting.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Core Scenario Schemas
# ============================================================================

class GlobalObjective(BaseModel):
    """Global objective specification for a scenario."""
    
    goal_type: Literal["increase_production", "reduce_capex", "improve_quality", "change_technology", "other"]
    change_direction: Literal["increase", "decrease"]
    change_magnitude: float  # Percentage or absolute value
    change_unit: str  # "%", "USD", "tpd", "gpm", etc.
    description: Optional[str] = None


class LocalObjective(BaseModel):
    """Local objective - entity-parameter pair relevant to scenario."""
    
    entity_id: str
    entity_name: str
    entity_type: str
    parameter: str  # e.g., "flow_rate", "capacity", "power"
    relevance_score: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    base_value: Optional[Any] = None
    base_unit: Optional[str] = None
    rationale: Optional[str] = None
    evidence: Optional[List[str]] = None


class UserConstraint(BaseModel):
    """User-provided constraint for entity attributes."""
    
    entity_id: str
    parameter: str
    constraint_type: Literal["FIXED", "VARIABLE"]
    value: Optional[Any] = None  # For FIXED constraints
    min_value: Optional[Any] = None  # For VARIABLE constraints
    max_value: Optional[Any] = None  # For VARIABLE constraints
    unit: Optional[str] = None


class ScenarioBase(BaseModel):
    """Base scenario model with core fields."""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: str
    base_case_reference_id: Optional[str] = None  # Reference to base case document
    
    # Global objective
    global_objective: Optional[GlobalObjective] = None
    
    # Status tracking
    status: Literal["draft", "analyzing", "ready", "archived"] = "draft"
    compute_state: Optional[Literal["idle", "queued", "running", "failed", "succeeded"]] = "idle"
    
    # Metadata
    created_by: Optional[str] = None
    option_count: int = 0


class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario."""
    pass


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario (partial updates allowed)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    global_objective: Optional[GlobalObjective] = None
    status: Optional[Literal["draft", "analyzing", "ready", "archived"]] = None
    compute_state: Optional[Literal["idle", "queued", "running", "failed", "succeeded"]] = None
    base_case_reference_id: Optional[str] = None
    
    class Config:
        extra = "forbid"


class ScenarioOut(ScenarioBase):
    """Schema for scenario output with all fields."""
    
    id: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Analysis Schemas
# ============================================================================

class Assumption(BaseModel):
    """Assumption extracted from base case."""
    
    text: str
    assumption_type: Literal["Design", "Operational", "Market", "Environmental"]
    refs: Optional[List[str]] = None  # Section/page references


class Policy(BaseModel):
    """Policy or code/standard extracted from base case."""
    
    text: str
    domain: Literal["Safety", "Code", "Cost", "Procurement", "Quality", "Environmental"]
    refs: Optional[List[str]] = None


class Constraint(BaseModel):
    """Constraint extracted from base case."""
    
    constraint: str
    basis: Literal["Physical", "Regulatory", "Budgetary", "Schedule", "Availability"]
    refs: Optional[List[str]] = None


class ScenarioAnalysis(BaseModel):
    """Results from LLM analysis of relevant entities."""
    
    scenario_summary: Optional[str] = None  # Summary of base case relevant to scenario
    local_objectives: List[LocalObjective] = []
    assumptions: List[Assumption] = []
    policies: List[Policy] = []
    constraints: List[Constraint] = []
    related_sections: List[str] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    analysis_timestamp: Optional[datetime] = None


# ============================================================================
# Resizing Schemas
# ============================================================================

class ResizedParameter(BaseModel):
    """A parameter that has been resized."""
    
    entity_id: str
    parameter: str
    original_value: Any
    resized_value: Any
    unit: Optional[str] = None
    calculation_method: str  # e.g., "percentage_scaling", "cost_exponent", "linear"
    calculation_details: Optional[Dict[str, Any]] = None  # e.g., {"exponent": 0.6, "scale_factor": 1.08}
    confidence: float = Field(ge=0.0, le=1.0)


class SystemResizing(BaseModel):
    """Results from system resizing calculations."""
    
    resized_parameters: List[ResizedParameter] = []
    resizing_timestamp: Optional[datetime] = None
    calculation_summary: Optional[str] = None


# ============================================================================
# Cost Estimation Schemas
# ============================================================================

class CostGuideline(BaseModel):
    """Cost guideline extracted from reference data."""
    
    item: str
    base_cost_value: Optional[float] = None
    currency: Optional[str] = None
    basis_year: Optional[int] = None
    scaling_rule: Optional[str] = None  # e.g., "C2 = C1 * (S2/S1)^0.6"
    risk_notes: Optional[str] = None
    estimation_note: Optional[str] = None


class CostEstimationData(BaseModel):
    """Prepared cost estimation data."""
    
    cost_guidelines: List[CostGuideline] = []
    cost_drivers: List[Dict[str, Any]] = []  # Entities/parameters that drive costs
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    cost_estimate_id: Optional[str] = None  # If estimate was generated
    prepared_timestamp: Optional[datetime] = None


# ============================================================================
# Recommendation Schemas
# ============================================================================

class ExpectedEffect(BaseModel):
    """Expected effect of an approach option."""
    
    metric: str  # "throughput", "capex", "opex", "quality"
    direction: Literal["increase", "decrease", "neutral"]
    estimate_pct: Optional[str] = None  # e.g., "8%", "+5%"
    notes: Optional[str] = None


class ApproachOption(BaseModel):
    """An approach option for achieving the scenario goal."""
    
    option_id: str
    title: str
    rationale: str
    expected_effects: Dict[str, ExpectedEffect] = {}  # Keyed by metric
    dependencies: List[str] = []  # e.g., "TDH validation", "electrical capacity"
    refs: Optional[List[str]] = None
    feasibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    impact_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ScenarioRecommendation(BaseModel):
    """System recommendation with approach options."""
    
    approach_options: List[ApproachOption] = []
    recommended_option_id: Optional[str] = None
    recommendation_summary: Optional[str] = None
    uncertainties: List[Dict[str, Any]] = []  # Gaps and suggested actions
    recommendation_timestamp: Optional[datetime] = None


# ============================================================================
# Report Schemas
# ============================================================================

class ScenarioReport(BaseModel):
    """Formatted report data for scenario."""
    
    format: Literal["json", "markdown"] = "json"
    content: str  # Formatted report content
    sections: Dict[str, Any] = {}  # Structured sections
    generated_timestamp: Optional[datetime] = None


# ============================================================================
# Complete Scenario with All Data
# ============================================================================

class ScenarioWithAnalysis(ScenarioOut):
    """Complete scenario with all analysis data."""
    
    analysis: Optional[ScenarioAnalysis] = None
    resizing: Optional[SystemResizing] = None
    cost_estimation: Optional[CostEstimationData] = None
    recommendation: Optional[ScenarioRecommendation] = None
    user_constraints: List[UserConstraint] = []

