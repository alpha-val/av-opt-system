"""
Pydantic schemas for request/response validation.

Schemas define the API contract and handle serialization/deserialization.
They are separate from domain models to allow different representations
at the API boundary vs. internal storage.
"""

from .scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioListResponse,
    ScenarioGenerateOptionsRequest,
    ScenarioStatusUpdate,
)
from .option import (
    OptionResponse,
    OptionListResponse,
    OptionComparisonResponse,
    OptionSelectionRequest,
)
from .costing import (
    CostBreakdown,
    CostProvenance,
    DownstreamImpact,
    NPVAnalysis,
    CostComparisonResponse,
)
from .query import QueryRequest, QueryResponse, QueryHistoryResponse, DataSource

__all__ = [
    # Scenario schemas
    "ScenarioCreate",
    "ScenarioUpdate",
    "ScenarioResponse",
    "ScenarioListResponse",
    "ScenarioGenerateOptionsRequest",
    "ScenarioStatusUpdate",
    # Option schemas
    "OptionResponse",
    "OptionListResponse",
    "OptionComparisonResponse",
    "OptionSelectionRequest",
    # Costing schemas
    "CostBreakdown",
    "CostProvenance",
    "DownstreamImpact",
    "NPVAnalysis",
    "CostComparisonResponse",
    # Query schemas
    "QueryRequest",
    "QueryResponse",
    "QueryHistoryResponse",
    "DataSource",
]
