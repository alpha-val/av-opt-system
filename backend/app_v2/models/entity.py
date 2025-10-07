"""
Entity domain models.

An Entity represents any physical or logical component in the mining operation:
- Equipment (crushers, mills, conveyors, etc.)
- Materials (ore, reagents, water)
- Infrastructure (buildings, utilities)
- Processes (circuits, unit operations)

Entities are the building blocks that make up:
- Base case configuration
- Scenario alternatives
- Process flowsheets
"""

from pydantic import Field
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime

from .base import BaseDBModel, PyObjectId


class EntitySpecifications(BaseDBModel):
    """
    Generic specifications container.

    Stores equipment-specific technical specifications.
    Each entity type has its own set of relevant specifications.
    """

    # Common specifications (all equipment)
    manufacturer: Optional[str] = Field(None, description="Equipment manufacturer")
    model: Optional[str] = Field(None, description="Model designation")
    serial_number: Optional[str] = Field(None, description="Serial number")

    # Capacity
    capacity: Optional[float] = Field(None, description="Rated capacity")
    capacity_unit: Optional[str] = Field(
        None, description="Capacity unit (tph, m³/h, etc.)"
    )
    capacity_margin_pct: Optional[float] = Field(
        None, description="Capacity margin over design requirement (%)"
    )

    # Power
    power_kw: Optional[float] = Field(None, description="Installed power (kW)")
    voltage: Optional[str] = Field(None, description="Operating voltage")

    # Physical dimensions
    length_m: Optional[float] = Field(None, description="Length (meters)")
    width_m: Optional[float] = Field(None, description="Width (meters)")
    height_m: Optional[float] = Field(None, description="Height (meters)")
    weight_kg: Optional[float] = Field(None, description="Weight (kg)")
    footprint_m2: Optional[float] = Field(None, description="Footprint area (m²)")

    # Additional specifications (flexible)
    custom_specs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom specifications specific to entity type",
    )


class CrusherSpecifications(EntitySpecifications):
    """
    Crusher-specific specifications.
    """

    # Feed and product
    feed_opening_in: Optional[float] = Field(
        None, description="Feed opening size (inches)"
    )
    closed_side_setting_in: Optional[float] = Field(
        None, description="Closed side setting (inches)"
    )
    min_p80_in: Optional[float] = Field(
        None, description="Minimum product P80 (inches)"
    )
    max_p80_in: Optional[float] = Field(
        None, description="Maximum product P80 (inches)"
    )

    # Performance
    reduction_ratio: Optional[float] = Field(
        None, description="Typical reduction ratio"
    )
    max_feed_size_in: Optional[float] = Field(
        None, description="Maximum feed size (inches)"
    )

    # Crusher type specifics
    crusher_type: Optional[Literal["gyratory", "jaw", "cone", "impact", "roll"]] = (
        Field(None, description="Type of crusher")
    )

    # Gyratory-specific
    head_diameter_in: Optional[float] = Field(
        None, description="Head diameter for gyratory (inches)"
    )
    mantle_diameter_in: Optional[float] = Field(
        None, description="Mantle diameter (inches)"
    )

    # Jaw-specific
    gape_in: Optional[float] = Field(None, description="Jaw gape (inches)")


class MillSpecifications(EntitySpecifications):
    """
    Mill-specific specifications (SAG, Ball, Rod mills).
    """

    # Mill dimensions
    diameter_m: Optional[float] = Field(None, description="Mill diameter (meters)")
    length_m: Optional[float] = Field(None, description="Mill length (meters)")

    # Mill type
    mill_type: Optional[Literal["sag", "ball", "rod", "autogenous", "vertimill"]] = (
        Field(None, description="Type of mill")
    )

    # Operating parameters
    critical_speed_pct: Optional[float] = Field(
        None, description="Operating speed as % of critical speed"
    )
    mill_filling_pct: Optional[float] = Field(
        None, description="Mill filling percentage"
    )
    ball_charge_pct: Optional[float] = Field(
        None, description="Ball charge percentage (for SAG mills)"
    )

    # Media
    media_type: Optional[str] = Field(
        None, description="Grinding media type (steel balls, ceramic, etc.)"
    )
    media_size_mm: Optional[List[float]] = Field(None, description="Media sizes (mm)")

    # Performance
    work_index: Optional[float] = Field(None, description="Bond work index (kWh/tonne)")
    f80_microns: Optional[float] = Field(None, description="Feed F80 (microns)")
    p80_microns: Optional[float] = Field(None, description="Product P80 (microns)")


class ConveyorSpecifications(EntitySpecifications):
    """
    Conveyor-specific specifications.
    """

    # Conveyor dimensions
    belt_width_mm: Optional[float] = Field(None, description="Belt width (mm)")
    belt_length_m: Optional[float] = Field(None, description="Belt length (meters)")
    lift_m: Optional[float] = Field(None, description="Vertical lift (meters)")

    # Operating parameters
    belt_speed_mps: Optional[float] = Field(
        None, description="Belt speed (meters per second)"
    )
    max_lump_size_mm: Optional[float] = Field(
        None, description="Maximum lump size (mm)"
    )

    # Belt specifications
    belt_type: Optional[str] = Field(None, description="Belt type/grade")
    number_of_plies: Optional[int] = Field(None, description="Number of plies in belt")

    # Idlers and pulleys
    idler_spacing_m: Optional[float] = Field(None, description="Idler spacing (meters)")
    drive_pulley_diameter_mm: Optional[float] = Field(
        None, description="Drive pulley diameter (mm)"
    )


class EntityCostData(BaseDBModel):
    """
    Cost data for an entity.

    Tracks complete cost breakdown with provenance.
    """

    # Purchase cost
    purchase_cost: Optional[float] = Field(None, description="Equipment purchase cost")
    purchase_cost_year: Optional[int] = Field(None, description="Year of purchase cost")
    purchase_cost_currency: str = Field("USD", description="Currency")

    # Installed cost
    installation_cost: Optional[float] = Field(None, description="Installation cost")
    total_installed_cost: Optional[float] = Field(
        None, description="Total installed cost (TIC)"
    )

    # Cost breakdown
    cost_breakdown: Dict[str, float] = Field(
        default_factory=dict, description="Cost breakdown by WBS or category"
    )

    # OPEX
    annual_maintenance_cost: Optional[float] = Field(
        None, description="Annual maintenance cost"
    )
    annual_power_cost: Optional[float] = Field(None, description="Annual power cost")
    annual_labor_cost: Optional[float] = Field(None, description="Annual labor cost")
    total_annual_opex: Optional[float] = Field(None, description="Total annual OPEX")

    # Provenance
    cost_source: Optional[str] = Field(
        None,
        description="Source of cost data (vendor quote, estimate, historical, etc.)",
    )
    cost_source_table_id: Optional[PyObjectId] = Field(
        None, description="ID of cost table if from database"
    )
    cost_confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence level in cost estimate"
    )
    cost_notes: Optional[str] = Field(None, description="Notes about cost estimate")


class EntityPerformanceData(BaseDBModel):
    """
    Performance and operating data for an entity.

    Tracks actual or expected performance metrics.
    """

    # Operating hours
    operating_hours_per_year: Optional[float] = Field(
        None, description="Operating hours per year"
    )
    availability_pct: Optional[float] = Field(
        None, description="Availability percentage"
    )
    utilization_pct: Optional[float] = Field(None, description="Utilization percentage")

    # Throughput
    actual_throughput: Optional[float] = Field(None, description="Actual throughput")
    throughput_unit: Optional[str] = Field(None, description="Throughput unit")

    # Energy consumption
    specific_energy_kwh_per_tonne: Optional[float] = Field(
        None, description="Specific energy consumption (kWh/tonne)"
    )
    annual_energy_consumption_kwh: Optional[float] = Field(
        None, description="Annual energy consumption (kWh)"
    )

    # Consumables
    liner_life_hours: Optional[float] = Field(None, description="Liner life (hours)")
    media_consumption_kg_per_tonne: Optional[float] = Field(
        None, description="Media consumption (kg/tonne)"
    )

    # Performance metrics
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Additional performance metrics"
    )


class EntityRelationship(BaseDBModel):
    """
    Relationship to another entity.

    Represents connections in the process flow:
    - Feed relationships (upstream equipment)
    - Product relationships (downstream equipment)
    - Supporting relationships (utilities, infrastructure)
    """

    related_entity_id: PyObjectId = Field(..., description="ID of related entity")

    relationship_type: Literal[
        "feeds_to",  # This entity feeds material to related entity
        "receives_from",  # This entity receives material from related entity
        "supports",  # This entity supports related entity (e.g., utility)
        "supported_by",  # This entity is supported by related entity
        "alternative_to",  # This entity is an alternative to related entity
        "replaced_by",  # This entity was replaced by related entity
        "replaces",  # This entity replaces related entity
    ] = Field(..., description="Type of relationship")

    relationship_context: Optional[str] = Field(
        None, description="Additional context about relationship"
    )

    # Flow data (if applicable)
    material_flow_tph: Optional[float] = Field(
        None, description="Material flow rate (tph)"
    )
    stream_name: Optional[str] = Field(None, description="Stream name/identifier")


class Entity(BaseDBModel):
    """
    Complete entity model.

    Represents any component in the mining operation.
    """

    # Core identification
    project_id: PyObjectId = Field(..., description="Parent project ID")
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(
        ...,
        description="Entity type (e.g., 'gyratory_crusher', 'sag_mill', 'conveyor')",
    )
    entity_category: Optional[
        Literal[
            "crushing",
            "grinding",
            "classification",
            "material_handling",
            "dewatering",
            "utilities",
            "infrastructure",
            "process",
            "other",
        ]
    ] = Field(None, description="Entity category for grouping")

    # Description and identification
    description: Optional[str] = Field(None, description="Entity description")
    tag_number: Optional[str] = Field(
        None, description="Equipment tag number (e.g., CR-001)"
    )
    location: Optional[str] = Field(None, description="Physical location in plant")

    # Status
    status: Literal[
        "planned",  # Not yet purchased/installed
        "existing",  # Currently in operation
        "proposed",  # Proposed addition/modification
        "retired",  # No longer in use
        "archived",  # Historical record
    ] = Field("planned", description="Entity status")

    # Scenario context (if part of a scenario)
    scenario_id: Optional[PyObjectId] = Field(
        None, description="Scenario ID if this entity is part of a scenario"
    )
    option_id: Optional[PyObjectId] = Field(
        None, description="Option ID if this entity is part of an option"
    )
    is_base_case: bool = Field(
        True, description="Whether this entity is part of the base case"
    )

    # Specifications (polymorphic based on entity_type)
    specifications: Union[
        CrusherSpecifications,
        MillSpecifications,
        ConveyorSpecifications,
        EntitySpecifications,
    ] = Field(
        default_factory=EntitySpecifications, description="Technical specifications"
    )

    # Cost data
    cost_data: Optional[EntityCostData] = Field(None, description="Cost data")

    # Performance data
    performance_data: Optional[EntityPerformanceData] = Field(
        None, description="Performance and operating data"
    )

    # Relationships
    relationships: List[EntityRelationship] = Field(
        default_factory=list, description="Relationships to other entities"
    )

    # Process integration
    process_circuit: Optional[str] = Field(
        None,
        description="Process circuit this entity belongs to (e.g., 'primary_crushing')",
    )
    process_stage: Optional[int] = Field(
        None, description="Stage number in process sequence"
    )

    # Data provenance
    data_source: Optional[str] = Field(
        None, description="Source of entity data (vendor, historical, estimate, etc.)"
    )
    source_document_ids: List[PyObjectId] = Field(
        default_factory=list, description="IDs of source documents"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence level in entity data"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for organization-specific data"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class EntitySummary(BaseDBModel):
    """
    Lightweight entity summary for list views.
    """

    id: PyObjectId = Field(..., alias="_id")
    project_id: PyObjectId
    name: str
    entity_type: str
    entity_category: Optional[str]
    status: str

    # Key specs
    manufacturer: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    capacity: Optional[float] = Field(None)
    capacity_unit: Optional[str] = Field(None)
    power_kw: Optional[float] = Field(None)

    # Cost summary
    total_installed_cost: Optional[float] = Field(None)

    # Context
    is_base_case: bool
    scenario_id: Optional[PyObjectId]

    created_at: datetime


class EntityComparison(BaseDBModel):
    """
    Comparison data for two entities.

    Used to show differences between base case and scenario alternatives.
    """

    base_entity: EntitySummary
    alternative_entity: EntitySummary

    # Differences
    specification_changes: Dict[str, Any] = Field(
        default_factory=dict, description="Changed specifications"
    )
    cost_delta: Optional[float] = Field(
        None, description="Cost difference (alternative - base)"
    )
    performance_changes: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metric changes"
    )

    # Impact assessment
    downstream_impacts: List[Dict[str, Any]] = Field(
        default_factory=list, description="Downstream impacts of this change"
    )
