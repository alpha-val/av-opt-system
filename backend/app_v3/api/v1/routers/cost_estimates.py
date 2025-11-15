"""
Cost estimate router for CRUD operations.

This module provides FastAPI endpoints for cost estimate management:
- Create, Read, Update, Delete (CRUD) operations
- List cost estimates for a scenario
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Path, Query, Depends
from bson.errors import InvalidId

# Import cost estimate service functions
from ....domain.cost_estimates import services
from ....domain.cost_estimates.schemas import (
    CostEstimateCreate,
    CostEstimateUpdate,
    CostEstimateOut,
)
# Import auth for user authentication
from .auth import get_current_user

logger = logging.getLogger(__name__)

# Create router with prefix and tags
# All routes will be under /api/v1/cost-estimates
cost_estimates_router = APIRouter(prefix="/api/v1/cost-estimates", tags=["cost-estimates"])


# Create a new cost estimate
@cost_estimates_router.post(
    "",
    response_model=CostEstimateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cost estimate",
    description="Create a new cost estimate for a scenario.",
)
async def create_cost_estimate(
    data: CostEstimateCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new cost estimate.
    
    Args:
        data: Cost estimate creation data
        current_user: Authenticated user
        
    Returns:
        Created cost estimate object
        
    Raises:
        HTTPException: If validation fails (400) or scenario not found (404)
    """
    try:
        cost_estimate = await services.create(data)
        return cost_estimate
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cost estimate: {str(e)}",
        )


# List all cost estimates
@cost_estimates_router.get(
    "",
    response_model=List[CostEstimateOut],
    summary="List cost estimates",
    description="List all cost estimates, optionally filtered by scenario_id.",
)
async def list_cost_estimates(
    scenario_id: Optional[str] = Query(None, description="Filter by scenario ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all cost estimates.
    
    Args:
        scenario_id: Optional scenario ID to filter cost estimates
        current_user: Authenticated user
        
    Returns:
        List of cost estimate objects
    """
    try:
        cost_estimates = await services.list_all(scenario_id)
        return cost_estimates
        
    except Exception as e:
        logger.error(f"Error listing cost estimates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cost estimates: {str(e)}",
        )


# Get a cost estimate by ID
@cost_estimates_router.get(
    "/{cost_estimate_id}",
    response_model=CostEstimateOut,
    summary="Get cost estimate by ID",
    description="Retrieve a cost estimate by its ID.",
)
async def get_cost_estimate(
    cost_estimate_id: str = Path(..., description="Cost estimate ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a cost estimate by ID.
    
    Args:
        cost_estimate_id: MongoDB ObjectId as string
        current_user: Authenticated user
        
    Returns:
        Cost estimate object
        
    Raises:
        HTTPException: If cost estimate not found (404) or invalid ID format (400)
    """
    try:
        cost_estimate = await services.get(cost_estimate_id)
        if not cost_estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cost estimate not found: {cost_estimate_id}",
            )
        return cost_estimate
        
    except ValueError as e:
        logger.warning(f"Invalid cost_estimate_id format: {cost_estimate_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost estimate: {str(e)}",
        )


# Update a cost estimate
@cost_estimates_router.patch(
    "/{cost_estimate_id}",
    response_model=CostEstimateOut,
    summary="Update a cost estimate",
    description="Update an existing cost estimate.",
)
async def update_cost_estimate(
    cost_estimate_id: str = Path(..., description="Cost estimate ID (MongoDB ObjectId as string)"),
    data: CostEstimateUpdate = ...,
    current_user: dict = Depends(get_current_user),
):
    """
    Update a cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        data: Cost estimate update data
        current_user: Authenticated user
        
    Returns:
        Updated cost estimate object
        
    Raises:
        HTTPException: If cost estimate not found (404) or invalid ID format (400)
    """
    try:
        cost_estimate = await services.update(cost_estimate_id, data)
        return cost_estimate
        
    except ValueError as e:
        logger.warning(f"Invalid cost_estimate_id format: {cost_estimate_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cost estimate: {str(e)}",
        )


# Delete a cost estimate
@cost_estimates_router.delete(
    "/{cost_estimate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cost estimate",
    description="Delete a cost estimate by ID.",
)
async def delete_cost_estimate(
    cost_estimate_id: str = Path(..., description="Cost estimate ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        current_user: Authenticated user
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException: If cost estimate not found (404) or invalid ID format (400)
    """
    try:
        deleted = await services.delete(cost_estimate_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cost estimate not found: {cost_estimate_id}",
            )
        return None
        
    except ValueError as e:
        logger.warning(f"Invalid cost_estimate_id format: {cost_estimate_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cost estimate: {str(e)}",
        )

