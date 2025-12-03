"""
Scenario service layer.

This module provides high-level service functions for scenario operations.
"""
from typing import List, Optional, Dict, Any
from .schemas import ScenarioCreate, ScenarioUpdate, ScenarioOut
from . import repository as repo


async def create(data: ScenarioCreate) -> ScenarioOut:
    """Create a new scenario."""
    return await repo.create_scenario(data)


async def list_all(project_id: Optional[str] = None) -> List[ScenarioOut]:
    """List all scenarios, optionally filtered by project_id."""
    return await repo.list_scenarios(project_id)


async def get(scenario_id: str) -> Optional[ScenarioOut]:
    """Get a scenario by ID."""
    return await repo.get_scenario(scenario_id)


async def update(scenario_id: str, patch: ScenarioUpdate) -> Optional[ScenarioOut]:
    """Update a scenario."""
    return await repo.update_scenario(scenario_id, patch)


async def delete(scenario_id: str) -> bool:
    """Delete a scenario."""
    return await repo.delete_scenario(scenario_id)


async def clear_data(scenario_id: str) -> dict:
    """Clear all data associated with a scenario, but keep the scenario itself."""
    return await repo.clear_scenario_data(scenario_id)


async def save_analysis_result(
    scenario_id: str,
    project_id: str,
    workflow: str,
    job_id: str,
    result: Dict[str, Any],
    context: Dict[str, Any],
) -> bool:
    """Persist the latest scenario analysis result."""
    return await repo.upsert_scenario_analysis_result(
        scenario_id=scenario_id,
        project_id=project_id,
        workflow=workflow,
        job_id=job_id,
        result=result,
        context=context,
    )


async def get_analysis_result(
    scenario_id: str, workflow: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve the latest scenario analysis result (optionally by workflow)."""
    return await repo.get_latest_scenario_analysis_result(
        scenario_id=scenario_id,
        workflow=workflow,
    )

