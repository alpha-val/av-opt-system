"""
Scenario router for CRUD operations.

This module provides FastAPI endpoints for scenario management:
- Create, Read, Update, Delete (CRUD) operations
- List scenarios for a project
- Run analysis for a scenario
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Path, Query, Depends
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
# Import auth for user authentication
from .auth import get_current_user

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
    current_user: dict = Depends(get_current_user),
):
    """
    Run or re-run analysis for a scenario.
    
    This endpoint triggers the document processing and analysis pipeline for a scenario.
    It requires that:
    - The scenario has global objective details set
    - The project has at least one base case document uploaded
    
    The endpoint processes each base case document using extract_base_case_entities,
    which extracts entities, generates summaries, recommendations, and identifies
    entities for cost estimation.
    
    Args:
        scenario_id: MongoDB ObjectId as string
        current_user: Authenticated user (from dependency injection)
        
    Returns:
        Dictionary with analysis status and results for each document
        
    Raises:
        HTTPException: If scenario not found (404), missing requirements (400), or processing fails (500)
    """
    try:
        # Get user_id from authenticated user
        user_id = str(current_user["_id"])
        
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
        
        # Get orchestration service
        orchestration = _get_orchestration_service()
        
        # Process each base case document using extract_base_case_entities
        document_results = []
        errors = []
        
        for document_id in project.base_case_documents:
            try:
                logger.info(
                    f"Processing base case document {document_id} for scenario {scenario_id}"
                )
                
                result = await orchestration.extract_base_case_entities(
                    project_id=scenario.project_id,
                    document_id=document_id,
                    global_objective_type=scenario.global_objective_type,
                    global_objective_target=scenario.global_objective_target,
                    user_id=user_id,
                    scenario_id=scenario_id,
                    objective_description=scenario.objective_description,
                )
                
                document_results.append({
                    "document_id": document_id,
                    "status": result.get("processing_status", "unknown"),
                    "entities_extracted": result.get("entities_extracted", 0),
                    "relations_extracted": result.get("relations_extracted", 0),
                    "summary_id": result.get("summary_id"),
                    "recommendations_id": result.get("recommendations_id"),
                    "entities_for_costing_count": len(result.get("entities_for_costing", [])),
                    "recommendations_count": len(result.get("recommendations", [])),
                })
                
                if result.get("processing_status") == "error":
                    errors.append({
                        "document_id": document_id,
                        "error": result.get("error", "Unknown error"),
                    })
                    
            except Exception as e:
                logger.error(
                    f"Error processing document {document_id} for scenario {scenario_id}: {e}",
                    exc_info=True
                )
                errors.append({
                    "document_id": document_id,
                    "error": str(e),
                })
                document_results.append({
                    "document_id": document_id,
                    "status": "error",
                    "error": str(e),
                })
        
        # Update scenario status based on results
        if errors:
            # If there are errors, set status to indicate partial completion
            final_status = ScenarioStatus.PROCESSING if len(errors) < len(project.base_case_documents) else ScenarioStatus.FAILED
        else:
            # All documents processed successfully
            final_status = ScenarioStatus.COMPLETED
        
        status_patch = ScenarioUpdate(status=final_status)
        await services.update(scenario_id, status_patch)
        
        logger.info(
            f"Analysis completed for scenario {scenario_id}: "
            f"{len(document_results)} documents processed, {len(errors)} errors"
        )
        
        return {
            "scenario_id": scenario_id,
            "project_id": scenario.project_id,
            "status": final_status.value,
            "message": "Analysis completed" if not errors else f"Analysis completed with {len(errors)} error(s)",
            "documents_processed": len(document_results),
            "document_results": document_results,
            "errors": errors if errors else None,
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

