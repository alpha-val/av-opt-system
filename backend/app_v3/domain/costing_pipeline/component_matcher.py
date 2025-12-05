"""
Component matching with tabular entities using vector search.

This module provides functions to match components with tabular entities
using semantic search, applying Fixed/Floating matching logic.
"""
from typing import Dict, Any, List, Optional
import logging

from ..parsing.storage.vector_store import (
    generate_embeddings,
    search_entities_by_embedding,
)
from .component_serializer import serialize_component_for_matching

logger = logging.getLogger(__name__)


def match_component_with_tabular_entities(
    component: Dict[str, Any],
    lever_values: Dict[str, Any],
    lever_types: Dict[str, str],
    project_id: str,
    top_k: int = 3,
    cutoff: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Match a component with tabular entities using semantic search.
    
    Applies Fixed/Floating matching logic:
    - Floating: Uses normal vector similarity (cutoff ~0.5-0.7)
    - Fixed: First does vector search, then filters for exact attribute matches.
             If no exact match found, reduces relevance_score by penalty factor (0.3)
    
    Args:
        component: Component dictionary from scenario analysis results
        lever_values: Dictionary mapping lever_id to current value
        lever_types: Dictionary mapping lever_id to 'Fixed' or 'Floating'
        project_id: Project identifier for Pinecone namespace
        top_k: Maximum number of matching entities to return
        cutoff: Minimum similarity score threshold for semantic search
        
    Returns:
        Ranked list of tabular entities with relevance scores, adjusted for Fixed attributes
    """
    try:
        # Serialize component for embedding
        text_for_embedding = serialize_component_for_matching(
            component, lever_values, lever_types
        )
        
        logger.debug(
            f"Finding tabular entities for component {component.get('component_id')}: "
            f"project_id={project_id}, top_k={top_k}, cutoff={cutoff}"
        )
        logger.debug(f"Component text for embedding: {text_for_embedding[:200]}...")
        
        # Generate embedding
        embeddings = generate_embeddings([text_for_embedding])
        if not embeddings:
            logger.error(f"Failed to generate embedding for component {component.get('component_id')}")
            return []
        
        embedding = embeddings[0]
        logger.debug(f"Generated embedding vector of length {len(embedding)}")
        
        # Search for tabular_data entities using semantic search
        # Filter for Equipment and Material entity types
        # Use a higher top_k initially to allow for filtering
        search_top_k = top_k * 2  # Get more results for filtering
        results = search_entities_by_embedding(
            embedding=embedding,
            project_id=project_id,
            artifact_type="tabular_data",
            entity_types=["Equipment", "Material"],
            top_k=search_top_k,
            cutoff=cutoff,
        )
        
        logger.debug(
            f"Found {len(results)} tabular entities before Fixed/Floating filtering"
        )
        
        # Apply Fixed/Floating matching logic
        filtered_results = _apply_fixed_floating_logic(
            component=component,
            results=results,
            lever_values=lever_values,
            lever_types=lever_types,
        )
        
        # Return top_k results after filtering
        final_results = filtered_results[:top_k]
        
        logger.info(
            f"Found {len(final_results)} tabular entities for component "
            f"{component.get('component_id')} after Fixed/Floating filtering"
        )
        
        return final_results
        
    except Exception as e:
        logger.error(
            f"Failed to match component {component.get('component_id')} with tabular entities: {e}",
            exc_info=True,
        )
        return []


def _apply_fixed_floating_logic(
    component: Dict[str, Any],
    results: List[Dict[str, Any]],
    lever_values: Dict[str, Any],
    lever_types: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Apply Fixed/Floating matching logic to search results.
    
    For Fixed attributes:
    - Check if tabular entity has exact attribute matches
    - If no exact match found, reduce relevance_score by penalty factor (0.3)
    
    For Floating attributes:
    - Keep original relevance score (no penalty)
    
    Args:
        component: Component dictionary
        results: List of tabular entities with relevance_score
        lever_values: Dictionary mapping lever_id to current value
        lever_types: Dictionary mapping lever_id to 'Fixed' or 'Floating'
        
    Returns:
        List of results with adjusted relevance scores, sorted by score (descending)
    """
    try:
        decision_levers = component.get("decision_levers", [])
        
        # Extract Fixed levers and their values
        fixed_levers = {}
        for lever in decision_levers:
            lever_id = lever.get("lever_id")
            if not lever_id:
                continue
                
            lever_type = lever_types.get(lever_id, "Floating")
            if lever_type == "Fixed":
                attribute_name = lever.get("attribute_name", "")
                lever_value = lever_values.get(lever_id)
                if attribute_name and lever_value is not None:
                    fixed_levers[attribute_name] = lever_value
        
        # If no Fixed levers, return results as-is
        if not fixed_levers:
            return results
        
        # Process each result
        adjusted_results = []
        for result in results:
            relevance_score = result.get("relevance_score", 0.0)
            
            # Check for exact matches on Fixed attributes
            tabular_entity = result
            tabular_props = tabular_entity.get("properties", {}) or {}
            tabular_attributes = tabular_props.get("attributes", [])
            
            # Build a map of tabular entity attributes
            tabular_attr_map = {}
            for attr in tabular_attributes:
                if isinstance(attr, dict):
                    attr_name = attr.get("name", "")
                    attr_value = attr.get("value")
                    if attr_name:
                        tabular_attr_map[attr_name] = attr_value
            
            # Check if all Fixed attributes have exact matches
            all_fixed_match = True
            for fixed_attr_name, fixed_attr_value in fixed_levers.items():
                tabular_value = tabular_attr_map.get(fixed_attr_name)
                
                # Compare values (handle numeric and string comparisons)
                if tabular_value is None:
                    all_fixed_match = False
                    break
                
                # Try numeric comparison first
                try:
                    fixed_num = float(fixed_attr_value) if fixed_attr_value is not None else None
                    tabular_num = float(tabular_value) if tabular_value is not None else None
                    if fixed_num is not None and tabular_num is not None:
                        if abs(fixed_num - tabular_num) > 0.01:  # Small tolerance for floating point
                            all_fixed_match = False
                            break
                    elif str(fixed_attr_value).strip().lower() != str(tabular_value).strip().lower():
                        all_fixed_match = False
                        break
                except (ValueError, TypeError):
                    # Fall back to string comparison
                    if str(fixed_attr_value).strip().lower() != str(tabular_value).strip().lower():
                        all_fixed_match = False
                        break
            
            # Apply penalty if Fixed attributes don't match exactly
            if not all_fixed_match:
                penalty_factor = 0.3
                relevance_score = relevance_score * (1 - penalty_factor)
                logger.debug(
                    f"Applied penalty to result {result.get('id')}: "
                    f"score reduced from {result.get('relevance_score')} to {relevance_score}"
                )
            
            # Create adjusted result
            adjusted_result = result.copy()
            adjusted_result["relevance_score"] = relevance_score
            adjusted_results.append(adjusted_result)
        
        # Sort by adjusted relevance score (descending)
        adjusted_results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        
        return adjusted_results
        
    except Exception as e:
        logger.error(
            f"Error applying Fixed/Floating logic: {e}",
            exc_info=True,
        )
        # Return original results on error
        return results

