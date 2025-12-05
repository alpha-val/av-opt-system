"""
Component serialization for vector search.

This module provides functions to serialize components from scenario analysis
results into text representations suitable for embedding and vector search.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def serialize_component_for_matching(
    component: Dict[str, Any],
    lever_values: Dict[str, Any],
    lever_types: Dict[str, str],
) -> str:
    """
    Serialize a component into text representation for embedding and vector search.
    
    Builds a text representation using:
    - Component role
    - MSIO hierarchy (discipline, category, subcategory)
    - Decision lever attributes with their values
    
    For Fixed attributes: Includes exact value in serialization
    For Floating attributes: Includes value but allows fuzzy matching
    
    Args:
        component: Component dictionary from scenario analysis results
        lever_values: Dictionary mapping lever_id to current value
        lever_types: Dictionary mapping lever_id to 'Fixed' or 'Floating'
        
    Returns:
        Text string suitable for embedding
    """
    try:
        parts = []
        
        # Component role (name)
        role = component.get("role", "Unknown Component")
        parts.append(f"name: {role}")
        
        # Type
        parts.append("type: Component")
        
        # MSIO hierarchy (critical for ontology alignment)
        msio_discipline = component.get("msio_discipline", "")
        msio_category = component.get("msio_category", "")
        msio_subcategory = component.get("msio_subcategory", "")
        
        if msio_discipline:
            parts.append(f"discipline: {msio_discipline}")
        if msio_category:
            parts.append(f"category: {msio_category}")
        if msio_subcategory:
            parts.append(f"subcategory: {msio_subcategory}")
        
        # Decision lever attributes
        # Note: lever_values and lever_types should only contain levers for this component
        # This ensures each component is matched independently with only its own attributes
        decision_levers = component.get("decision_levers", [])
        attr_texts = []
        
        for lever in decision_levers:
            lever_id = lever.get("lever_id")
            if not lever_id:
                continue
            
            # Only include levers that are in lever_values (component-specific filtering)
            if lever_id not in lever_values:
                continue
                
            attribute_name = lever.get("attribute_name", "Unknown")
            lever_value = lever_values.get(lever_id)
            lever_type = lever_types.get(lever_id, "Floating")
            baseline_unit = lever.get("baseline_unit", "")
            
            # Use user-provided value if available, otherwise use baseline
            if lever_value is not None:
                value = lever_value
            else:
                value = lever.get("baseline_value")
            
            # Build attribute text
            if value is not None:
                attr_text = f"{attribute_name}: {value}"
                if baseline_unit:
                    attr_text += f" {baseline_unit}"
                
                # For Fixed attributes, emphasize exact matching
                if lever_type == "Fixed":
                    attr_text += " [Fixed]"
                
                attr_texts.append(attr_text)
        
        # Append attributes to parts if any were collected
        if attr_texts:
            parts.append(f"attributes: {', '.join(attr_texts)}")
        
        # Quantity if available
        quantity = component.get("quantity")
        if quantity is not None:
            parts.append(f"quantity: {quantity}")
        
        # Join all parts into a single text string
        text = ". ".join(parts)
        return text if text else "Unknown Component"
        
    except Exception as e:
        logger.error(f"Error serializing component {component.get('component_id')}: {e}", exc_info=True)
        return "Unknown Component"

