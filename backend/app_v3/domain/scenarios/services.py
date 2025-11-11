"""
Scenario service layer.

This module provides high-level service functions for scenario operations.
"""
from typing import List, Optional
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

