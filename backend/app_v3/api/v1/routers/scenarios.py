"""
Scenario router for CRUD operations.

This module provides FastAPI endpoints for scenario management:
- Create, Read, Update, Delete (CRUD) operations
- List scenarios for a project
- Run analysis for a scenario
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
# Import project services and orchestration
from ....domain.projects import services as project_services
from ....domain.projects.orchestration import ProjectOrchestrationService
from ....domain.projects.schemas import ProjectStatus, ProjectUpdate

logger = logging.getLogger(__name__)

# Create router with prefix and tags
# All routes will be under /api/v1/scenarios
scenarios_router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

# Global orchestration service instance (will be injected in main.py)
_orchestration_service: Optional[ProjectOrchestrationService] = None


def set_orchestration_service(service: ProjectOrchestrationService) -> None:
    """Set the global orchestration service instance."""
    global _orchestration_service
    _orchestration_service = service
    logger.info("Project orchestration service set for scenarios router")


def _get_orchestration_service() -> ProjectOrchestrationService:
    """Get the global orchestration service instance."""
    if _orchestration_service is None:
        raise RuntimeError("Orchestration service not initialized")
    return _orchestration_service


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


@scenarios_router.post(
    "/{scenario_id}/run-analysis",
    summary="Run or re-run analysis for a scenario",
    description="Trigger document processing and analysis for a scenario. Requires objective details and project documents to be uploaded.",
)
async def run_analysis(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
):
    """
    Run or re-run analysis for a scenario.
    
    This endpoint triggers the document processing and analysis pipeline for a scenario.
    It requires that:
    - The scenario has global objective details set
    - The project has at least one base case document uploaded
    
    Args:
        scenario_id: MongoDB ObjectId as string
        
    Returns:
        Dictionary with analysis status and job information
        
    Raises:
        HTTPException: If scenario not found (404), missing requirements (400), or processing fails (500)
    """
    try:
        # Validate scenario exists
        scenario = await services.get(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        
        # Validate objective requirements
        if not scenario.global_objective_type or not scenario.global_objective_target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Global objective details are required. Please set objective type and target first.",
            )
        
        # Get project to access documents
        project = await project_services.get(scenario.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {scenario.project_id}",
            )
        
        # Validate project has base case documents
        if not project.base_case_documents or len(project.base_case_documents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one base case document is required. Please upload documents in the project Sources tab first.",
            )
        
        # Update scenario status to processing
        status_patch = ScenarioUpdate(status=ScenarioStatus.PROCESSING)
        await services.update(scenario_id, status_patch)
        
        # Trigger document processing via orchestration service
        orchestration = _get_orchestration_service()
        processing_result = await orchestration.process_project_documents(
            project_id=scenario.project_id,
            global_objective_type=scenario.global_objective_type,
            global_objective_target=scenario.global_objective_target,
            base_case_document_ids=project.base_case_documents,
            tabular_data_document_ids=project.tabular_data_documents or [],
        )
        
        logger.info(f"Analysis started for scenario {scenario_id} (project: {scenario.project_id})")
        
        return {
            "scenario_id": scenario_id,
            "project_id": scenario.project_id,
            "status": "processing",
            "message": "Analysis started successfully",
            "processing_result": processing_result,
        }
        
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Orchestration service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processing service not available",
        )
    except Exception as e:
        logger.error(f"Error running analysis for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run analysis: {str(e)}",
        )

