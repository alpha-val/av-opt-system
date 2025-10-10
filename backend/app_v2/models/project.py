"""
Project domain models.

A Project is the top-level container for all mining project data:
- Base case entities (existing equipment, flowsheet)
- Scenarios (what-if analyses)
- Options (alternative designs)
- Reference data (cost tables, sizing tables, lang factors)
"""

from pydantic import Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

from .base import BaseDBModel, PyObjectId


class ProjectMetadata(BaseDBModel):
    """
    Project metadata and classification.

    Contains high-level project information for filtering and reporting.
    """

    # Location
    country: Optional[str] = Field(None, description="Country")
    region: Optional[str] = Field(None, description="Region/state/province")
    site_name: Optional[str] = Field(None, description="Site name")
    coordinates: Optional[Dict[str, float]] = Field(
        None, description="GPS coordinates {'lat': float, 'lon': float}"
    )

    # Project classification
    project_stage: Literal[
        "conceptual",
        "pre_feasibility",
        "feasibility",
        "basic_engineering",
        "detailed_engineering",
        "construction",
        "operations",
    ] = Field("conceptual", description="Project development stage")

    commodity: Optional[str] = Field(
        None, description="Primary commodity (e.g., 'copper', 'gold', 'iron_ore')"
    )
    ore_type: Optional[str] = Field(
        None, description="Ore type (e.g., 'oxide', 'sulfide', 'mixed')"
    )

    # Scale
    design_capacity_tpd: Optional[float] = Field(
        None, description="Design capacity in tonnes per day"
    )
    design_capacity_mtpa: Optional[float] = Field(
        None, description="Design capacity in million tonnes per annum"
    )

    # Economic
    mine_life_years: Optional[int] = Field(
        None, description="Expected mine life in years"
    )
    estimated_capex_usd: Optional[float] = Field(
        None, description="Estimated total CAPEX (USD)"
    )

    # Reference currency and year
    currency: str = Field("USD", description="Currency for costs")
    cost_basis_year: Optional[int] = Field(
        None, description="Cost basis year for project estimates"
    )


class ProjectSettings(BaseDBModel):
    """
    Project-specific settings and preferences.

    Controls behavior of analysis and estimation for this project.
    """

    # Cost estimation defaults
    default_escalation_index: str = Field(
        "CEPCI", description="Default cost escalation index"
    )
    default_lang_factor_source: Optional[str] = Field(
        None, description="Default source for lang factors"
    )

    # Analysis settings
    enable_downstream_analysis: bool = Field(
        True, description="Enable downstream impact analysis"
    )
    enable_opex_estimation: bool = Field(True, description="Enable OPEX estimation")
    enable_npv_calculation: bool = Field(False, description="Enable NPV calculation")

    # Default NPV parameters
    default_discount_rate: float = Field(
        0.08, description="Default discount rate (e.g., 0.08 = 8%)"
    )
    default_analysis_period_years: int = Field(
        20, description="Default analysis period for NPV"
    )

    # Capacity margins
    min_capacity_margin_pct: float = Field(
        10.0, description="Minimum capacity margin required (%)"
    )
    max_capacity_margin_pct: float = Field(
        50.0, description="Maximum acceptable capacity margin (%)"
    )

    # Power costs (for OPEX estimation)
    power_cost_usd_per_kwh: Optional[float] = Field(
        None, description="Electricity cost (USD/kWh)"
    )
    operating_hours_per_year: int = Field(
        8760, description="Operating hours per year (default: 24/7 = 8760)"
    )

    # Validation
    require_cost_validation: bool = Field(
        True, description="Require cost data validation before generating options"
    )

    # Units
    use_metric: bool = Field(True, description="Use metric units (vs imperial)")


class BaseCaseSnapshot(BaseDBModel):
    """
    Snapshot of base case (existing/planned) configuration.

    This is the reference point against which all scenarios are compared.
    """

    snapshot_date: datetime = Field(
        default_factory=datetime.utcnow, description="When snapshot was taken"
    )

    # Key parameters
    primary_crushing_p80_in: Optional[float] = Field(
        None, description="Primary crusher product P80 (inches)"
    )
    throughput_tph: Optional[float] = Field(
        None, description="Design throughput (tonnes per hour)"
    )

    # Equipment summary
    entity_ids: List[PyObjectId] = Field(
        default_factory=list, description="IDs of entities in base case"
    )
    entity_count_by_type: Dict[str, int] = Field(
        default_factory=dict, description="Count of entities by type"
    )

    # Cost summary
    total_capex_base: Optional[float] = Field(
        None, description="Total CAPEX of base case"
    )
    total_opex_annual_base: Optional[float] = Field(
        None, description="Total annual OPEX of base case"
    )

    # Description
    description: Optional[str] = Field(
        None, description="Description of base case configuration"
    )


class DataInventory(BaseDBModel):
    """
    Inventory of data available for this project.

    Helps users understand what data has been uploaded and is available
    for analysis.
    """

    # Tables
    cost_tables: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of cost tables with metadata"
    )
    sizing_tables: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of sizing tables with metadata"
    )
    lang_factor_tables: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of lang factor tables with metadata"
    )
    escalation_indices: List[str] = Field(
        default_factory=list, description="Available escalation indices"
    )

    # Entities
    entity_count: int = Field(0, description="Total number of entities")
    entity_types: List[str] = Field(
        default_factory=list, description="Types of entities in project"
    )

    # Scenarios
    scenario_count: int = Field(0, description="Number of scenarios")
    option_count: int = Field(0, description="Total number of options")

    # Last updated
    last_data_upload: Optional[datetime] = Field(
        None, description="When data was last uploaded"
    )


class Project(BaseDBModel):
    """
    Complete project model.

    The top-level container for all project data.
    """

    # Basic information
    name: str = Field(..., description="Project name")
    code: Optional[str] = Field(None, description="Project code/identifier")
    description: Optional[str] = Field(None, description="Project description")

    # Metadata
    metadata: ProjectMetadata = Field(
        default_factory=ProjectMetadata, description="Project metadata"
    )

    # Settings
    settings: ProjectSettings = Field(
        default_factory=ProjectSettings, description="Project settings"
    )

    # Base case
    base_case: Optional[BaseCaseSnapshot] = Field(
        None, description="Base case configuration snapshot"
    )

    # Data inventory
    data_inventory: DataInventory = Field(
        default_factory=DataInventory, description="Inventory of available data"
    )

    # Status
    status: Literal["active", "archived", "template"] = Field(
        "active", description="Project status"
    )

    # Access control
    owner_id: Optional[str] = Field(None, description="User ID of project owner")
    team_member_ids: List[str] = Field(
        default_factory=list, description="User IDs of team members with access"
    )
    visibility: Literal["private", "team", "public"] = Field(
        "private", description="Project visibility"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for organization-specific data"
    )


class ProjectSummary(BaseDBModel):
    """
    Lightweight project summary for list views.

    Contains only essential fields for displaying project lists.
    """

    id: PyObjectId = Field(..., alias="_id")
    name: str
    code: Optional[str]
    status: str

    # Key metrics
    scenario_count: int = Field(0, description="Number of scenarios")
    option_count: int = Field(0, description="Total number of options")

    # Metadata
    commodity: Optional[str]
    design_capacity_mtpa: Optional[float]
    project_stage: str

    # Dates
    created_at: datetime
    updated_at: datetime

    # Access
    owner_id: Optional[str]
