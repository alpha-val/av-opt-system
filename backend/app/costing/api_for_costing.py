from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging
from datetime import datetime

from app.costing.schemas_for_costing import (
    CostEstimateRequest,
    CostEstimateResponse,
    CostEstimateListResponse,
)

from app.costing.costing import cost_estimation
from app.bronze_store import db
from ..pipeline_users import get_current_user

logger = logging.getLogger(__name__)
router_costing = APIRouter()


@router_costing.post("/cost-estimates", response_model=CostEstimateResponse)
async def create_cost_estimate(
    request: CostEstimateRequest, current_user: dict = Depends(get_current_user)
):
    """
    Estimate costs for a scenario description.

    This endpoint:
    1. Retrieves relevant entities from Pinecone (vector search) or MongoDB (fallback)
    2. Builds prompt with entities and scenario description
    3. Calls LLM to estimate costs
    4. Stores estimate in MongoDB
    5. Returns cost breakdown

    Request body:
        - project_id: Project identifier
        - scenario_id: Scenario identifier
        - cost_id: Optional cost estimate ID (auto-generated if not provided)
        - scenario_description: What the user wants to change
        - entity_types: Types of entities to consider (Equipment, Material, Process)
        - uncertainties: Optional uncertainty parameters
        - goal: Optional scenario goal
        - change_type: Optional change type
        - equipment_types: Optional list of specific equipment types
        - capacity_range: Optional [min, max] capacity range
    """
    try:
        logger.info(
            f"[COST_ESTIMATE] Creating estimate for project: {request.project_id}, "
            f"scenario: {request.scenario_id}"
        )

        # Try multiple possible keys for user_id
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )
        if not user_id:
            raise HTTPException(400, "User ID not found in authentication token")

        # Run cost estimation        
        estimate = cost_estimation(
            scenario_description=request.scenario_description,
            project_id=request.project_id,
            scenario_id=request.scenario_id,
            goal=request.goal,
            change_type=request.change_type,
            uncertainties=request.uncertainties,
            selected_entities=request.selected_entities,
            user_id=user_id,
        )
        
        estimate["created_at"] = datetime.utcnow()
        estimate["user_id"] = user_id
        try:
            # Upsert estimate in the collection "cost_estimates"
            db().cost_estimates.update_one(
                {"estimate_id": estimate["estimate_id"]},
                {"$set": estimate},
                upsert=True,
            )
        except Exception as e:
            logger.error(
                f"[COST_ESTIMATE] Failed to upsert estimate: {e}", exc_info=True
            )

        logger.info(f"[COST_ESTIMATE] Estimate created: {estimate['estimate_id']}")

        return estimate

    except Exception as e:
        logger.error(f"[COST_ESTIMATE] Failed to create estimate: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create cost estimate: {str(e)}")


@router_costing.get(
    "/cost-estimates/{estimate_id}", response_model=CostEstimateResponse
)
async def get_cost_estimate(estimate_id: str):
    """
    Retrieve a specific cost estimate by ID.
    """
    try:
        estimate = db().cost_estimates.find_one(
            {"estimate_id": estimate_id}, {"_id": 0}
        )

        if not estimate:
            raise HTTPException(404, f"Cost estimate {estimate_id} not found")

        return estimate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COST_ESTIMATE] Failed to retrieve estimate: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to retrieve estimate: {str(e)}")


@router_costing.get("/cost-estimates", response_model=CostEstimateListResponse)
async def list_cost_estimates(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    scenario_id: Optional[str] = Query(None, description="Filter by scenario ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of estimates to return"
    ),
    skip: int = Query(0, ge=0, description="Number of estimates to skip"),
):
    """
    List cost estimates with optional filtering.
    """
    try:
        # Build query filter
        query_filter = {}
        if project_id:
            query_filter["project_id"] = project_id
        if scenario_id:
            query_filter["scenario_id"] = scenario_id
        if user_id:
            query_filter["user_id"] = user_id

        # Get total count
        total = db().cost_estimates.count_documents(query_filter)

        # Get estimates
        estimates = list(
            db()
            .cost_estimates.find(query_filter, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {"estimates": estimates, "total": total}

    except Exception as e:
        logger.error(f"[COST_ESTIMATE] Failed to list estimates: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list estimates: {str(e)}")


@router_costing.delete("/cost-estimates/{estimate_id}")
async def delete_cost_estimate(estimate_id: str):
    """
    Delete a cost estimate by ID.
    """
    try:
        result = db().cost_estimates.delete_one({"estimate_id": estimate_id})

        if result.deleted_count == 0:
            raise HTTPException(404, f"Cost estimate {estimate_id} not found")

        logger.info(f"[COST_ESTIMATE] Deleted estimate: {estimate_id}")

        return {
            "message": f"Cost estimate {estimate_id} deleted successfully",
            "deleted_count": result.deleted_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COST_ESTIMATE] Failed to delete estimate: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete estimate: {str(e)}")
