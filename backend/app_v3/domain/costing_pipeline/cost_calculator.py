"""
Cost calculation utilities for components.

This module provides functions to extract costs from matched tabular entities
and calculate baseline vs redesigned system costs.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def extract_component_costs(
    component: Dict[str, Any],
    matched_tabular_entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Extract cost information from matched tabular entities for a component.
    
    Args:
        component: Component dictionary from scenario analysis results
        matched_tabular_entities: List of matched tabular entities with relevance scores
        
    Returns:
        Dictionary containing:
        {
            "component_id": str,
            "component_role": str,
            "baseline_cost": float | None,  # Cost from baseline component (if available)
            "matched_costs": List[Dict],  # Each with:
                {
                    "tabular_entity": Dict,  # Full tabular entity
                    "cost": float | None,  # Extracted cost value
                    "relevance_score": float,  # Match relevance score
                }
        }
    """
    try:
        component_id = component.get("component_id", "")
        component_role = component.get("role", "Unknown")
        
        # Extract baseline cost (if component has cost info)
        baseline_cost = _extract_cost_value(component)
        
        # Extract costs from matched tabular entities
        matched_costs = []
        for tabular_entity in matched_tabular_entities:
            cost_value = _extract_cost_value(tabular_entity)
            relevance_score = tabular_entity.get("relevance_score", 0.0)
            
            matched_costs.append({
                "tabular_entity": tabular_entity,
                "cost": cost_value,
                "relevance_score": relevance_score,
            })
        
        return {
            "component_id": component_id,
            "component_role": component_role,
            "baseline_cost": baseline_cost,
            "matched_costs": matched_costs,
        }
        
    except Exception as e:
        logger.error(
            f"Error extracting costs for component {component.get('component_id')}: {e}",
            exc_info=True,
        )
        return {
            "component_id": component.get("component_id", ""),
            "component_role": component.get("role", "Unknown"),
            "baseline_cost": None,
            "matched_costs": [],
        }


def calculate_baseline_vs_redesigned(
    component_costs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate baseline vs redesigned system costs.
    
    Args:
        component_costs: List of component cost dictionaries from extract_component_costs
        
    Returns:
        Dictionary containing:
        {
            "baseline_total": float | None,
            "redesigned_total": float | None,
            "cost_difference": float | None,
            "cost_percentage_change": float | None,
            "components": List[Dict],  # Component-by-component breakdown
        }
    """
    try:
        baseline_total = 0.0
        redesigned_total = 0.0
        components_breakdown = []
        
        for comp_cost in component_costs:
            component_id = comp_cost.get("component_id", "")
            component_role = comp_cost.get("component_role", "Unknown")
            baseline_cost = comp_cost.get("baseline_cost")
            
            # Get best match cost (highest relevance score)
            matched_costs = comp_cost.get("matched_costs", [])
            best_match_cost = None
            best_match = None
            
            if matched_costs:
                # Sort by relevance score (descending) and take the best match
                sorted_matches = sorted(
                    matched_costs,
                    key=lambda x: x.get("relevance_score", 0.0),
                    reverse=True,
                )
                best_match = sorted_matches[0]
                best_match_cost = best_match.get("cost")
            
            # Use best match cost as redesigned cost, or baseline if no match
            redesigned_cost = best_match_cost if best_match_cost is not None else baseline_cost
            
            # Accumulate totals (only if costs are numeric)
            if isinstance(baseline_cost, (int, float)) and baseline_cost is not None:
                baseline_total += baseline_cost
            
            if isinstance(redesigned_cost, (int, float)) and redesigned_cost is not None:
                redesigned_total += redesigned_cost
            
            # Component breakdown
            components_breakdown.append({
                "component_id": component_id,
                "component_role": component_role,
                "baseline_cost": baseline_cost,
                "redesigned_cost": redesigned_cost,
                "best_match": best_match,
            })
        
        # Calculate difference and percentage change
        cost_difference = None
        cost_percentage_change = None
        
        if baseline_total > 0:
            cost_difference = redesigned_total - baseline_total
            cost_percentage_change = (cost_difference / baseline_total) * 100
        
        return {
            "baseline_total": baseline_total if baseline_total > 0 else None,
            "redesigned_total": redesigned_total if redesigned_total > 0 else None,
            "cost_difference": cost_difference,
            "cost_percentage_change": cost_percentage_change,
            "components": components_breakdown,
        }
        
    except Exception as e:
        logger.error(f"Error calculating baseline vs redesigned costs: {e}", exc_info=True)
        return {
            "baseline_total": None,
            "redesigned_total": None,
            "cost_difference": None,
            "cost_percentage_change": None,
            "components": [],
        }


def _extract_cost_value(entity_or_component: Dict[str, Any]) -> Optional[float]:
    """
    Extract cost value from entity or component properties.
    
    Handles both old format (cost object) and new format (direct properties).
    Also handles components which may have cost in different structure.
    
    Args:
        entity_or_component: Entity or component dictionary
        
    Returns:
        Cost value as float, or None if not found
    """
    try:
        props = entity_or_component.get("properties", {}) or {}
        
        # Try new format first (direct properties)
        cost_value = props.get("cost_value")
        
        # If not found, try old format (cost object)
        if cost_value is None:
            cost_info = props.get("cost", {}) or {}
            cost_value = cost_info.get("cost_value")
        
        # Handle cost_value if it's a string (convert to float)
        if isinstance(cost_value, str):
            try:
                # Remove currency symbols and commas
                cost_value = float(
                    cost_value.replace(",", "").replace("$", "").replace("USD", "").strip()
                )
            except (ValueError, AttributeError):
                return None
        elif cost_value is not None:
            try:
                cost_value = float(cost_value)
            except (ValueError, TypeError):
                return None
        
        return cost_value
        
    except Exception as e:
        logger.debug(f"Error extracting cost value: {e}")
        return None

