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
            "baseline_cost": float | None,  # Cost value from baseline component (if available)
            "baseline_cost_info": Dict | None,  # Full cost object with currency, basis_year, etc.
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
        
        # Extract baseline cost value and full cost info (if component has cost info)
        baseline_cost = _extract_cost_value(component)
        baseline_cost_info = _extract_full_cost_info(component)
        
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
            "baseline_cost_info": baseline_cost_info,
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
            "baseline_cost_info": None,
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
            baseline_cost_info = comp_cost.get("baseline_cost_info")
            
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
            
            # Component breakdown (include baseline_cost_info for full cost metadata)
            component_breakdown = {
                "component_id": component_id,
                "component_role": component_role,
                "baseline_cost": baseline_cost,
                "redesigned_cost": redesigned_cost,
                "best_match": best_match,
            }
            
            # Include baseline_cost_info if available (for currency, basis_year, etc.)
            if baseline_cost_info is not None:
                component_breakdown["baseline_cost_info"] = baseline_cost_info
            
            components_breakdown.append(component_breakdown)
        
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
    
    Handles multiple formats:
    1. Component-level cost: component.cost.cost_value (NEW)
    2. Entity properties direct: properties.cost_value
    3. Entity properties nested: properties.cost.cost_value
    
    Args:
        entity_or_component: Entity or component dictionary
        
    Returns:
        Cost value as float, or None if not found
    """
    try:
        # Priority 1: Check for component-level cost structure (NEW)
        # This is for components that have cost information directly at component level
        component_cost = entity_or_component.get("cost")
        if component_cost is not None and isinstance(component_cost, dict):
            cost_value = component_cost.get("cost_value")
            if cost_value is not None:
                # Convert to float if needed
                return _normalize_cost_value(cost_value)
        
        # Priority 2 & 3: Check entity properties formats (existing)
        props = entity_or_component.get("properties", {}) or {}
        
        # Try new format first (direct properties)
        cost_value = props.get("cost_value")
        
        # If not found, try old format (cost object)
        if cost_value is None:
            cost_info = props.get("cost", {}) or {}
            cost_value = cost_info.get("cost_value")
        
        # Normalize and return
        if cost_value is not None:
            return _normalize_cost_value(cost_value)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting cost value: {e}")
        return None


def _extract_full_cost_info(entity_or_component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract full cost information object from entity or component.
    
    Returns the complete cost object with all fields (currency, basis_year, cost_type, etc.)
    when available. This is useful for preserving cost metadata for reporting.
    
    Args:
        entity_or_component: Entity or component dictionary
        
    Returns:
        Full cost info dictionary, or None if not found
    """
    try:
        # Priority 1: Check for component-level cost structure (NEW)
        component_cost = entity_or_component.get("cost")
        if component_cost is not None and isinstance(component_cost, dict):
            # Return a copy to avoid mutating the original
            return component_cost.copy()
        
        # Priority 2 & 3: Check entity properties formats (existing)
        props = entity_or_component.get("properties", {}) or {}
        
        # Try direct cost object first
        cost_info = props.get("cost")
        if cost_info is not None and isinstance(cost_info, dict):
            return cost_info.copy()
        
        # Try building from direct properties
        cost_value = props.get("cost_value")
        if cost_value is not None:
            # Build cost info from available properties
            cost_info = {
                "cost_value": cost_value,
                "cost_currency": props.get("cost_currency"),
                "cost_min": props.get("cost_min"),
                "cost_max": props.get("cost_max"),
                "cost_unit": props.get("cost_unit"),
                "cost_basis": props.get("cost_basis"),
                "cost_basis_year": props.get("cost_basis_year"),
                "cost_type": props.get("cost_type"),
                "annual_op_cost": props.get("annual_op_cost"),
                "reclamation_cost": props.get("reclamation_cost"),
                "cost_text": props.get("cost_text"),
                "cost_alternates": props.get("cost_alternates"),
            }
            # Remove None values to keep it clean
            return {k: v for k, v in cost_info.items() if v is not None}
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting full cost info: {e}")
        return None


def _normalize_cost_value(cost_value: Any) -> Optional[float]:
    """
    Normalize cost value to float.
    
    Handles string values with currency symbols and commas.
    
    Args:
        cost_value: Cost value (string, number, or None)
        
    Returns:
        Cost value as float, or None if conversion fails
    """
    if cost_value is None:
        return None
    
    # Handle string values
    if isinstance(cost_value, str):
        try:
            # Remove currency symbols and commas
            cleaned = cost_value.replace(",", "").replace("$", "").replace("USD", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    # Handle numeric values
    try:
        return float(cost_value)
    except (ValueError, TypeError):
        return None

