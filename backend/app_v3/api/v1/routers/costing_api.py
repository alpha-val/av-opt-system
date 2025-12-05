"""
Costing API router for component-based cost estimates.

This module provides FastAPI endpoints for creating cost estimates from
SystemDesign component selections.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Path
from typing import List, Optional

from ....domain.costing_pipeline import schemas
from ....domain.costing_pipeline import repository as costing_repo
from ....domain.costing_pipeline.component_matcher import match_component_with_tabular_entities
from ....domain.costing_pipeline.cost_calculator import (
    extract_component_costs,
    calculate_baseline_vs_redesigned,
)
from ....domain.costing_pipeline.report_builder import build_cost_comparison_report
from ....domain.scenarios import services as scenario_services
from ....domain.scenarios import repository as scenario_repo
from .auth import get_current_user

logger = logging.getLogger(__name__)

# Create router with prefix and tags
costing_router = APIRouter(prefix="/api/v1/costing", tags=["costing"])


@costing_router.post(
    "/estimate",
    response_model=schemas.ComponentCostEstimateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create cost estimate from SystemDesign components",
    description="Create a cost estimate by processing selected components from SystemDesign.",
)
async def create_component_cost_estimate(
    data: schemas.ComponentCostEstimateCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a cost estimate from SystemDesign component selections.
    
    This endpoint:
    1. Fetches scenario analysis results for baseline components
    2. Processes selected components with user-modified lever values
    3. Matches components with tabular entities using semantic search
    4. Extracts cost information and calculates baseline vs redesigned costs
    5. Builds a cost comparison report
    6. Stores results in scenario_cost_estimates collection
    
    Args:
        data: Cost estimate creation data with SystemDesign config
        current_user: Authenticated user
        
    Returns:
        Created cost estimate object with calculation results
        
    Raises:
        HTTPException: If validation fails (400) or scenario not found (404)
    """
    try:
        # Get scenario to retrieve project_id
        scenario = await scenario_services.get(data.scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {data.scenario_id}",
            )
        
        project_id = scenario.project_id
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario missing project_id",
            )
        
        # Fetch scenario analysis results
        analysis_result = await scenario_repo.get_latest_scenario_analysis_result(
            scenario_id=data.scenario_id,
            workflow="v5",  # Use v5 workflow for component-based analysis
        )
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No scenario analysis result found for scenario {data.scenario_id}. Run scenario analysis first.",
            )
        
        # Extract components from analysis result
        result_data = analysis_result.get("result", {})
        all_components = result_data.get("components", [])
        
        if not all_components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No components found in scenario analysis result.",
            )
        
        # Build a map of component_id -> component data for quick lookup
        components_map = {comp.get("component_id"): comp for comp in all_components}
        
        # Get selected component IDs from the components list
        selected_component_ids = [comp_config.component_id for comp_config in data.components]
        
        if not selected_component_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No components selected for cost estimation.",
            )
        
        # Verify all selected components exist in analysis results
        missing_components = [
            comp_id for comp_id in selected_component_ids
            if comp_id not in components_map
        ]
        if missing_components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Components not found in analysis results: {missing_components}",
            )
        
        logger.info(
            f"Processing {len(selected_component_ids)} selected components for cost estimation"
        )
        
        # Create cost estimate entry first
        cost_estimate = await costing_repo.create_scenario_cost_estimate(
            data=data,
            project_id=project_id,
        )
        
        # Process each selected component with its own lever configuration
        component_costs = []
        all_matched_tabular_entities = []
        seen_tabular_ids = set()
        
        for comp_config in data.components:
            component_id = comp_config.component_id
            component = components_map.get(component_id)
            
            if not component:
                logger.warning(f"Component {component_id} not found in analysis results, skipping")
                continue
            
            try:
                # Match component with tabular entities using component-specific levers
                matched_entities = match_component_with_tabular_entities(
                    component=component,
                    lever_values=comp_config.lever_values,
                    lever_types=comp_config.lever_types,
                    project_id=project_id,
                    top_k=data.top_k or 3,
                    cutoff=data.cutoff or 0.75,
                )
                
                # Track unique tabular entities
                for tabular_entity in matched_entities:
                    tabular_id = tabular_entity.get("id")
                    if tabular_id and tabular_id not in seen_tabular_ids:
                        seen_tabular_ids.add(tabular_id)
                        all_matched_tabular_entities.append(tabular_entity)
                
                # Extract costs for this component
                comp_cost = extract_component_costs(
                    component=component,
                    matched_tabular_entities=matched_entities,
                )
                component_costs.append(comp_cost)
                
            except Exception as e:
                logger.error(
                    f"Error processing component {component.get('component_id')}: {e}",
                    exc_info=True,
                )
                # Continue processing other components
                continue
        
        # Calculate baseline vs redesigned costs
        calculation_summary = calculate_baseline_vs_redesigned(
            component_costs=component_costs,
        )
        
        # Build cost comparison report
        cost_report = build_cost_comparison_report(
            component_costs=component_costs,
            calculation_summary=calculation_summary,
        )
        
        # Build metadata with calculation results
        metadata = {
            "component_costs": component_costs,
            "matched_tabular_entities": all_matched_tabular_entities,
            "calculation_summary": calculation_summary,
            "status": "completed",
        }
        
        # Update cost estimate with report and metadata
        cost_estimate = await costing_repo.update_scenario_cost_estimate_metadata(
            cost_estimate_id=cost_estimate.id,
            cost_report=cost_report,
            metadata=metadata,
        )
        
        logger.info(
            f"Cost estimation completed for estimate {cost_estimate.id}: "
            f"{len(component_costs)} components processed, "
            f"{len(all_matched_tabular_entities)} unique tabular entities found"
        )
        
        return cost_estimate
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating component cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cost estimate: {str(e)}",
        )


@costing_router.get(
    "/estimates",
    response_model=List[schemas.ComponentCostEstimateOut],
    summary="List scenario cost estimates",
    description="List all scenario cost estimates, optionally filtered by scenario_id.",
)
async def list_scenario_cost_estimates(
    scenario_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    List all scenario cost estimates.
    
    Args:
        scenario_id: Optional scenario ID to filter cost estimates
        current_user: Authenticated user
        
    Returns:
        List of scenario cost estimate objects
    """
    try:
        cost_estimates = await costing_repo.list_scenario_cost_estimates(scenario_id)
        return cost_estimates
        
    except Exception as e:
        logger.error(f"Error listing scenario cost estimates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenario cost estimates: {str(e)}",
        )


@costing_router.get(
    "/estimates/{cost_estimate_id}",
    response_model=schemas.ComponentCostEstimateOut,
    summary="Get scenario cost estimate by ID",
    description="Retrieve a scenario cost estimate by its ID.",
)
async def get_scenario_cost_estimate(
    cost_estimate_id: str = Path(..., description="Cost estimate ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a scenario cost estimate by ID.
    
    Args:
        cost_estimate_id: MongoDB ObjectId as string
        current_user: Authenticated user
        
    Returns:
        Scenario cost estimate object
        
    Raises:
        HTTPException: If cost estimate not found (404) or invalid ID format (400)
    """
    try:
        cost_estimate = await costing_repo.get_scenario_cost_estimate(cost_estimate_id)
        if not cost_estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario cost estimate not found: {cost_estimate_id}",
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
        logger.error(f"Error getting scenario cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario cost estimate: {str(e)}",
        )


@costing_router.delete(
    "/estimates/{cost_estimate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scenario cost estimate",
    description="Delete a scenario cost estimate by ID.",
)
async def delete_scenario_cost_estimate(
    cost_estimate_id: str = Path(..., description="Cost estimate ID (MongoDB ObjectId as string)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a scenario cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        current_user: Authenticated user
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException: If cost estimate not found (404) or invalid ID format (400)
    """
    try:
        deleted = await costing_repo.delete_scenario_cost_estimate(cost_estimate_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario cost estimate not found: {cost_estimate_id}",
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
        logger.error(f"Error deleting scenario cost estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scenario cost estimate: {str(e)}",
        )

