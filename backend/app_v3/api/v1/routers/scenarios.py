"""
Scenario router for CRUD operations.

This module provides FastAPI endpoints for scenario management:
- Create, Read, Update, Delete (CRUD) operations
- List scenarios for a project
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Path, Query
from bson.errors import InvalidId

# Import scenario service functions
from ....domain.scenarios import services
from ....domain.scenarios.schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioOut,
    ScenarioStatus,
)

logger = logging.getLogger(__name__)

# Create router with prefix and tags
# All routes will be under /api/v1/scenarios
scenarios_router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@scenarios_router.post(
    "",
    response_model=ScenarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scenario",
    description="Create a new scenario for a project.",
)
async def create_scenario(data: ScenarioCreate):
    """
    Create a new scenario.
    
    Args:
        data: Scenario creation data
        
    Returns:
        Created scenario object
        
    Raises:
        HTTPException: If validation fails (400) or project not found (404)
    """
    try:
        # Validate project exists (optional - can be added if needed)
        # For now, we'll just create the scenario
        
        scenario = await services.create(data)
        return scenario
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scenario: {str(e)}",
        )


@scenarios_router.get(
    "",
    response_model=List[ScenarioOut],
    summary="List scenarios",
    description="List all scenarios, optionally filtered by project_id.",
)
async def list_scenarios(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
):
    """
    List all scenarios.
    
    Args:
        project_id: Optional project ID to filter scenarios
        
    Returns:
        List of scenario objects
    """
    try:
        scenarios = await services.list_all(project_id)
        return scenarios
        
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}",
        )


@scenarios_router.get(
    "/{scenario_id}",
    response_model=ScenarioOut,
    summary="Get scenario by ID",
    description="Retrieve a scenario by its ID.",
)
async def get_scenario(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
):
    """
    Get a scenario by ID.
    
    Args:
        scenario_id: MongoDB ObjectId as string
        
    Returns:
        Scenario object
        
    Raises:
        HTTPException: If scenario not found (404) or invalid ID format (400)
    """
    try:
        scenario = await services.get(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        return scenario
        
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario: {str(e)}",
        )


@scenarios_router.patch(
    "/{scenario_id}",
    response_model=ScenarioOut,
    summary="Update scenario",
    description="Update a scenario by its ID.",
)
async def update_scenario(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    patch: ScenarioUpdate = ...,
):
    """
    Update a scenario.
    
    Args:
        scenario_id: MongoDB ObjectId as string
        patch: Scenario update data
        
    Returns:
        Updated scenario object
        
    Raises:
        HTTPException: If scenario not found (404) or invalid ID format (400)
    """
    try:
        scenario = await services.update(scenario_id, patch)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        return scenario
        
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scenario: {str(e)}",
        )


@scenarios_router.delete(
    "/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scenario",
    description="Delete a scenario by its ID.",
)
async def delete_scenario(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
):
    """
    Delete a scenario.
    
    Args:
        scenario_id: MongoDB ObjectId as string
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException: If scenario not found (404) or invalid ID format (400)
    """
    try:
        deleted = await services.delete(scenario_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        return None
        
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scenario: {str(e)}",
        )

