from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid

from ..bronze_store import db
from ..pipeline_users import get_current_user
from .schemas_for_scenario import (
    ScenarioBase,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
)
from .scenario_estimate import estimate_scenario_cost, get_scenario_cost_estimate

router_scenarios = APIRouter()

# ============================================================================
# ENDPOINTS
# ============================================================================


# Create a new scenario
@router_scenarios.post(
    "/scenarios/add",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scenario(
    scenario_data: ScenarioCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new scenario"""
    try:
        # Debug: print current_user to see what keys exist
        print(f"[DEBUG] current_user: {current_user}")
        print(f"[DEBUG] current_user type: {type(current_user)}")

        scenario_dict = scenario_data.model_dump()

        # Try multiple possible keys for user_id
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            print(
                f"[ERROR] Could not extract user_id from current_user: {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not extract user_id from authentication token. Available keys: {list(current_user.keys()) if isinstance(current_user, dict) else 'not a dict'}",
            )

        print(f"[DEBUG] Extracted user_id: {user_id}")

        # Set all required fields
        scenario_dict["id"] = str(uuid.uuid4())
        scenario_dict["created_by"] = user_id
        scenario_dict["created_at"] = datetime.utcnow()
        scenario_dict["updated_at"] = datetime.utcnow()

        # Set defaults
        if "status" not in scenario_dict or scenario_dict["status"] is None:
            scenario_dict["status"] = "draft"
        if "compute_state" not in scenario_dict:
            scenario_dict["compute_state"] = "idle"
        if "target" not in scenario_dict or scenario_dict["target"] is None:
            scenario_dict["target"] = {}
        if "constraints" not in scenario_dict or scenario_dict["constraints"] is None:
            scenario_dict["constraints"] = {}

        print(f"[DEBUG] scenario_dict before insert: {scenario_dict}")

        # Insert into database
        result = db().scenarios.insert_one(scenario_dict)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create scenario",
            )

        print(f"[DEBUG] Successfully inserted scenario with id: {scenario_dict['id']}")

        # Remove MongoDB _id before returning
        scenario_dict.pop("_id", None)

        return ScenarioResponse(**scenario_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Create scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# List scenarios for a project
@router_scenarios.get(
    "/projects/{project_id}/scenarios",
    response_model=List[ScenarioResponse],
    status_code=status.HTTP_200_OK,
)
def list_scenarios(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List scenarios for a specific project"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        query = {"project_id": project_id, "created_by": user_id}

        scenarios_cursor = (
            db().scenarios.find(query, {"_id": 0}).skip(skip).limit(limit)
        )
        scenarios = list(scenarios_cursor)

        return [ScenarioResponse(**scenario) for scenario in scenarios]

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] List scenarios failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Get a single scenario by ID
@router_scenarios.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Get a scenario by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        scenario_data = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        if not scenario_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        return ScenarioResponse(**scenario_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Get scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Update a scenario
@router_scenarios.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: str,
    update_data: ScenarioUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a scenario"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Verify scenario exists and belongs to user
        existing = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Build update dict
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

        if not update_dict:
            return ScenarioResponse(**existing)

        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        result = db().scenarios.update_one(
            {"id": scenario_id, "created_by": user_id}, {"$set": update_dict}
        )

        if result.modified_count == 0 and result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update scenario {scenario_id}",
            )

        # Fetch updated scenario
        updated_scenario = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        return ScenarioResponse(**updated_scenario)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Update scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Delete a scenario
@router_scenarios.delete(
    "/scenarios/{scenario_id}",
    status_code=status.HTTP_200_OK,
)
def delete_scenario(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scenario by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Verify scenario exists and belongs to user
        scenario = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0, "name": 1}
        )

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Delete scenario
        result = db().scenarios.delete_one({"id": scenario_id, "created_by": user_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete scenario {scenario_id}",
            )

        print(f"[DEBUG] Deleted scenario {scenario_id}")

        return {
            "message": f"Scenario '{scenario.get('name', scenario_id)}' deleted successfully",
            "scenario_id": scenario_id,
            "scenario_name": scenario.get("name"),
            "deleted_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Run cost analysis for a scenario
@router_scenarios.post("/scenarios/{scenario_id}/analyze")
def analyze_scenario(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Trigger cost analysis for a scenario"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Get the scenario
        scenario_data = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        if not scenario_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Update scenario status to analyzing
        db().scenarios.update_one(
            {"id": scenario_id, "created_by": user_id},
            {
                "$set": {
                    "status": "analyzing",
                    "compute_state": "running",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Build scenario description for LLM
        scenario_description = f"""
Name: {scenario_data.get('name', 'Unnamed Scenario')}
Goal: {scenario_data.get('goal', 'Not specified')}
Description: {scenario_data.get('description', 'No description provided')}
Change Type: {scenario_data.get('change_type', 'Not specified')}
Target: {scenario_data.get('target', {})}
Constraints: {scenario_data.get('constraints', {})}
"""

        print(f"[DEBUG] Scenario description for analysis:\n{scenario_description}")

        # Run cost estimation
        cost_estimate = estimate_scenario_cost(
            scenario_id=scenario_id,
            scenario_description=scenario_description,
            project_id=scenario_data.get("project_id"),
            user_id=user_id,
        )

        # Check if estimation succeeded
        if cost_estimate.get("status") == "failed":
            # Update scenario to failed state
            db().scenarios.update_one(
                {"id": scenario_id, "created_by": user_id},
                {
                    "$set": {
                        "status": "draft",
                        "compute_state": "failed",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cost estimation failed: {cost_estimate.get('error', 'Unknown error')}",
            )

        # Update scenario to completed state with cost estimate reference
        db().scenarios.update_one(
            {"id": scenario_id, "created_by": user_id},
            {
                "$set": {
                    "status": "ready",
                    "compute_state": "succeeded",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Fetch updated scenario
        updated_scenario = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        print(f"[DEBUG] Analysis completed for scenario {scenario_id}")

        # Return both scenario and cost estimate data
        return {
            "message": "Scenario analysis completed successfully",
            "scenario": ScenarioResponse(**updated_scenario),
            "cost_estimate": {
                "scenario_id": cost_estimate.get("scenario_id"),
                "estimated_at": cost_estimate.get("estimated_at"),
                "status": cost_estimate.get("status"),
                "cost_breakdown": cost_estimate.get("cost_breakdown", {}),
                "relevant_entities": cost_estimate.get("relevant_entities", {}),
                "assumptions": cost_estimate.get("assumptions", []),
                "confidence": cost_estimate.get("confidence", "medium"),
                "notes": cost_estimate.get("notes", ""),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Analyze scenario failed: {e}")
        import traceback

        traceback.print_exc()

        # Update scenario to failed state
        try:
            db().scenarios.update_one(
                {"id": scenario_id},
                {
                    "$set": {
                        "status": "draft",
                        "compute_state": "failed",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        except Exception as update_error:
            print(f"[ERROR] Failed to update scenario status: {update_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Get cost estimate for a scenario
@router_scenarios.get("/scenarios/{scenario_id}/cost-estimate")
def get_cost_estimate(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Get the most recent cost estimate for a scenario"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Verify scenario belongs to user
        scenario = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0, "id": 1}
        )

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Get cost estimate
        cost_estimate = get_scenario_cost_estimate(scenario_id)

        if not cost_estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cost estimate found for scenario {scenario_id}",
            )

        return cost_estimate

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Get cost estimate failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
