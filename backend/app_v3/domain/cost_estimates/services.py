"""
Cost estimate service layer.

This module provides service functions for cost estimate operations,
acting as a thin wrapper around the repository layer.
"""

from typing import List, Optional, Dict, Any
import logging
from . import repository
from .schemas import CostEstimateCreate, CostEstimateUpdate, CostEstimateOut
from .costing import (
    find_related_tabular_entities,
    build_cost_comparison_report,
)
from ...adapters.mongo.client import db

logger = logging.getLogger(__name__)

__all__ = [
    "create",
    "get",
    "list_all",
    "update",
    "delete",
    "calculate_cost_estimate",
]


async def create(data: CostEstimateCreate) -> CostEstimateOut:
    """
    Create a new cost estimate.
    
    Args:
        data: Cost estimate creation data
        
    Returns:
        Created cost estimate object
    """
    return await repository.create_cost_estimate(data)


async def get(cost_estimate_id: str) -> Optional[CostEstimateOut]:
    """
    Get a cost estimate by ID.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        
    Returns:
        Cost estimate object if found, None otherwise
    """
    return await repository.get_cost_estimate(cost_estimate_id)


async def list_all(scenario_id: Optional[str] = None) -> List[CostEstimateOut]:
    """
    List all cost estimates, optionally filtered by scenario_id.
    
    Args:
        scenario_id: Optional scenario ID to filter cost estimates
        
    Returns:
        List of cost estimate objects
    """
    return await repository.list_cost_estimates(scenario_id)


async def update(
    cost_estimate_id: str, data: CostEstimateUpdate
) -> CostEstimateOut:
    """
    Update an existing cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        data: Cost estimate update data
        
    Returns:
        Updated cost estimate object
        
    Raises:
        ValueError: If cost estimate not found or invalid ID format
    """
    return await repository.update_cost_estimate(cost_estimate_id, data)


async def delete(cost_estimate_id: str) -> bool:
    """
    Delete a cost estimate by ID.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If invalid ID format
    """
    return await repository.delete_cost_estimate(cost_estimate_id)


async def calculate_cost_estimate(
    cost_estimate_id: str,
    project_id: str,
    selected_entities: List[str],
    top_k: int = 3,
    cutoff: float = 0.25,
) -> Dict[str, Any]:
    """
    Calculate cost estimate by finding matching tabular entities for base case entities.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        project_id: Project identifier
        selected_entities: List of base case entity IDs to calculate costs for
        top_k: Number of top matching tabular entities to return per base entity
        cutoff: Minimum similarity score threshold for semantic search
        
    Returns:
        Dictionary containing:
        {
            "cost_comparison_report": List[Dict],
            "base_entities": List[Dict],
            "tabular_entities": List[Dict],
            "matched_entities": List[Dict],
        }
        
    Raises:
        ValueError: If no entities found or invalid parameters
    """
    if not selected_entities:
        raise ValueError("selected_entities cannot be empty")
    
    logger.info(
        f"Calculating cost estimate {cost_estimate_id} for {len(selected_entities)} entities"
    )
    
    # Fetch base case entities from MongoDB
    entities_collection = db().entities
    query = {
        "id": {"$in": selected_entities},
        "properties.artifact_type": "base_case",
    }
    
    base_entities = list(entities_collection.find(query, {"_id": 0}))
    
    if not base_entities:
        raise ValueError(
            f"No base case entities found for IDs: {selected_entities}"
        )
    
    logger.info(f"Found {len(base_entities)} base case entities")
    
    # For each base entity, find related tabular entities
    matched_tabular_entities: Dict[str, List[Dict[str, Any]]] = {}
    all_tabular_entities = []
    seen_tabular_ids = set()
    
    for base_entity in base_entities:
        entity_id = base_entity.get("id")
        if not entity_id:
            logger.warning(f"Base entity missing 'id' field: {base_entity}")
            continue
        
        logger.debug(f"Finding tabular entities for base entity: {entity_id}")
        
        # Find related tabular entities using semantic search
        related_tabular = find_related_tabular_entities(
            entity=base_entity,
            project_id=project_id,
            top_k=top_k,
            cutoff=cutoff,
        )
        
        # Track unique tabular entities
        for tabular_entity in related_tabular:
            tabular_id = tabular_entity.get("id")
            if tabular_id and tabular_id not in seen_tabular_ids:
                seen_tabular_ids.add(tabular_id)
                all_tabular_entities.append(tabular_entity)
        
        matched_tabular_entities[entity_id] = related_tabular
        
        logger.debug(
            f"Found {len(related_tabular)} tabular entities for base entity {entity_id}"
        )
    
    # Build cost comparison report
    cost_comparison_report = build_cost_comparison_report(
        base_entities=base_entities,
        matched_tabular_entities=matched_tabular_entities,
    )
    
    # Build matched entities structure for metadata
    matched_entities = []
    for base_entity in base_entities:
        entity_id = base_entity.get("id")
        matched_entities.append({
            "base_entity": base_entity,
            "tabular_entities": matched_tabular_entities.get(entity_id, []),
        })
    
    logger.info(
        f"Cost calculation completed: {len(cost_comparison_report)} entities processed, "
        f"{len(all_tabular_entities)} unique tabular entities found"
    )
    
    return {
        "cost_comparison_report": cost_comparison_report,
        "base_entities": base_entities,
        "tabular_entities": all_tabular_entities,
        "matched_entities": matched_entities,
    }

