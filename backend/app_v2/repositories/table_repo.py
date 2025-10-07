"""
Table repository for cost/sizing/lang factor tables.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from .base import BaseRepository

logger = logging.getLogger(__name__)


class TableRepository(BaseRepository):
    """
    Repository for table data (cost tables, sizing tables, lang factors).
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "tables")

    async def find_by_type(
        self, project_id: str, table_type: str
    ) -> List[Dict[str, Any]]:
        """
        Find tables by type.

        Args:
            project_id: Project ID
            table_type: Table type (e.g., "cost_table", "sizing_table", "lang_factors")

        Returns:
            List of tables
        """
        query = {"project_id": ObjectId(project_id), "table_type": table_type}

        return await self.find_many(query)

    async def find_cost_table(
        self,
        project_id: str,
        equipment_type: Optional[str] = None,
        cost_year: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find cost table for equipment type.

        Args:
            project_id: Project ID
            equipment_type: Equipment type (e.g., "gyratory_crusher")
            cost_year: Cost basis year

        Returns:
            Cost table or None
        """
        query = {"project_id": ObjectId(project_id), "table_type": "cost_table"}

        if equipment_type:
            query["metadata.equipment_type"] = equipment_type

        if cost_year:
            query["metadata.cost_basis_year"] = cost_year

        return await self.find_one(query)

    async def find_sizing_table(
        self, project_id: str, equipment_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find sizing table for equipment type.

        Args:
            project_id: Project ID
            equipment_type: Equipment type

        Returns:
            Sizing table or None
        """
        query = {
            "project_id": ObjectId(project_id),
            "table_type": "sizing_table",
            "metadata.equipment_type": equipment_type,
        }

        return await self.find_one(query)

    async def find_lang_factors(
        self, project_id: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find lang factors table.

        Args:
            project_id: Project ID
            category: Optional category filter

        Returns:
            Lang factors table or None
        """
        query = {"project_id": ObjectId(project_id), "table_type": "lang_factors"}

        if category:
            query["metadata.category"] = category

        return await self.find_one(query)

    async def get_table_row(
        self, table_id: str, model: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific row from table by model designation.

        Args:
            table_id: Table ID
            model: Model designation (e.g., "54-75")

        Returns:
            Table row or None
        """
        try:
            if not ObjectId.is_valid(table_id):
                return None

            # Query for table and extract specific row
            table = await self.collection.find_one(
                {"_id": ObjectId(table_id)}, {"extracted_data.rows": 1}
            )

            if not table:
                return None

            rows = table.get("extracted_data", {}).get("rows", [])

            # Find row matching model
            for row in rows:
                row_model = row.get("model") or row.get("data", {}).get("model")
                if row_model == model:
                    return row

            return None

        except Exception as e:
            logger.error(f"Error getting table row: {e}")
            return None

    async def search_table_rows(
        self, table_id: str, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search table rows with filters.

        Args:
            table_id: Table ID
            filters: Field filters (e.g., {"capacity_tph": {"$gte": 1000}})

        Returns:
            Matching rows
        """
        try:
            if not ObjectId.is_valid(table_id):
                return []

            table = await self.collection.find_one(
                {"_id": ObjectId(table_id)}, {"extracted_data.rows": 1}
            )

            if not table:
                return []

            rows = table.get("extracted_data", {}).get("rows", [])

            # Apply filters
            matching_rows = []
            for row in rows:
                data = row.get("data", {})
                match = True

                for field, condition in filters.items():
                    value = data.get(field)
                    if value is None:
                        match = False
                        break

                    # Handle operators
                    if isinstance(condition, dict):
                        for op, target in condition.items():
                            if op == "$gte" and value < target:
                                match = False
                            elif op == "$lte" and value > target:
                                match = False
                            elif op == "$eq" and value != target:
                                match = False
                    else:
                        # Direct equality
                        if value != condition:
                            match = False

                if match:
                    matching_rows.append(row)

            return matching_rows

        except Exception as e:
            logger.error(f"Error searching table rows: {e}")
            return []
