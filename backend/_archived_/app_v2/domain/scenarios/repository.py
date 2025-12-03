"""
MongoDB repository for scenario operations.

Handles all database interactions for scenarios, following patterns from projects/repository.py.
"""

from __future__ import annotations
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from bson import ObjectId
from ...adapters.mongo.client import db
from .schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioOut,
    ScenarioWithAnalysis,
    ScenarioAnalysis,
    SystemResizing,
    CostEstimationData,
    ScenarioRecommendation,
    UserConstraint,
)
import logging

logger = logging.getLogger(__name__)

# Get the MongoDB scenarios collection
_scenarios_collection = db().scenarios


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def _normalize_scenario_for_output(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize scenario from MongoDB format to ScenarioOut format.
    
    Ensures required fields are properly structured.
    """
    # Convert ObjectId to string
    scenario_id = str(scenario.get("_id") or scenario.get("id", ""))
    
    # Build normalized scenario
    normalized = {
        "id": scenario_id,
        "name": scenario.get("name", "Unnamed Scenario"),
        "description": scenario.get("description"),
        "project_id": scenario.get("project_id", ""),
        "base_case_reference_id": scenario.get("base_case_reference_id"),
        "global_objective": scenario.get("global_objective"),
        "status": scenario.get("status", "draft"),
        "compute_state": scenario.get("compute_state", "idle"),
        "created_by": scenario.get("created_by"),
        "option_count": scenario.get("option_count", 0),
        "created_at": scenario.get("created_at") or _now(),
        "updated_at": scenario.get("updated_at") or _now(),
    }
    
    return normalized


async def create_scenario(data: ScenarioCreate) -> ScenarioOut:
    """Create a new scenario in the MongoDB collection."""
    doc = {
        "name": data.name,
        "description": data.description,
        "project_id": data.project_id,
        "base_case_reference_id": data.base_case_reference_id,
        "global_objective": data.global_objective.model_dump() if data.global_objective else None,
        "status": data.status,
        "compute_state": data.compute_state,
        "created_by": data.created_by,
        "option_count": data.option_count,
        "created_at": _now(),
        "updated_at": _now(),
    }
    
    result = _scenarios_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return ScenarioOut(**doc)


async def get_scenario(scenario_id: str) -> Optional[ScenarioOut]:
    """Get a scenario by its ID from the MongoDB collection."""
    try:
        scenario = _scenarios_collection.find_one({"_id": ObjectId(scenario_id)})
    except Exception:
        # If ObjectId conversion fails, try as string
        scenario = _scenarios_collection.find_one({"id": scenario_id})
    
    if not scenario:
        return None
    
    normalized = _normalize_scenario_for_output(scenario)
    return ScenarioOut(**normalized)


async def get_scenario_with_analysis(scenario_id: str) -> Optional[ScenarioWithAnalysis]:
    """Get a scenario with all analysis data."""
    try:
        scenario = _scenarios_collection.find_one({"_id": ObjectId(scenario_id)})
    except Exception:
        scenario = _scenarios_collection.find_one({"id": scenario_id})
    
    if not scenario:
        return None
    
    normalized = _normalize_scenario_for_output(scenario)
    
    # Extract analysis data
    analysis_data = scenario.get("analysis")
    resizing_data = scenario.get("resizing")
    cost_estimation_data = scenario.get("cost_estimation")
    recommendation_data = scenario.get("recommendation")
    user_constraints_data = scenario.get("user_constraints", [])
    
    return ScenarioWithAnalysis(
        **normalized,
        analysis=ScenarioAnalysis(**analysis_data) if analysis_data else None,
        resizing=SystemResizing(**resizing_data) if resizing_data else None,
        cost_estimation=CostEstimationData(**cost_estimation_data) if cost_estimation_data else None,
        recommendation=ScenarioRecommendation(**recommendation_data) if recommendation_data else None,
        user_constraints=[UserConstraint(**uc) for uc in user_constraints_data] if user_constraints_data else [],
    )


async def list_scenarios_by_project(project_id: str) -> List[ScenarioOut]:
    """List all scenarios for a project."""
    scenarios = _scenarios_collection.find({"project_id": project_id})
    result = []
    
    for scenario in scenarios:
        normalized = _normalize_scenario_for_output(scenario)
        result.append(ScenarioOut(**normalized))
    
    return result


async def update_scenario(scenario_id: str, update_data: ScenarioUpdate) -> Optional[ScenarioOut]:
    """Update a scenario in the MongoDB collection."""
    data = update_data.model_dump(exclude_unset=True)
    
    # Convert global_objective to dict if present
    if "global_objective" in data and data["global_objective"] is not None:
        if hasattr(data["global_objective"], "model_dump"):
            data["global_objective"] = data["global_objective"].model_dump()
    
    data["updated_at"] = _now()
    
    try:
        result = _scenarios_collection.find_one_and_update(
            {"_id": ObjectId(scenario_id)},
            {"$set": data},
            return_document=True,
        )
    except Exception:
        result = _scenarios_collection.find_one_and_update(
            {"id": scenario_id},
            {"$set": data},
            return_document=True,
        )
    
    if not result:
        return None
    
    normalized = _normalize_scenario_for_output(result)
    return ScenarioOut(**normalized)


async def update_scenario_analysis(
    scenario_id: str, analysis: ScenarioAnalysis
) -> bool:
    """Update scenario analysis data."""
    try:
        result = _scenarios_collection.update_one(
            {"_id": ObjectId(scenario_id)},
            {
                "$set": {
                    "analysis": analysis.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    except Exception:
        result = _scenarios_collection.update_one(
            {"id": scenario_id},
            {
                "$set": {
                    "analysis": analysis.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    
    return result.modified_count > 0


async def update_scenario_resizing(
    scenario_id: str, resizing: SystemResizing
) -> bool:
    """Update scenario resizing data."""
    try:
        result = _scenarios_collection.update_one(
            {"_id": ObjectId(scenario_id)},
            {
                "$set": {
                    "resizing": resizing.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    except Exception:
        result = _scenarios_collection.update_one(
            {"id": scenario_id},
            {
                "$set": {
                    "resizing": resizing.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    
    return result.modified_count > 0


async def update_scenario_cost_estimation(
    scenario_id: str, cost_estimation: CostEstimationData
) -> bool:
    """Update scenario cost estimation data."""
    try:
        result = _scenarios_collection.update_one(
            {"_id": ObjectId(scenario_id)},
            {
                "$set": {
                    "cost_estimation": cost_estimation.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    except Exception:
        result = _scenarios_collection.update_one(
            {"id": scenario_id},
            {
                "$set": {
                    "cost_estimation": cost_estimation.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    
    return result.modified_count > 0


async def update_scenario_recommendation(
    scenario_id: str, recommendation: ScenarioRecommendation
) -> bool:
    """Update scenario recommendation data."""
    try:
        result = _scenarios_collection.update_one(
            {"_id": ObjectId(scenario_id)},
            {
                "$set": {
                    "recommendation": recommendation.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    except Exception:
        result = _scenarios_collection.update_one(
            {"id": scenario_id},
            {
                "$set": {
                    "recommendation": recommendation.model_dump(),
                    "updated_at": _now(),
                }
            },
        )
    
    return result.modified_count > 0


async def update_scenario_user_constraints(
    scenario_id: str, user_constraints: List[UserConstraint]
) -> bool:
    """Update scenario user constraints."""
    constraints_data = [uc.model_dump() for uc in user_constraints]
    
    try:
        result = _scenarios_collection.update_one(
            {"_id": ObjectId(scenario_id)},
            {
                "$set": {
                    "user_constraints": constraints_data,
                    "updated_at": _now(),
                }
            },
        )
    except Exception:
        result = _scenarios_collection.update_one(
            {"id": scenario_id},
            {
                "$set": {
                    "user_constraints": constraints_data,
                    "updated_at": _now(),
                }
            },
        )
    
    return result.modified_count > 0


async def delete_scenario(scenario_id: str) -> bool:
    """Delete a scenario from the MongoDB collection."""
    try:
        result = _scenarios_collection.delete_one({"_id": ObjectId(scenario_id)})
    except Exception:
        result = _scenarios_collection.delete_one({"id": scenario_id})
    
    return result.deleted_count > 0

