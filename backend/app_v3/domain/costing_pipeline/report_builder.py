"""
Cost comparison report builder for components.

This module provides functions to build cost comparison reports
showing baseline vs redesigned system costs.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def build_cost_comparison_report(
    component_costs: List[Dict[str, Any]],
    calculation_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a comprehensive cost comparison report.
    
    Args:
        component_costs: List of component cost dictionaries from extract_component_costs
        calculation_summary: Summary from calculate_baseline_vs_redesigned
        
    Returns:
        Dictionary containing:
        {
            "summary": {
                "baseline_total": float | None,
                "redesigned_total": float | None,
                "cost_difference": float | None,
                "cost_percentage_change": float | None,
            },
            "components": List[Dict],  # Component-by-component breakdown
            "metadata": {
                "total_components": int,
                "components_with_costs": int,
                "components_with_matches": int,
            }
        }
    """
    try:
        # Extract summary data
        summary = {
            "baseline_total": calculation_summary.get("baseline_total"),
            "redesigned_total": calculation_summary.get("redesigned_total"),
            "cost_difference": calculation_summary.get("cost_difference"),
            "cost_percentage_change": calculation_summary.get("cost_percentage_change"),
        }
        
        # Extract component breakdown
        components = calculation_summary.get("components", [])
        
        # Calculate metadata
        total_components = len(component_costs)
        components_with_costs = sum(
            1 for comp in components
            if comp.get("baseline_cost") is not None or comp.get("redesigned_cost") is not None
        )
        components_with_matches = sum(
            1 for comp in components
            if comp.get("best_match") is not None
        )
        
        metadata = {
            "total_components": total_components,
            "components_with_costs": components_with_costs,
            "components_with_matches": components_with_matches,
        }
        
        return {
            "summary": summary,
            "components": components,
            "metadata": metadata,
        }
        
    except Exception as e:
        logger.error(f"Error building cost comparison report: {e}", exc_info=True)
        return {
            "summary": {
                "baseline_total": None,
                "redesigned_total": None,
                "cost_difference": None,
                "cost_percentage_change": None,
            },
            "components": [],
            "metadata": {
                "total_components": 0,
                "components_with_costs": 0,
                "components_with_matches": 0,
            },
        }

