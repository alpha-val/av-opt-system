"""
Table domain models.

Tables store reference data extracted from uploaded documents:
- Cost tables (equipment purchase costs)
- Sizing tables (equipment selection criteria)
- Lang factor tables (cost estimation factors)
- Escalation indices (cost escalation data)
- Process data tables (metallurgical test results, etc.)

Tables bridge the gap between unstructured documents (PDFs, Excel) and
structured data needed for analysis.
"""

from pydantic import Field
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime

from .base import BaseDBModel, PyObjectId


class TableMetadata(BaseDBModel):
    """
    Metadata about a table.

    Describes what the table contains and how it should be used.
    """

    # Source information
    source_document_id: Optional[PyObjectId] = Field(
        None, description="ID of source document this table was extracted from"
    )
    source_filename: Optional[str] = Field(None, description="Original filename")
    source_page: Optional[str] = Field(
        None, description="Page reference (e.g., 'Pg13', 'Sheet2')"
    )
    source_location: Optional[str] = Field(
        None, description="Location within document (e.g., 'Table 4-2', 'Section 3.1')"
    )

    # Table classification
    equipment_type: Optional[str] = Field(
        None, description="Equipment type if table is equipment-specific"
    )
    commodity: Optional[str] = Field(
        None, description="Commodity if table is commodity-specific"
    )
    region: Optional[str] = Field(None, description="Geographic region if applicable")

    # Data characteristics
    data_quality: Literal["high", "medium", "low"] = Field(
        "medium", description="Assessed data quality"
    )
    completeness_pct: Optional[float] = Field(
        None, description="Percentage of complete/non-null data"
    )

    # Temporal context
    data_year: Optional[int] = Field(None, description="Year the data is from")
    revision: Optional[str] = Field(
        None, description="Revision or version (e.g., 'Rev 3', 'Q1 2025')"
    )
    supersedes_table_id: Optional[PyObjectId] = Field(
        None, description="ID of table this supersedes (if updated version)"
    )

    # Usage
    is_default: bool = Field(
        False, description="Whether this is the default table for its type"
    )
    usage_count: int = Field(
        0, description="Number of times this table has been used in analysis"
    )
    last_used: Optional[datetime] = Field(
        None, description="When this table was last used"
    )


class TableColumn(BaseDBModel):
    """
    Definition of a table column.

    Describes the structure and meaning of each column.
    """

    name: str = Field(..., description="Column name")
    display_name: Optional[str] = Field(None, description="Human-readable column name")

    data_type: Literal[
        "string",
        "number",
        "integer",
        "boolean",
        "date",
        "currency",
        "percentage",
        "measurement",
    ] = Field(..., description="Data type")

    unit: Optional[str] = Field(
        None, description="Unit of measurement (e.g., 'USD', 'inches', 'kW')"
    )

    description: Optional[str] = Field(
        None, description="Description of what this column contains"
    )

    # Data validation
    is_required: bool = Field(
        False, description="Whether this column must have a value"
    )
    min_value: Optional[float] = Field(
        None, description="Minimum valid value (for numeric columns)"
    )
    max_value: Optional[float] = Field(
        None, description="Maximum valid value (for numeric columns)"
    )
    allowed_values: Optional[List[str]] = Field(
        None, description="List of allowed values (for categorical columns)"
    )

    # Index/key
    is_primary_key: bool = Field(
        False, description="Whether this is the primary key column (e.g., 'model')"
    )
    is_indexed: bool = Field(
        False, description="Whether this column is indexed for searching"
    )


class TableRow(BaseDBModel):
    """
    A single row in a table.

    Stores the actual data with validation status.
    """

    # Row identification
    row_number: Optional[int] = Field(
        None, description="Original row number from source"
    )
    row_id: Optional[str] = Field(
        None, description="Unique identifier for this row (e.g., model number)"
    )

    # Data
    data: Dict[str, Any] = Field(..., description="Row data as key-value pairs")

    # Validation
    is_valid: bool = Field(True, description="Whether row passed validation")
    validation_errors: List[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    validation_warnings: List[str] = Field(
        default_factory=list, description="List of validation warnings"
    )

    # Flags
    is_interpolated: bool = Field(
        False, description="Whether any values were interpolated/estimated"
    )
    is_outlier: bool = Field(False, description="Whether row is a statistical outlier")

    # Usage tracking
    usage_count: int = Field(0, description="Number of times this row was used")

    # Notes
    notes: Optional[str] = Field(None, description="Notes about this row")


class CostTableRow(TableRow):
    """
    Specialized row for cost tables.

    Ensures cost-specific fields are properly structured.
    """

    # Override data field with typed structure
    model: str = Field(..., description="Equipment model")
    equipment_type: str = Field(..., description="Equipment type")

    # Cost data
    purchase_cost: float = Field(..., description="Purchase cost")
    cost_currency: str = Field("USD", description="Currency")
    cost_year: int = Field(..., description="Cost basis year")

    # Cost details
    includes: List[str] = Field(
        default_factory=list,
        description="What's included in cost (e.g., 'motor', 'controls')",
    )
    excludes: List[str] = Field(
        default_factory=list,
        description="What's excluded (e.g., 'foundation', 'installation')",
    )

    # Vendor information
    vendor: Optional[str] = Field(None, description="Vendor/manufacturer")
    quote_date: Optional[datetime] = Field(None, description="Quote date")
    quote_number: Optional[str] = Field(None, description="Quote reference number")


class SizingTableRow(TableRow):
    """
    Specialized row for sizing tables.

    Equipment selection criteria and capacities.
    """

    model: str = Field(..., description="Equipment model")
    manufacturer: Optional[str] = Field(None, description="Manufacturer")

    # Capacity range
    min_capacity: Optional[float] = Field(None, description="Minimum capacity")
    max_capacity: float = Field(..., description="Maximum/rated capacity")
    capacity_unit: str = Field("tph", description="Capacity unit")

    # Size constraints
    min_feed_size: Optional[float] = Field(None, description="Minimum feed size")
    max_feed_size: Optional[float] = Field(None, description="Maximum feed size")
    min_product_size: Optional[float] = Field(None, description="Minimum product size")
    max_product_size: Optional[float] = Field(None, description="Maximum product size")
    size_unit: str = Field("inches", description="Size unit")

    # Power
    power_kw: float = Field(..., description="Installed power (kW)")

    # Applicability
    suitable_materials: List[str] = Field(
        default_factory=list, description="Suitable materials/ore types"
    )
    application_notes: Optional[str] = Field(None, description="Application guidelines")


class LangFactorRow(TableRow):
    """
    Specialized row for lang factor tables.

    Cost estimation factors for installed cost calculation.
    """

    category: str = Field(
        ..., description="Equipment category (e.g., 'Primary Crushing')"
    )
    wbs_code: Optional[str] = Field(None, description="WBS code")

    # Factors
    equipment_multiplier: float = Field(
        ..., description="Total equipment multiplier (e.g., 3.5x)"
    )

    # Breakdown (if available)
    civil_structural_factor: Optional[float] = Field(
        None, description="Civil & structural as factor of equipment cost"
    )
    piping_factor: Optional[float] = Field(
        None, description="Piping as factor of equipment cost"
    )
    electrical_factor: Optional[float] = Field(
        None, description="Electrical as factor of equipment cost"
    )
    instrumentation_factor: Optional[float] = Field(
        None, description="Instrumentation as factor of equipment cost"
    )
    installation_labor_factor: Optional[float] = Field(
        None, description="Installation labor as factor of equipment cost"
    )

    # Indirect costs (as percentages)
    indirect_costs_pct: Optional[float] = Field(
        None, description="Indirect costs percentage"
    )
    owners_costs_pct: Optional[float] = Field(
        None, description="Owner's costs percentage"
    )
    contingency_pct: Optional[float] = Field(None, description="Contingency percentage")

    # Applicability
    applicable_equipment_types: List[str] = Field(
        default_factory=list, description="Equipment types these factors apply to"
    )
    project_type: Optional[
        Literal["greenfield", "brownfield", "expansion", "modification"]
    ] = Field(None, description="Type of project factors are for")

    # Source and confidence
    basis: Optional[str] = Field(
        None,
        description="Basis for factors (e.g., 'historical projects', 'vendor data')",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence in factors"
    )


class EscalationIndexRow(TableRow):
    """
    Specialized row for cost escalation indices.

    Time series data for cost escalation (CEPCI, CPI, etc.)
    """

    index_name: str = Field(..., description="Index name (e.g., 'CEPCI')")
    year: int = Field(..., description="Year")
    period: Optional[str] = Field(
        None, description="Period if sub-annual (e.g., 'Q1', 'January')"
    )

    index_value: float = Field(..., description="Index value")

    # Additional context
    base_year: Optional[int] = Field(
        None, description="Base year for index (e.g., 2015=100)"
    )
    source: Optional[str] = Field(None, description="Source of index data")


class ExtractedTableData(BaseDBModel):
    """
    Complete extracted data from a table.

    Contains column definitions and all rows.
    """

    # Structure
    columns: List[TableColumn] = Field(
        default_factory=list, description="Column definitions"
    )

    # Data
    rows: List[
        Union[TableRow, CostTableRow, SizingTableRow, LangFactorRow, EscalationIndexRow]
    ] = Field(default_factory=list, description="Table rows")

    # Statistics
    total_rows: int = Field(0, description="Total number of rows")
    valid_rows: int = Field(0, description="Number of valid rows")
    invalid_rows: int = Field(0, description="Number of invalid rows")

    # Extraction metadata
    extraction_method: Optional[str] = Field(
        None,
        description="Method used to extract table (e.g., 'pdf_plumber', 'openpyxl', 'manual')",
    )
    extraction_confidence: Literal["high", "medium", "low"] = Field(
        "medium", description="Confidence in extraction quality"
    )
    extraction_notes: Optional[str] = Field(
        None, description="Notes about extraction process"
    )


class TableValidationRule(BaseDBModel):
    """
    Validation rule for table data.

    Defines business rules for validating table contents.
    """

    rule_name: str = Field(..., description="Rule name")
    rule_type: Literal[
        "required_field",
        "numeric_range",
        "allowed_values",
        "unique_constraint",
        "cross_field_validation",
        "custom",
    ] = Field(..., description="Type of validation rule")

    column_name: Optional[str] = Field(None, description="Column this rule applies to")

    # Rule parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Rule-specific parameters"
    )

    # Severity
    severity: Literal["error", "warning"] = Field(
        "error", description="Severity if rule is violated"
    )

    error_message: str = Field(
        ..., description="Error message to show if rule is violated"
    )

    is_active: bool = Field(True, description="Whether rule is active")


class Table(BaseDBModel):
    """
    Complete table model.

    Represents a table of reference data extracted from documents.
    """

    # Core identification
    project_id: PyObjectId = Field(..., description="Parent project ID")
    name: str = Field(..., description="Table name")

    # Table type
    table_type: Literal[
        "cost_table",
        "sizing_table",
        "lang_factors",
        "escalation_index",
        "process_data",
        "metallurgical_data",
        "geotechnical_data",
        "environmental_data",
        "custom",
    ] = Field(..., description="Type of table")

    description: Optional[str] = Field(None, description="Table description")

    # Metadata
    metadata: TableMetadata = Field(
        default_factory=TableMetadata, description="Table metadata"
    )

    # Structure and data
    extracted_data: ExtractedTableData = Field(
        default_factory=ExtractedTableData, description="Extracted table data"
    )

    # Validation
    validation_rules: List[TableValidationRule] = Field(
        default_factory=list, description="Validation rules for this table"
    )
    validation_status: Literal[
        "not_validated", "validating", "passed", "passed_with_warnings", "failed"
    ] = Field("not_validated", description="Overall validation status")

    # Status
    status: Literal["draft", "active", "superseded", "archived"] = Field(
        "draft", description="Table status"
    )

    # Usage tracking
    used_in_scenario_ids: List[PyObjectId] = Field(
        default_factory=list, description="Scenarios that use this table"
    )
    used_in_option_ids: List[PyObjectId] = Field(
        default_factory=list, description="Options that use this table"
    )

    # Access control
    is_public: bool = Field(
        False, description="Whether table is shared across projects"
    )
    owner_id: Optional[str] = Field(None, description="User who uploaded/created table")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class TableSummary(BaseDBModel):
    """
    Lightweight table summary for list views.
    """

    id: PyObjectId = Field(..., alias="_id")
    project_id: PyObjectId
    name: str
    table_type: str
    status: str

    # Metadata highlights
    equipment_type: Optional[str]
    data_year: Optional[int]
    source_filename: Optional[str]

    # Data stats
    total_rows: int
    valid_rows: int

    # Usage
    usage_count: int
    last_used: Optional[datetime]

    created_at: datetime
    updated_at: datetime


class TableSearchQuery(BaseDBModel):
    """
    Query for searching within tables.

    Supports flexible filtering and searching of table data.
    """

    table_id: PyObjectId = Field(..., description="Table to search")

    # Column filters
    column_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters by column (e.g., {'capacity': {'$gte': 1000}})",
    )

    # Text search
    search_text: Optional[str] = Field(
        None, description="Text to search for across all columns"
    )

    # Pagination
    skip: int = Field(0, description="Number of rows to skip")
    limit: int = Field(100, description="Maximum rows to return")

    # Sorting
    sort_by: Optional[str] = Field(None, description="Column to sort by")
    sort_order: Literal["asc", "desc"] = Field("asc", description="Sort order")


class TableSearchResult(BaseDBModel):
    """
    Results from table search.
    """

    table_id: PyObjectId
    table_name: str

    # Results
    rows: List[TableRow] = Field(default_factory=list, description="Matching rows")
    total_matches: int = Field(0, description="Total number of matching rows")

    # Pagination
    skip: int
    limit: int
    has_more: bool = Field(False, description="Whether more results exist")
