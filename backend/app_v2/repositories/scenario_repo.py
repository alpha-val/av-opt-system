"""
Scenario repository with domain-specific queries.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from .base import BaseRepository
from ..models.scenario import Scenario

logger = logging.getLogger(__name__)


class ScenarioRepository(BaseRepository[Scenario]):
    """
    Repository for scenario data access.

    Provides scenario-specific queries beyond basic CRUD.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "scenarios")

    async def find_by_project(
        self,
        project_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find scenarios for a project.

        Args:
            project_id: Project ID
            status: Optional status filter
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of scenarios
        """
        query = {"project_id": ObjectId(project_id)}

        if status:
            query["status"] = status

        return await self.find_many(query, skip=skip, limit=limit)

    async def find_by_parameter(
        self, project_id: str, parameter: str
    ) -> List[Dict[str, Any]]:
        """
        Find scenarios that change a specific parameter.

        Args:
            project_id: Project ID
            parameter: Parameter name (e.g., "crusher_product_size")

        Returns:
            List of matching scenarios
        """
        query = {
            "project_id": ObjectId(project_id),
            "parameter_changes.parameter": parameter,
        }

        return await self.find_many(query)

    async def get_with_options_count(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get scenarios with option counts using aggregation.

        This is more efficient than querying scenarios and options separately.

        Returns:
            List of scenarios with option_count field
        """
        pipeline = [
            # Match scenarios for project
            {"$match": {"project_id": ObjectId(project_id)}},
            # Lookup options
            {
                "$lookup": {
                    "from": "options",
                    "localField": "_id",
                    "foreignField": "scenario_id",
                    "as": "options",
                }
            },
            # Add option count
            {"$addFields": {"option_count": {"$size": "$options"}}},
            # Remove options array (we only want count)
            {"$project": {"options": 0}},
            # Sort by creation date
            {"$sort": {"created_at": -1}},
        ]

        return await self.aggregate(pipeline)

    async def update_status(
        self, scenario_id: str, status: str, compute_state: Optional[str] = None
    ) -> bool:
        """
        Update scenario status.

        Args:
            scenario_id: Scenario ID
            status: New status
            compute_state: Optional compute state

        Returns:
            True if updated
        """
        update_data = {"status": status}

        if compute_state:
            update_data["compute_state"] = compute_state

        return await self.update(scenario_id, update_data)

    async def increment_option_count(self, scenario_id: str) -> bool:
        """
        Increment option count for a scenario.

        Called when a new option is created.

        Args:
            scenario_id: Scenario ID

        Returns:
            True if incremented
        """
        try:
            if not ObjectId.is_valid(scenario_id):
                return False

            result = await self.collection.update_one(
                {"_id": ObjectId(scenario_id)}, {"$inc": {"option_count": 1}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error incrementing option count: {e}")
            return False
