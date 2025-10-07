"""
Option API endpoints.

Handles retrieval and management of equipment options.
An option represents a specific equipment alternative for a scenario.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app_v2.core.database import get_database
from app_v2.schemas.option import (
    OptionResponse,
    OptionListResponse,
    OptionComparisonResponse,
    OptionSelectionRequest,
)
from app_v2.repositories.option_repo import OptionRepository
from app_v2.repositories.entity_repo import EntityRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{option_id}", response_model=OptionResponse)
async def get_option(option_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Get option by ID.

    Returns complete option data including:
    - Equipment specifications
    - Cost breakdown with provenance
    - Downstream impact analysis
    - Performance metrics

    Args:
        option_id: Option ID
        db: Database connection

    Returns:
        Option data

    Raises:
        HTTPException: If option not found
    """
    try:
        option_repo = OptionRepository(db)
        option = await option_repo.find_by_id(option_id)

        if not option:
            raise HTTPException(status_code=404, detail=f"Option {option_id} not found")

        return OptionResponse(**option)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving option: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve option: {str(e)}"
        )


@router.get("", response_model=OptionListResponse)
async def list_options(
    scenario_id: str = Query(..., description="Scenario ID"),
    skip: int = Query(0, ge=0, description="Number to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum to return"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List options for a scenario.

    Options are returned sorted by rank (best first).

    Args:
        scenario_id: Scenario ID
        skip: Pagination offset
        limit: Maximum results
        db: Database connection

    Returns:
        List of options with pagination metadata
    """
    try:
        option_repo = OptionRepository(db)

        # Get options
        options = await option_repo.find_by_scenario(
            scenario_id, skip=skip, limit=limit
        )

        # Get total count
        total = await option_repo.count({"scenario_id": scenario_id})

        return OptionListResponse(
            options=[OptionResponse(**o) for o in options],
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list options: {str(e)}")


@router.get("/{option_id}/entities")
async def get_option_entities(
    option_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all entities associated with an option.

    This includes:
    - The main equipment entity (e.g., the crusher)
    - Any downstream affected entities

    Args:
        option_id: Option ID
        db: Database connection

    Returns:
        List of entities
    """
    try:
        entity_repo = EntityRepository(db)

        entities = await entity_repo.find_by_option(option_id)

        return {"option_id": option_id, "entities": entities, "count": len(entities)}

    except Exception as e:
        logger.error(f"Error getting option entities: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get option entities: {str(e)}"
        )


@router.post("/{option_id}/select")
async def select_option(
    option_id: str,
    selection: OptionSelectionRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Mark an option as selected.

    This:
    1. Unselects all other options for the scenario
    2. Marks this option as selected
    3. Updates the scenario's selected_option_id

    Args:
        option_id: Option ID to select
        selection: Selection metadata (reason, etc.)
        db: Database connection

    Returns:
        Success message

    Raises:
        HTTPException: If option not found or selection fails
    """
    try:
        option_repo = OptionRepository(db)

        # Get option to verify it exists and get scenario_id
        option = await option_repo.find_by_id(option_id)

        if not option:
            raise HTTPException(status_code=404, detail=f"Option {option_id} not found")

        scenario_id = str(option["scenario_id"])

        # Select the option
        success = await option_repo.set_selected(option_id, scenario_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to select option")

        logger.info(
            f"Selected option",
            extra={
                "option_id": option_id,
                "scenario_id": scenario_id,
                "reason": selection.reason,
            },
        )

        return {
            "option_id": option_id,
            "scenario_id": scenario_id,
            "status": "selected",
            "message": "Option selected successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting option: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to select option: {str(e)}"
        )


@router.get("/compare", response_model=OptionComparisonResponse)
async def compare_options(
    option_ids: List[str] = Query(..., description="Option IDs to compare"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Compare multiple options side-by-side.

    Returns structured comparison data for:
    - Equipment specifications
    - Costs (purchase, installed, OPEX)
    - Downstream impacts
    - Key metrics

    Args:
        option_ids: List of option IDs to compare (2-5 recommended)
        db: Database connection

    Returns:
        Comparison data

    Raises:
        HTTPException: If options not found or comparison fails
    """
    try:
        if len(option_ids) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 options required for comparison"
            )

        if len(option_ids) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 options can be compared at once"
            )

        option_repo = OptionRepository(db)

        # Get all options
        options = []
        for option_id in option_ids:
            option = await option_repo.find_by_id(option_id)
            if not option:
                raise HTTPException(
                    status_code=404, detail=f"Option {option_id} not found"
                )
            options.append(option)

        # Verify all options are from same scenario
        scenario_ids = set(str(opt["scenario_id"]) for opt in options)
        if len(scenario_ids) > 1:
            raise HTTPException(
                status_code=400, detail="All options must be from the same scenario"
            )

        # Build comparison structure
        comparison = {
            "scenario_id": str(options[0]["scenario_id"]),
            "options_compared": len(options),
            "options": [],
        }

        # Extract comparable fields from each option
        for option in options:
            equipment = option.get("equipment", {})
            cost_data = option.get("cost_data", {})
            downstream = option.get("downstream_impact", {})

            comparison["options"].append(
                {
                    "option_id": str(option["_id"]),
                    "name": option.get("name"),
                    "rank": option.get("rank"),
                    "selected": option.get("selected", False),
                    # Equipment
                    "manufacturer": equipment.get("manufacturer"),
                    "model": equipment.get("model"),
                    "capacity_tph": equipment.get("capacity_tph"),
                    "power_kw": equipment.get("power_kw"),
                    # Costs
                    "purchase_cost": cost_data.get("purchase_cost_escalated"),
                    "installed_cost": cost_data.get("installed_equipment_cost"),
                    "total_capex": option.get("total_capex"),
                    "annual_opex": option.get("opex", {}).get("total_opex_per_year"),
                    # Downstream
                    "downstream_capex_delta": option.get(
                        "total_downstream_capex_delta"
                    ),
                    "downstream_entities_affected": len(
                        downstream.get("affected_entities", [])
                    ),
                    # Metrics
                    "npv": option.get("npv_analysis", {}).get("npv"),
                    "payback_years": option.get("npv_analysis", {}).get(
                        "payback_years"
                    ),
                }
            )

        return OptionComparisonResponse(**comparison)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing options: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to compare options: {str(e)}"
        )


@router.get("/scenario/{scenario_id}/cost-comparison")
async def get_cost_comparison(
    scenario_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get simplified cost comparison for all options in a scenario.

    Useful for charts and visualizations.

    Args:
        scenario_id: Scenario ID
        db: Database connection

    Returns:
        Cost comparison data
    """
    try:
        option_repo = OptionRepository(db)

        comparison_data = await option_repo.get_cost_comparison(scenario_id)

        return {"scenario_id": scenario_id, "options": comparison_data}

    except Exception as e:
        logger.error(f"Error getting cost comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get cost comparison: {str(e)}"
        )


@router.post("/scenario/{scenario_id}/rank")
async def rank_options(
    scenario_id: str,
    ranking_key: str = Query("total_capex", description="Field to rank by"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Re-rank options for a scenario based on a metric.

    Args:
        scenario_id: Scenario ID
        ranking_key: Field to rank by (e.g., "total_capex", "npv_analysis.npv")
        db: Database connection

    Returns:
        Success message with count
    """
    try:
        option_repo = OptionRepository(db)

        success = await option_repo.rank_options(scenario_id, ranking_key)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to rank options")

        # Get count of ranked options
        count = await option_repo.count({"scenario_id": scenario_id})

        logger.info(
            f"Ranked {count} options for scenario",
            extra={"scenario_id": scenario_id, "ranking_key": ranking_key},
        )

        return {
            "scenario_id": scenario_id,
            "ranking_key": ranking_key,
            "options_ranked": count,
            "message": "Options ranked successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ranking options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to rank options: {str(e)}")
