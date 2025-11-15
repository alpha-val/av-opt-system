"""
Cost estimate service layer.

This module provides service functions for cost estimate operations,
acting as a thin wrapper around the repository layer.
"""

from typing import List, Optional
from . import repository
from .schemas import CostEstimateCreate, CostEstimateUpdate, CostEstimateOut

__all__ = [
    "create",
    "get",
    "list_all",
    "update",
    "delete",
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

