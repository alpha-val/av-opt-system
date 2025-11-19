"""
Scenario router for CRUD operations.

This module provides FastAPI endpoints for scenario management:
- Create, Read, Update, Delete (CRUD) operations
- List scenarios for a project
- Run analysis for a scenario
"""
import logging
import asyncio
import uuid
from typing import List, Optional, Dict
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
# Import MongoDB client for direct queries
from ....adapters.mongo.client import db
# Import progress tracking
from ....domain.progress.events import ProgressEvent, Stage, Status
from .websocket import get_progress_publisher
# Import file storage
from ....domain.projects.file_storage import FileStorageService

logger = logging.getLogger(__name__)

# Create router with prefix and tags
# All routes will be under /api/v1/scenarios
scenarios_router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

# Global orchestration service instance (will be injected in main.py)
_orchestration_service: Optional[ProjectOrchestrationService] = None
# Global file storage service instance
_file_storage_service: Optional[FileStorageService] = None
# Background task registry for V3 analysis
_analysis_v3_tasks: Dict[str, asyncio.Task] = {}
# Background task registry for V4 analysis
_analysis_v4_tasks: Dict[str, asyncio.Task] = {}


def set_orchestration_service(service: ProjectOrchestrationService) -> None:
    """Set the global orchestration service instance."""
    global _orchestration_service
    _orchestration_service = service
    logger.info("Project orchestration service set for scenarios router")


def set_file_storage_service(service: FileStorageService) -> None:
    """Set the global file storage service instance."""
    global _file_storage_service
    _file_storage_service = service
    logger.info("File storage service set for scenarios router")


def _get_orchestration_service() -> ProjectOrchestrationService:
    """Get the global orchestration service instance."""
    if _orchestration_service is None:
        raise RuntimeError("Orchestration service not initialized")
    return _orchestration_service


def _get_file_storage_service() -> FileStorageService:
    """Get the global file storage service instance."""
    if _file_storage_service is None:
        raise RuntimeError("File storage service not initialized")
    return _file_storage_service

# Create a new scenario
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

# List all scenarios
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

# Get a scenario by ID
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


# Update a scenario
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


# Delete a scenario
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


# Run or re-run analysis for a scenario
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


# Run or re-run analysis for a scenario (V2 workflow)
@scenarios_router.post(
    "/{scenario_id}/run-analysis-v2",
    summary="Run or re-run analysis for a scenario (V2 workflow)",
    description="Trigger document processing and analysis for a scenario using V2 workflow (recommendations-first approach). Requires objective details and project documents to be uploaded.",
)
async def run_analysis_v2(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    extract_summary: bool = Query(False, description="Whether to extract document summary"),
    extraction_scope: str = Query("exact", description="Extraction scope: 'exact', 'with_relationships', or 'with_context'"),
    current_user: dict = Depends(get_current_user),
):
    """
    Run analysis for a scenario using V2 workflow.
    
    V2 workflow:
    1. First analyzes the document to generate recommendations and identify relevant entities
    2. Then extracts only those relevant entities (more targeted and efficient)
    
    Args:
        scenario_id: Scenario identifier
        extract_summary: Whether to extract document summary (default: False)
        extraction_scope: "exact" (only specified entities), "with_relationships" 
                         (entities + direct relationships), or "with_context" 
                         (entities + related entities in same context)
        current_user: Authenticated user
    
    Returns:
        Analysis results with recommendations, entities, and statistics
    """
    try:
        # Get user_id from authenticated user
        user_id = str(current_user["_id"])
        
        # Validate scenario_id format
        try:
            from bson import ObjectId
            ObjectId(scenario_id)
        except Exception:
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")
        
        # Get scenario
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
        
        # Validate extraction_scope
        if extraction_scope not in ["exact", "with_relationships", "with_context"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid extraction_scope: {extraction_scope}. Must be 'exact', 'with_relationships', or 'with_context'.",
            )
        
        # Update scenario status to processing
        status_patch = ScenarioUpdate(status=ScenarioStatus.PROCESSING)
        await services.update(scenario_id, status_patch)
        
        # Get orchestration service
        orchestration = _get_orchestration_service()
        
        # Process each base case document using extract_base_case_entities_v2
        document_results = []
        errors = []
        
        # Process each base case document using extract_base_case_entities_v2
        for document_id in project.base_case_documents:
            try:
                logger.info(
                    f"Processing base case document {document_id} for scenario {scenario_id} (V2 workflow)"
                )
                
                # Extract entities from a base case document using V2 workflow (recommendations-first approach)
                result = await orchestration.extract_base_case_entities_v2(
                    project_id=scenario.project_id,
                    document_id=document_id,
                    global_objective_type=scenario.global_objective_type,
                    global_objective_target=scenario.global_objective_target,
                    user_id=user_id,
                    scenario_id=scenario_id,
                    objective_description=scenario.objective_description,
                    extract_summary=extract_summary,
                    extraction_scope=extraction_scope,
                )
                
                # Append document results
                document_results.append({
                    "document_id": document_id,
                    "status": result.get("processing_status", "unknown"),
                    "entities_extracted": result.get("entities_extracted", 0),
                    "relations_extracted": result.get("relations_extracted", 0),
                    "summary_id": result.get("summary_id"),
                    "recommendations_id": result.get("recommendations_id"),
                    "relevant_entities_count": result.get("relevant_entities_count", 0),
                    "recommendations_count": len(result.get("recommendations", [])),
                    "extraction_scope": result.get("extraction_scope", extraction_scope),
                })
                
                # Append errors
                if result.get("processing_status") == "error":
                    errors.append({
                        "document_id": document_id,
                        "error": result.get("error", "Unknown error"),
                    })
                elif result.get("processing_status") == "warning":
                    errors.append({
                        "document_id": document_id,
                        "warning": result.get("message", "Warning occurred"),
                    })
                    
            except Exception as e:
                logger.error(
                    f"Error processing document {document_id} for scenario {scenario_id} (V2): {e}",
                    exc_info=True
                )
                errors.append({
                    "document_id": document_id,
                    "error": str(e),
                })
                
                # Append document results
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
            f"Analysis (V2) completed for scenario {scenario_id}: "
            f"{len(document_results)} documents processed, {len(errors)} errors/warnings"
        )
        
        return {
            "scenario_id": scenario_id,
            "project_id": scenario.project_id,
            "status": final_status.value,
            "workflow_version": "v2",
            "message": "Analysis completed" if not errors else f"Analysis completed with {len(errors)} error(s)/warning(s)",
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
        logger.error(f"Error running analysis (V2) for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run analysis: {str(e)}",
        )


# Get recommendations for a scenario
@scenarios_router.get(
    "/{scenario_id}/recommendations",
    summary="Get recommendations for a scenario",
    description="Retrieve base case recommendations and relevant entities for a scenario",
)
async def get_scenario_recommendations(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get recommendations for a scenario.
    
    Returns recommendations document(s) from base_case_recommendations collection
    that match the scenario_id. Includes recommendations array and relevant_entities
    if available (v2 workflow).
    
    Args:
        scenario_id: Scenario identifier
        current_user: Authenticated user
    
    Returns:
        Recommendations document(s) with recommendations and relevant_entities
    """
    try:
        # Validate scenario_id format
        try:
            from bson import ObjectId
            ObjectId(scenario_id)
        except Exception:
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")
        
        # Verify scenario exists and user has access
        scenario = await services.get(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        
        # Query base_case_recommendations collection
        recommendations_collection = db().base_case_recommendations
        recommendations_docs = list(
            recommendations_collection.find({"scenario_id": scenario_id})
        )
        
        if not recommendations_docs:
            return {
                "scenario_id": scenario_id,
                "recommendations": [],
                "relevant_entities": [],
                "count": 0,
            }
        
        # Convert MongoDB documents to dictionaries and remove _id
        result = []
        for doc in recommendations_docs:
            doc_dict = dict(doc)
            # Convert ObjectId to string if present
            if "_id" in doc_dict:
                doc_dict["id"] = str(doc_dict["_id"])
                del doc_dict["_id"]
            result.append(doc_dict)
        
        # If multiple documents, return all; otherwise return single document structure
        if len(result) == 1:
            return result[0]
        else:
            return {
                "scenario_id": scenario_id,
                "recommendations_documents": result,
                "count": len(result),
            }
            
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendations for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendations: {str(e)}",
        )


# Get entities for a scenario
@scenarios_router.get(
    "/{scenario_id}/entities",
    summary="Get entities for a scenario",
    description="Retrieve entities from the entities collection filtered by scenario_id and artifact_type",
)
async def get_scenario_entities(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    artifact_type: str = Query("base_case", description="Artifact type filter (default: base_case)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get entities for a scenario.
    
    Returns entities from the entities collection that match the scenario_id
    and artifact_type. Entities are filtered by properties.scenario_id and
    properties.artifact_type.
    
    Args:
        scenario_id: Scenario identifier
        artifact_type: Artifact type filter (default: "base_case")
        current_user: Authenticated user
    
    Returns:
        List of entity dictionaries with id, type, and properties
    """
    try:
        # Validate scenario_id format
        try:
            from bson import ObjectId
            ObjectId(scenario_id)
        except Exception:
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")
        
        # Verify scenario exists and user has access
        scenario = await services.get(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )
        
        # Query entities collection
        entities_collection = db().entities
        query = {
            "properties.scenario_id": scenario_id,
            "properties.artifact_type": artifact_type,
        }
        
        entities = list(entities_collection.find(query, {"_id": 0}))
        
        # Convert ObjectId to string if present in nested structures
        for entity in entities:
            if "_id" in entity:
                entity["id"] = str(entity["_id"])
                del entity["_id"]
            elif "id" not in entity and "_id" in entity:
                entity["id"] = str(entity["_id"])
        
        logger.info(
            f"Retrieved {len(entities)} entities for scenario {scenario_id} "
            f"with artifact_type {artifact_type}"
        )
        
        return {
            "scenario_id": scenario_id,
            "artifact_type": artifact_type,
            "entities": entities,
            "count": len(entities),
        }
            
    except ValueError as e:
        logger.warning(f"Invalid scenario_id format: {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entities for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch entities: {str(e)}",
        )


async def _run_analysis_background_v3(
    job_id: str,
    scenario_id: str,
    project_id: str,
    user_id: str,
    global_objective_type: str,
    global_objective_target: str,
    objective_description: Optional[str],
    base_case_document_ids: List[str],
):
    """
    Background async function for V3 analysis.
    
    Args:
        job_id: Unique job identifier for progress tracking
        scenario_id: Scenario identifier
        project_id: Project identifier
        user_id: User identifier
        global_objective_type: Type of global objective
        global_objective_target: Target magnitude of change
        objective_description: Optional description of the global objective
        base_case_document_ids: List of base case document IDs
    """
    logger.info(
        f"[Background Task] Starting V3 analysis for job {job_id}, scenario {scenario_id}"
    )
    try:
        publisher = get_progress_publisher()
        orchestration = _get_orchestration_service()
        file_storage = _get_file_storage_service()
        
        from ....domain.parsing.utils.text_utils import extract_and_clean, extract_fulltext
        
        # Emit start event
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.PROCESSING,
                status=Status.STARTED,
                progress=0,
                seq=0,
                meta={
                    "scenario_id": scenario_id,
                    "project_id": project_id,
                    "total_documents": len(base_case_document_ids),
                    "current_stage": "Starting V3 analysis",
                },
            ),
        )
        
        # Step 1: Read base case documents
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.PROCESSING,
                status=Status.IN_PROGRESS,
                progress=10,
                seq=1,
                meta={
                    "current_stage": "Reading base case documents",
                },
            ),
        )
        
        documents = await orchestration._read_base_case_documents_v3(
            base_case_document_ids, file_storage
        )
        
        if not documents:
            raise ValueError("No base case documents could be retrieved")
        
        document_results = []
        all_recommendations = []
        all_relevant_entities = []
        
        # Process each document
        for idx, doc in enumerate(documents, 1):
            document_id = doc["document_id"]
            file_bytes = doc["file_bytes"]
            filename = doc["filename"]
            
            # Extract text from PDF
            _, _, _, pages_clean = extract_and_clean(file_bytes, filename)
            full_text = extract_fulltext(pages_clean)
            
            # Step 2: Extract recommendations
            publisher.publish(
                job_id,
                ProgressEvent(
                    job_id=job_id,
                    stage=Stage.PROCESSING,
                    status=Status.IN_PROGRESS,
                    progress=30 + int((idx - 1) / len(documents) * 30),
                    seq=idx * 2,
                    meta={
                        "current_stage": f"Extracting recommendations for document {idx}/{len(documents)}: {filename}",
                        "document_id": document_id,
                    },
                ),
            )
            
            rec_result = await orchestration._extract_recommendations_v3_chunked(
                full_text=full_text,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                objective_description=objective_description,
                document_id=document_id,
            )
            
            recommendations = rec_result.get("recommendations", [])
            entities_for_costing = rec_result.get("entities_for_costing", [])
            all_recommendations.extend(recommendations)
            
            # Step 3: Retrieve relevant entities from MongoDB
            publisher.publish(
                job_id,
                ProgressEvent(
                    job_id=job_id,
                    stage=Stage.PROCESSING,
                    status=Status.IN_PROGRESS,
                    progress=60 + int((idx - 1) / len(documents) * 20),
                    seq=idx * 2 + 1,
                    meta={
                        "current_stage": f"Retrieving relevant entities from MongoDB for document {idx}/{len(documents)}",
                        "document_id": document_id,
                    },
                ),
            )
            
            relevant_entities = await orchestration._retrieve_relevant_entities_v3(
                project_id=project_id,
                scenario_id=scenario_id,
                recommendations=recommendations,
                entities_for_costing=entities_for_costing,
                artifact_type="base_case",
            )
            for entity in relevant_entities:
                logger.info(f"Relevant entity: {entity}")
                logger.info(f"Entity type: {entity['type']}")
                logger.info(f"Entity properties: {entity['properties']}")
                logger.info(f"Entity id: {entity['id']}")
                logger.info(f"Entity scenario_id: {entity['properties'].get('scenario_id')}")
                logger.info(f"Entity artifact_type: {entity['properties'].get('artifact_type')}")
                logger.info(f"Entity name: {entity['properties'].get('name')}")
                logger.info(f"Entity discipline: {entity['properties'].get('discipline')}")
                logger.info(f"Entity category: {entity['properties'].get('category')}")
                logger.info(f"Entity subcategory: {entity['properties'].get('subcategory')}")
                logger.info(f"Entity entity: {entity['properties'].get('entity')}")
                logger.info(f"Entity extraction_priority: {entity['properties'].get('extraction_priority')}")
                logger.info(f"Entity extraction_rationale: {entity['properties'].get('extraction_rationale')}")
                logger.info(f"Entity expected_attributes: {entity['properties'].get('expected_attributes')}")
                logger.info(f"Entity priority: {entity['properties'].get('priority')}")
                logger.info(f"Entity rationale: {entity['properties'].get('rationale')}")
                logger.info(f"Entity expected_attributes: {entity['properties'].get('expected_attributes')}")
                logger.info(f"Entity priority: {entity['properties'].get('priority')}")
                logger.info(f"Entity rationale: {entity['properties'].get('rationale')}")
                logger.info(f"Entity expected_attributes: {entity['properties'].get('expected_attributes')}")
                logger.info(f"Entity priority: {entity['properties'].get('priority')}")
                logger.info(f"Entity rationale: {entity['properties'].get('rationale')}")
                logger.info(f"Entity expected_attributes: {entity['properties'].get('expected_attributes')}")
            all_relevant_entities.extend(relevant_entities)
            
            # Step 4: Store recommendations
            recommendations_id = await orchestration._store_recommendations_v3(
                document_id=document_id,
                project_id=project_id,
                scenario_id=scenario_id,
                user_id=user_id,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                recommendations=recommendations,
                relevant_entities=relevant_entities,
                overwrite=True,
            )
            
            document_results.append({
                "document_id": document_id,
                "filename": filename,
                "status": "completed",
                "recommendations_count": len(recommendations),
                "relevant_entities_count": len(relevant_entities),
                "recommendations_id": recommendations_id,
            })
        
        # Update scenario status
        status_patch = ScenarioUpdate(status=ScenarioStatus.COMPLETED)
        await services.update(scenario_id, status_patch)
        
        # Emit completion event
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.COMPLETE,
                status=Status.COMPLETED,
                progress=100,
                seq=len(documents) * 2 + 2,
                meta={
                    "current_stage": "Analysis completed",
                    "documents_processed": len(document_results),
                    "total_recommendations": len(all_recommendations),
                    "total_relevant_entities": len(all_relevant_entities),
                },
            ),
        )
        
        logger.info(
            f"[Background Task] V3 analysis completed for job {job_id}, scenario {scenario_id}: "
            f"{len(document_results)} documents processed"
        )
        
    except Exception as e:
        logger.error(
            f"[Background Task] Error in V3 analysis for job {job_id}, scenario {scenario_id}: {e}",
            exc_info=True,
        )
        
        # Update scenario status to failed
        try:
            status_patch = ScenarioUpdate(status=ScenarioStatus.FAILED)
            await services.update(scenario_id, status_patch)
        except Exception as update_error:
            logger.error(f"Failed to update scenario status: {update_error}")
        
        # Emit failure event
        publisher = get_progress_publisher()
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.ERROR,
                status=Status.FAILED,
                progress=0,
                seq=999,
                meta={
                    "current_stage": "Analysis failed",
                    "error": str(e),
                },
            ),
        )
    finally:
        # Clean up task registry
        if job_id in _analysis_v3_tasks:
            del _analysis_v3_tasks[job_id]

@scenarios_router.post(
    "/{scenario_id}/run-analysis-v3",
    summary="Run or re-run analysis for a scenario (V3 workflow)",
    description="Trigger document processing and analysis for a scenario using V3 workflow (MongoDB entity retrieval). Requires objective details and project documents to be uploaded.",
)
async def run_analysis_v3(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Run analysis for a scenario using V3 workflow.
    
    V3 workflow:
    1. Reads base case documents from GridFS
    2. Extracts recommendations using LLM (simplified, no entity extraction)
    3. Retrieves existing entities from MongoDB based on recommendations
    4. Creates placeholder entities if no matches found
    5. Returns recommendations + relevant_entities
    
    Args:
        scenario_id: Scenario identifier
        current_user: Authenticated user
    
    Returns:
        Response with job_id, status, and websocket_url for progress tracking
    """
    try:
        # Get user_id from authenticated user
        user_id = str(current_user["_id"])
        
        # Validate scenario_id format
        try:
            from bson import ObjectId
            ObjectId(scenario_id)
        except Exception:
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")
        
        # Get scenario
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
        
        # Generate job_id
        job_id = str(uuid.uuid4())
        
        # Create background task
        task = asyncio.create_task(
            _run_analysis_background_v3(
                job_id=job_id,
                scenario_id=scenario_id,
                project_id=scenario.project_id,
                user_id=user_id,
                global_objective_type=scenario.global_objective_type,
                global_objective_target=scenario.global_objective_target,
                objective_description=scenario.objective_description,
                base_case_document_ids=project.base_case_documents,
            )
        )
        
        # Store task in registry
        _analysis_v3_tasks[job_id] = task
        
        # Yield control to allow task to start
        await asyncio.sleep(0)
        
        # Return immediately with job_id
        return {
            "job_id": job_id,
            "scenario_id": scenario_id,
            "status": "queued",
            "message": "Analysis started. Connect to WebSocket endpoint for progress updates.",
            "websocket_url": f"/api/v1/ws/progress/{job_id}",
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
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not available",
        )
    except Exception as e:
        logger.error(f"Error starting V3 analysis for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}",
        )


@scenarios_router.post(
    "/{scenario_id}/run-analysis-v4",
    summary="Run or re-run analysis for a scenario (V4 workflow)",
    description="Trigger document processing and analysis for a scenario using V4 workflow (Objective-driven nodes and relations extraction). Requires objective details and project documents to be uploaded.",
)
async def run_analysis_v4(
    scenario_id: str = Path(..., description="Scenario ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Run analysis for a scenario using V4 workflow.
    
    V4 workflow:
    1. Reads base case documents from GridFS
    2. Extracts objective-driven nodes and relations using LLM
    3. Stores extracted entities and edges in MongoDB
    
    Args:
        scenario_id: Scenario identifier
        current_user: Authenticated user
    
    Returns:
        Response with job_id, status, and websocket_url for progress tracking
    """
    try:
        # Get user_id from authenticated user
        user_id = str(current_user["_id"])
        
        # Validate scenario_id format
        try:
            from bson import ObjectId
            ObjectId(scenario_id)
        except Exception:
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")
        
        # Get scenario
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
        
        # Generate job_id
        job_id = str(uuid.uuid4())
        
        # Create background task
        task = asyncio.create_task(
            _run_analysis_background_v4(
                job_id=job_id,
                scenario_id=scenario_id,
                project_id=scenario.project_id,
                user_id=user_id,
                global_objective_type=scenario.global_objective_type,
                global_objective_target=scenario.global_objective_target,
                objective_description=scenario.objective_description,
                base_case_document_ids=project.base_case_documents,
            )
        )
        
        # Store task in registry
        _analysis_v4_tasks[job_id] = task
        
        # Yield control to allow task to start
        await asyncio.sleep(0)
        
        # Return immediately with job_id
        return {
            "job_id": job_id,
            "scenario_id": scenario_id,
            "status": "queued",
            "message": "Analysis started. Connect to WebSocket endpoint for progress updates.",
            "websocket_url": f"/api/v1/ws/progress/{job_id}",
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
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not available",
        )
    except Exception as e:
        logger.error(f"Error starting V4 analysis for scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}",
        )


async def _run_analysis_background_v4(
    job_id: str,
    scenario_id: str,
    project_id: str,
    user_id: str,
    global_objective_type: str,
    global_objective_target: str,
    objective_description: Optional[str],
    base_case_document_ids: List[str],
):
    """
    Background async function for V4 analysis.
    
    Args:
        job_id: Unique job identifier for progress tracking
        scenario_id: Scenario identifier
        project_id: Project identifier
        user_id: User identifier
        global_objective_type: Type of global objective
        global_objective_target: Target magnitude of change
        objective_description: Optional description of the global objective
        base_case_document_ids: List of base case document IDs
    """
    logger.info(
        f"[Background Task] Starting V4 analysis for job {job_id}, scenario {scenario_id}"
    )
    try:
        publisher = get_progress_publisher()
        orchestration = _get_orchestration_service()
        file_storage = _get_file_storage_service()
        
        from ....domain.parsing.utils.text_utils import extract_and_clean, extract_fulltext
        from ....domain.parsing.storage.document_store import DocumentStore
        
        # Emit start event
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.PROCESSING,
                status=Status.STARTED,
                progress=0,
                seq=0,
                meta={
                    "scenario_id": scenario_id,
                    "project_id": project_id,
                    "total_documents": len(base_case_document_ids),
                    "current_stage": "Starting V4 analysis",
                },
            ),
        )
        
        # Step 1: Read base case documents
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.PROCESSING,
                status=Status.IN_PROGRESS,
                progress=10,
                seq=1,
                meta={
                    "current_stage": "Reading base case documents",
                },
            ),
        )
        
        documents = await orchestration._read_base_case_documents_v3(
            base_case_document_ids, file_storage
        )
        
        if not documents:
            raise ValueError("No base case documents could be retrieved")
        
        document_results = []
        all_nodes = []
        all_edges = []
        
        # Process each document
        for idx, doc in enumerate(documents, 1):
            document_id = doc["document_id"]
            file_bytes = doc["file_bytes"]
            filename = doc["filename"]
            
            # Extract text from PDF
            publisher.publish(
                job_id,
                ProgressEvent(
                    job_id=job_id,
                    stage=Stage.PROCESSING,
                    status=Status.IN_PROGRESS,
                    progress=20 + int((idx - 1) / len(documents) * 30),
                    seq=idx * 2,
                    meta={
                        "current_stage": f"Extracting text from document {idx}/{len(documents)}: {filename}",
                        "document_id": document_id,
                    },
                ),
            )
            
            _, _, _, pages_clean = extract_and_clean(file_bytes, filename)
            full_text = extract_fulltext(pages_clean)
            
            # Step 2: Extract objective-driven nodes and relations
            publisher.publish(
                job_id,
                ProgressEvent(
                    job_id=job_id,
                    stage=Stage.PROCESSING,
                    status=Status.IN_PROGRESS,
                    progress=50 + int((idx - 1) / len(documents) * 30),
                    seq=idx * 2 + 1,
                    meta={
                        "current_stage": f"Extracting nodes and relations for document {idx}/{len(documents)}: {filename}",
                        "document_id": document_id,
                    },
                ),
            )
            
            extraction_result = await orchestration._extract_objective_driven_nodes_and_relations_v4(
                full_text=full_text,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                objective_description=objective_description,
                document_id=document_id,
            )
            
            nodes = extraction_result.get("nodes", [])
            edges = extraction_result.get("edges", [])
            
            # Add metadata to nodes and edges
            for node in nodes:
                if "properties" not in node:
                    node["properties"] = {}
                node["properties"].update({
                    "project_id": project_id,
                    "scenario_id": scenario_id,
                    "user_id": user_id,
                    "doc_id": document_id,
                    "artifact_type": "base_case",
                })
            
            for edge in edges:
                if "properties" not in edge:
                    edge["properties"] = {}
                edge["properties"].update({
                    "project_id": project_id,
                    "scenario_id": scenario_id,
                    "user_id": user_id,
                    "doc_id": document_id,
                    "artifact_type": "base_case",
                })
            
            all_nodes.extend(nodes)
            all_edges.extend(edges)
            
            # Step 3: Store nodes and edges in MongoDB
            publisher.publish(
                job_id,
                ProgressEvent(
                    job_id=job_id,
                    stage=Stage.PROCESSING,
                    status=Status.IN_PROGRESS,
                    progress=80 + int((idx - 1) / len(documents) * 15),
                    seq=idx * 2 + 2,
                    meta={
                        "current_stage": f"Storing entities and relations for document {idx}/{len(documents)}",
                        "document_id": document_id,
                        "nodes_count": len(nodes),
                        "edges_count": len(edges),
                    },
                ),
            )
            
            document_store = DocumentStore()
            entities_stored = document_store.bulk_upsert_entities(nodes)
            edges_stored = document_store.bulk_upsert_relations(edges)
            
            document_results.append({
                "document_id": document_id,
                "filename": filename,
                "status": "completed",
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "entities_stored": entities_stored,
                "edges_stored": edges_stored,
            })
        
        # Update scenario status
        status_patch = ScenarioUpdate(status=ScenarioStatus.COMPLETED)
        await services.update(scenario_id, status_patch)
        
        # Emit completion event
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.COMPLETE,
                status=Status.COMPLETED,
                progress=100,
                seq=len(documents) * 3 + 1,
                meta={
                    "current_stage": "Analysis completed",
                    "documents_processed": len(document_results),
                    "total_nodes": len(all_nodes),
                    "total_edges": len(all_edges),
                },
            ),
        )
        
        logger.info(
            f"[Background Task] V4 analysis completed for job {job_id}, scenario {scenario_id}: "
            f"{len(document_results)} documents processed, "
            f"{len(all_nodes)} nodes, {len(all_edges)} edges extracted"
        )
        
    except Exception as e:
        logger.error(
            f"[Background Task] Error in V4 analysis for job {job_id}, scenario {scenario_id}: {e}",
            exc_info=True,
        )
        
        # Update scenario status to failed
        try:
            status_patch = ScenarioUpdate(status=ScenarioStatus.FAILED)
            await services.update(scenario_id, status_patch)
        except Exception as update_error:
            logger.error(f"Failed to update scenario status: {update_error}")
        
        # Emit failure event
        publisher = get_progress_publisher()
        publisher.publish(
            job_id,
            ProgressEvent(
                job_id=job_id,
                stage=Stage.ERROR,
                status=Status.FAILED,
                progress=0,
                seq=999,
                meta={
                    "current_stage": "Analysis failed",
                    "error": str(e),
                },
            ),
        )
    finally:
        # Clean up task registry
        if job_id in _analysis_v4_tasks:
            del _analysis_v4_tasks[job_id]