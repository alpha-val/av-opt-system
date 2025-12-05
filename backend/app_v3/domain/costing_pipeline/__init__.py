"""
Costing pipeline for component-based cost estimates.

This module provides functions for:
- Serializing components for vector search
- Matching components with tabular entities
- Calculating costs and building comparison reports
"""
from .component_serializer import serialize_component_for_matching
from .component_matcher import match_component_with_tabular_entities
from .cost_calculator import (
    extract_component_costs,
    calculate_baseline_vs_redesigned,
)
from .report_builder import build_cost_comparison_report

__all__ = [
    "serialize_component_for_matching",
    "match_component_with_tabular_entities",
    "extract_component_costs",
    "calculate_baseline_vs_redesigned",
    "build_cost_comparison_report",
]

