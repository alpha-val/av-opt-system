"""
FastAPI router for scenario analysis endpoints.

Provides CRUD operations and analysis workflow endpoints for scenarios.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import logging

from ....domain.scenarios.services import ScenarioService
from ....domain.scenarios.schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioOut,
    ScenarioWithAnalysis,
    UserConstraint,
)

logger = logging.getLogger(__name__)

# Initialize service
scenario_service = ScenarioService()

scenarios_router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@scenarios_router.post("/", status_code=status.HTTP_201_CREATED, response_model=ScenarioOut)
async def create_scenario(data: ScenarioCreate):
    """Create a new scenario."""
    try:
        scenario = await scenario_service.create_scenario(data)
        return scenario
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scenario: {str(e)}",
        )


@scenarios_router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(scenario_id: str):
    """Get a scenario by ID."""
    scenario = await scenario_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return scenario


@scenarios_router.get("/{scenario_id}/full", response_model=ScenarioWithAnalysis)
async def get_scenario_with_analysis(scenario_id: str):
    """Get a scenario with all analysis data."""
    scenario = await scenario_service.get_scenario_with_analysis(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return scenario


@scenarios_router.get("/project/{project_id}/list", response_model=List[ScenarioOut])
async def list_scenarios(project_id: str):
    """List all scenarios for a project."""
    try:
        scenarios = await scenario_service.list_scenarios(project_id)
        return scenarios
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}",
        )


@scenarios_router.patch("/{scenario_id}", response_model=ScenarioOut)
async def update_scenario(scenario_id: str, data: ScenarioUpdate):
    """Update a scenario."""
    scenario = await scenario_service.update_scenario(scenario_id, data)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return scenario


@scenarios_router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    success = await scenario_service.delete_scenario(scenario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )


@scenarios_router.post("/{scenario_id}/analyze", response_model=ScenarioWithAnalysis)
async def analyze_scenario(scenario_id: str):
    """
    Run LLM analysis of relevant entities for a scenario.
    
    Identifies local objectives (entity-parameter pairs) relevant to the global objective.
    """
    try:
        scenario = await scenario_service.analyze_scenario(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or analysis failed",
            )
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze scenario: {str(e)}",
        )


@scenarios_router.post("/{scenario_id}/resize", response_model=ScenarioWithAnalysis)
async def resize_system(
    scenario_id: str,
    user_constraints: Optional[List[UserConstraint]] = None,
):
    """
    Apply system resizing based on global objective and user constraints.
    
    Hybrid approach: LLM identifies what to resize, algorithms calculate new values.
    """
    try:
        scenario = await scenario_service.resize_system(scenario_id, user_constraints)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or resizing failed",
            )
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resizing system: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resize system: {str(e)}",
        )


@scenarios_router.post("/{scenario_id}/recommend", response_model=ScenarioWithAnalysis)
async def build_recommendation(scenario_id: str):
    """
    Build system recommendations with approach options.
    
    Analyzes objectives and constraints to generate and rank approach options.
    """
    try:
        scenario = await scenario_service.build_recommendation(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or recommendation building failed",
            )
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build recommendation: {str(e)}",
        )


@scenarios_router.post("/{scenario_id}/cost-estimation", response_model=ScenarioWithAnalysis)
async def prepare_cost_estimation(
    scenario_id: str,
    generate_estimates: bool = Query(False, description="Generate cost estimates if True"),
):
    """
    Prepare cost estimation data.
    
    Identifies cost reference data and prepares cost estimation data.
    Optionally generates cost estimates if generate_estimates=True.
    """
    try:
        scenario = await scenario_service.prepare_cost_estimation(
            scenario_id, generate_estimates=generate_estimates
        )
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or cost estimation preparation failed",
            )
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing cost estimation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prepare cost estimation: {str(e)}",
        )


@scenarios_router.get("/{scenario_id}/report")
async def generate_report(
    scenario_id: str,
    format: str = Query("json", regex="^(json|markdown)$", description="Report format"),
):
    """
    Generate a formatted report for a scenario.
    
    Returns JSON or markdown formatted report with all analysis data.
    """
    try:
        report = await scenario_service.generate_report(scenario_id, format=format)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or report generation failed",
            )
        
        # Return appropriate content type
        from fastapi.responses import Response
        if format == "markdown":
            return Response(
                content=report.get("content", ""),
                media_type="text/markdown",
            )
        else:
            return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )
