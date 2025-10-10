"""
Scenario API endpoints.

Handles creation, retrieval, and management of scenarios.
A scenario represents a what-if analysis with parameter changes.
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app_v2.core.database import get_database
from app_v2.schemas.scenario import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioListResponse,
    ScenarioUpdate,
    ScenarioGenerateOptionsRequest,
    ScenarioStatusUpdate
)
from app_v2.repositories.scenario_repo import ScenarioRepository
from app_v2.repositories.entity_repo import EntityRepository
from app_v2.services.equipment_selector import EquipmentSelector
from app_v2.services.validation import ScenarioValidator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    scenario_data: ScenarioCreate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new scenario.
    
    A scenario defines parameter changes to analyze (e.g., changing crusher
    product size from 8" to 6").
    
    Steps:
    1. Validate scenario data
    2. Create base case snapshot
    3. Store scenario
    4. Return scenario with metadata
    
    Args:
        scenario_data: Scenario creation data
        db: Database connection
        
    Returns:
        Created scenario with ID
        
    Raises:
        HTTPException: If validation fails or creation errors
    """
    try:
        logger.info(
            f"Creating scenario for project",
            extra={"project_id": scenario_data.project_id}
        )
        
        # Initialize repositories
        scenario_repo = ScenarioRepository(db)
        entity_repo = EntityRepository(db)
        validator = ScenarioValidator(db)
        
        # 1. Validate scenario data
        validation_result = await validator.validate_scenario(scenario_data.dict())
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Scenario validation failed",
                    "errors": validation_result["errors"]
                }
            )
        
        # 2. Create base case snapshot
        logger.info("Creating base case snapshot")
        base_case_snapshot = await entity_repo.snapshot_base_case(
            scenario_data.project_id
        )
        
        # 3. Prepare scenario document
        scenario_doc = scenario_data.dict()
        scenario_doc["base_case_snapshot"] = base_case_snapshot
        scenario_doc["status"] = "draft"
        scenario_doc["compute_state"] = "not_started"
        scenario_doc["option_count"] = 0
        
        # 4. Create scenario
        scenario_id = await scenario_repo.create(scenario_doc)
        
        # 5. Retrieve and return
        created_scenario = await scenario_repo.find_by_id(scenario_id)
        
        logger.info(
            f"Created scenario",
            extra={
                "scenario_id": scenario_id,
                "project_id": scenario_data.project_id
            }
        )
        
        return ScenarioResponse(**created_scenario)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create scenario: {str(e)}"
        )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get scenario by ID.
    
    Args:
        scenario_id: Scenario ID
        db: Database connection
        
    Returns:
        Scenario data
        
    Raises:
        HTTPException: If scenario not found
    """
    try:
        scenario_repo = ScenarioRepository(db)
        scenario = await scenario_repo.find_by_id(scenario_id)
        
        if not scenario:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        return ScenarioResponse(**scenario)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve scenario: {str(e)}"
        )


@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    project_id: str = Query(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum to return"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List scenarios for a project.
    
    Args:
        project_id: Project ID
        status: Optional status filter
        skip: Pagination offset
        limit: Maximum results
        db: Database connection
        
    Returns:
        List of scenarios with pagination metadata
    """
    try:
        scenario_repo = ScenarioRepository(db)
        
        # Get scenarios
        scenarios = await scenario_repo.find_by_project(
            project_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # Get total count
        total = await scenario_repo.count({
            "project_id": scenario_id,
            **({"status": status} if status else {})
        })
        
        return ScenarioListResponse(
            scenarios=[ScenarioResponse(**s) for s in scenarios],
            total=total,
            skip=skip,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list scenarios: {str(e)}"
        )


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    update_data: ScenarioUpdate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update scenario.
    
    Args:
        scenario_id: Scenario ID
        update_data: Fields to update
        db: Database connection
        
    Returns:
        Updated scenario
        
    Raises:
        HTTPException: If scenario not found or update fails
    """
    try:
        scenario_repo = ScenarioRepository(db)
        
        # Only update provided fields
        update_dict = update_data.dict(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )
        
        success = await scenario_repo.update(scenario_id, update_dict)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        # Retrieve updated scenario
        updated_scenario = await scenario_repo.find_by_id(scenario_id)
        
        logger.info(
            f"Updated scenario",
            extra={"scenario_id": scenario_id}
        )
        
        return ScenarioResponse(**updated_scenario)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update scenario: {str(e)}"
        )


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete scenario.
    
    Note: This will also delete all associated options.
    
    Args:
        scenario_id: Scenario ID
        db: Database connection
        
    Raises:
        HTTPException: If scenario not found or deletion fails
    """
    try:
        scenario_repo = ScenarioRepository(db)
        
        success = await scenario_repo.delete(scenario_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        # TODO: Delete associated options and entities
        # This should be done in a transaction or background task
        
        logger.info(
            f"Deleted scenario",
            extra={"scenario_id": scenario_id}
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete scenario: {str(e)}"
        )


@router.post("/{scenario_id}/generate-options", status_code=202)
async def generate_options(
    scenario_id: str,
    request: ScenarioGenerateOptionsRequest = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate equipment options for a scenario.
    
    This is the CORE USP endpoint. It:
    1. Analyzes parameter changes
    2. Selects suitable equipment from sizing tables
    3. Estimates costs with full breakdown
    4. Analyzes downstream impacts
    5. Creates option documents
    
    This is an async operation - returns immediately with task ID.
    Use GET /scenarios/{id} to check status.
    
    Args:
        scenario_id: Scenario ID
        request: Generation parameters
        db: Database connection
        
    Returns:
        Task information
        
    Raises:
        HTTPException: If scenario not found or generation fails
    """
    try:
        logger.info(
            f"Generating options for scenario",
            extra={"scenario_id": scenario_id}
        )
        
        scenario_repo = ScenarioRepository(db)
        
        # Get scenario
        scenario = await scenario_repo.find_by_id(scenario_id)
        
        if not scenario:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        # Update status
        await scenario_repo.update_status(
            scenario_id,
            status="processing",
            compute_state="equipment_selection"
        )
        
        # TODO: Trigger async task for option generation
        # For now, we'll import and call directly
        # In production, use Celery or similar task queue
        
        from ...services.option_generator import OptionGenerator
        
        generator = OptionGenerator(db)
        
        # Generate options asynchronously
        # This should be wrapped in a background task
        result = await generator.generate_options(
            scenario_id=scenario_id,
            max_options=request.max_options,
            filters=request.filters
        )
        
        logger.info(
            f"Generated {result['options_created']} options",
            extra={"scenario_id": scenario_id}
        )
        
        return {
            "scenario_id": scenario_id,
            "status": "processing",
            "message": "Option generation started",
            "options_created": result["options_created"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating options: {e}", exc_info=True)
        
        # Update scenario status to error
        try:
            await scenario_repo.update_status(
                scenario_id,
                status="error",
                compute_state="failed"
            )
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate options: {str(e)}"
        )


@router.post("/{scenario_id}/status", response_model=ScenarioResponse)
async def update_scenario_status(
    scenario_id: str,
    status_update: ScenarioStatusUpdate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update scenario status.
    
    Args:
        scenario_id: Scenario ID
        status_update: Status update data
        db: Database connection
        
    Returns:
        Updated scenario
        
    Raises:
        HTTPException: If scenario not found
    """
    try:
        scenario_repo = ScenarioRepository(db)
        
        success = await scenario_repo.update_status(
            scenario_id,
            status=status_update.status,
            compute_state=status_update.compute_state
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        updated_scenario = await scenario_repo.find_by_id(scenario_id)
        
        return ScenarioResponse(**updated_scenario)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status: {str(e)}"
        )


@router.get("/{scenario_id}/summary")
async def get_scenario_summary(
    scenario_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get scenario summary with aggregated data.
    
    Includes:
    - Option count and status breakdown
    - Cost range (min/max across options)
    - Key metrics
    
    Args:
        scenario_id: Scenario ID
        db: Database connection
        
    Returns:
        Scenario summary
    """
    try:
        scenario_repo = ScenarioRepository(db)
        
        # Get scenario with options count
        scenarios = await scenario_repo.get_with_options_count(scenario_id)
        
        if not scenarios:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_id} not found"
            )
        
        scenario = scenarios[0]
        
        # TODO: Add option statistics (cost ranges, etc.)
        # This would involve querying the option repository
        
        return {
            "scenario": ScenarioResponse(**scenario),
            "option_count": scenario.get("option_count", 0),
            # Add more aggregated data here
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get summary: {str(e)}"
        )