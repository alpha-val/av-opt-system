"""
Option repository with domain-specific queries.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from .base import BaseRepository
from ..models.option import Option

logger = logging.getLogger(__name__)


class OptionRepository(BaseRepository[Option]):
    """
    Repository for option data access.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "options")

    async def find_by_scenario(
        self, scenario_id: str, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find options for a scenario.

        Args:
            scenario_id: Scenario ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of options
        """
        query = {"scenario_id": ObjectId(scenario_id)}
        return await self.find_many(query, skip=skip, limit=limit)

    async def find_selected(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Find the selected option for a scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            Selected option or None
        """
        query = {"scenario_id": ObjectId(scenario_id), "selected": True}
        return await self.find_one(query)

    async def set_selected(self, option_id: str, scenario_id: str) -> bool:
        """
        Mark an option as selected and unselect others.

        This is a transactional operation:
        1. Unselect all options for scenario
        2. Select the specified option
        3. Update scenario.selected_option_id

        Args:
            option_id: Option ID to select
            scenario_id: Scenario ID

        Returns:
            True if successful
        """
        try:
            # 1. Unselect all options for scenario
            await self.collection.update_many(
                {"scenario_id": ObjectId(scenario_id)}, {"$set": {"selected": False}}
            )

            # 2. Select specified option
            await self.collection.update_one(
                {"_id": ObjectId(option_id)}, {"$set": {"selected": True}}
            )

            # 3. Update scenario
            await self.db.scenarios.update_one(
                {"_id": ObjectId(scenario_id)},
                {"$set": {"selected_option_id": ObjectId(option_id)}},
            )

            logger.info(
                f"Selected option for scenario",
                extra={"option_id": option_id, "scenario_id": scenario_id},
            )

            return True

        except Exception as e:
            logger.error(f"Error selecting option: {e}")
            return False

    async def rank_options(
        self, scenario_id: str, ranking_key: str = "total_capex"
    ) -> bool:
        """
        Rank options for a scenario based on a metric.

        Args:
            scenario_id: Scenario ID
            ranking_key: Field to rank by (e.g., "total_capex", "npv_analysis.npv")

        Returns:
            True if successful
        """
        try:
            # Get all options for scenario
            options = await self.find_by_scenario(scenario_id)

            # Sort by ranking key (ascending for cost, descending for NPV)
            reverse = "npv" in ranking_key.lower()

            # Extract nested keys
            def get_nested(obj, key):
                keys = key.split(".")
                value = obj
                for k in keys:
                    value = value.get(k, 0)
                return value

            sorted_options = sorted(
                options, key=lambda x: get_nested(x, ranking_key), reverse=reverse
            )

            # Update ranks
            for rank, option in enumerate(sorted_options, start=1):
                await self.update(str(option["_id"]), {"rank": rank})

            logger.info(
                f"Ranked {len(sorted_options)} options for scenario",
                extra={"scenario_id": scenario_id, "ranking_key": ranking_key},
            )

            return True

        except Exception as e:
            logger.error(f"Error ranking options: {e}")
            return False

    async def get_cost_comparison(self, scenario_id: str) -> List[Dict[str, Any]]:
        """
        Get cost comparison data for all options in a scenario.

        Returns simplified data for comparison charts.

        Returns:
            List of cost comparison data
        """
        pipeline = [
            {"$match": {"scenario_id": ObjectId(scenario_id)}},
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "model": "$equipment.model",
                    "purchase_cost": "$cost_data.purchase_cost_escalated",
                    "installed_cost": "$cost_data.installed_equipment_cost",
                    "total_capex": "$total_capex",
                    "opex_annual": "$opex.total_opex_per_year",
                    "downstream_impact": "$total_downstream_capex_delta",
                    "selected": 1,
                    "rank": 1,
                }
            },
            {"$sort": {"rank": 1}},
        ]

        return await self.aggregate(pipeline)
