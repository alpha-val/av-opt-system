from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from app.scenario.scenario_model import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioWithOptions,
    OptionCreate,
    OptionUpdate,
    OptionResponse,
)
from app.scenario.scenario_db import (
    create_scenario_db,
    get_scenario_db,
    get_scenarios_by_project_db,
    update_scenario_db,
    delete_scenario_db,
    create_option_db,
    get_option_db,
    get_options_by_scenario_db,
    update_option_db,
    delete_option_db,
    select_option_db,
)

router_scenarios = APIRouter()


# Mock user authentication - replace with your actual auth
def get_current_user():
    return "user_sid"  # Replace with actual user ID from JWT/session


# ============================================================================
# SCENARIO ROUTES
# ============================================================================


@router_scenarios.post(
    "/scenarios", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED
)
def create_scenario(
    scenario: ScenarioCreate, user_id: str = Depends(get_current_user)
):
    """
    Create a new scenario
    """
    try:
        created_scenario = create_scenario_db(scenario, user_id)
        return created_scenario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scenario: {str(e)}",
        )


@router_scenarios.get("/scenarios/{scenario_id}", response_model=ScenarioWithOptions)
def get_scenario(scenario_id: str):
    """
    Get a scenario by ID with all its options
    """
    scenario = get_scenario_db(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )

    # Get options for this scenario
    options = get_options_by_scenario_db(scenario_id)

    # Return scenario with options
    scenario_dict = scenario.model_dump()
    scenario_dict["options"] = [opt.model_dump() for opt in options]
    return ScenarioWithOptions(**scenario_dict)


@router_scenarios.get(
    "/projects/{project_id}/scenarios", response_model=List[ScenarioResponse]
)
def get_project_scenarios(project_id: str):
    """
    Get all scenarios for a project
    """
    scenarios = get_scenarios_by_project_db(project_id)
    return scenarios


@router_scenarios.patch("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(scenario_id: str, update_data: ScenarioUpdate):
    """
    Update a scenario
    """
    updated_scenario = update_scenario_db(scenario_id, update_data)
    if not updated_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return updated_scenario


@router_scenarios.delete(
    "/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_scenario(scenario_id: str):
    """
    Delete a scenario and all its options
    """
    success = delete_scenario_db(scenario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return None


# ============================================================================
# OPTION ROUTES
# ============================================================================


@router_scenarios.post(
    "/options", response_model=OptionResponse, status_code=status.HTTP_201_CREATED
)
def create_option(option: OptionCreate, user_id: str = Depends(get_current_user)):
    """
    Create a new option for a scenario
    """
    # Verify scenario exists
    scenario = get_scenario_db(option.scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {option.scenario_id} not found",
        )

    try:
        created_option = create_option_db(option, user_id)
        return created_option
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create option: {str(e)}",
        )


@router_scenarios.get("/options/{option_id}", response_model=OptionResponse)
def get_option(option_id: str):
    """
    Get an option by ID
    """
    option = get_option_db(option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found",
        )
    return option


@router_scenarios.get(
    "/scenarios/{scenario_id}/options", response_model=List[OptionResponse]
)
def get_scenario_options(scenario_id: str):
    """
    Get all options for a scenario
    """
    # Verify scenario exists
    scenario = get_scenario_db(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )

    options = get_options_by_scenario_db(scenario_id)
    return options


@router_scenarios.patch("/options/{option_id}", response_model=OptionResponse)
def update_option(option_id: str, update_data: OptionUpdate):
    """
    Update an option
    """
    updated_option = update_option_db(option_id, update_data)
    if not updated_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found",
        )
    return updated_option

@router_scenarios.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option(option_id: str):
    """
    Delete an option
    """
    success = delete_option_db(option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found",
        )
    return None


@router_scenarios.post("/options/{option_id}/select", response_model=OptionResponse)
def select_option(option_id: str):
    """
    Select an option (and deselect others in the same scenario)
    """
    selected_option = select_option_db(option_id)
    if not selected_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found",
        )
    return selected_option


# ============================================================================
# UTILITY ROUTES
# ============================================================================


@router_scenarios.post(
    "/scenarios/{scenario_id}/analyze", response_model=ScenarioResponse
)
def analyze_scenario(scenario_id: str):
    """
    Trigger analysis for a scenario (generates options)
    This is a placeholder - implement actual analysis logic
    """
    scenario = get_scenario_db(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )

    # Update status to analyzing
    update_data = ScenarioUpdate(status="analyzing", compute_state="queued")
    updated_scenario = update_scenario_db(scenario_id, update_data)

    # TODO: Trigger actual analysis job here
    # This would typically:
    # 1. Queue a background job
    # 2. Analyze base case data
    # 3. Generate multiple options
    # 4. Update scenario status to "ready"

    return updated_scenario
