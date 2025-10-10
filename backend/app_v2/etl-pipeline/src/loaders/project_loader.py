"""
Project loader for inserting project data into MongoDB.

Loads validated project data structures into the database,
handling creation, updates, and base case initialization.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class ProjectLoader:
    """Loads project data into MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.projects_collection = db.projects
        self.entities_collection = db.entities
        self.tables_collection = db.tables

    async def load_project(
        self, project_data: Dict[str, Any], overwrite: bool = False
    ) -> str:
        """
        Load a project into the database.

        Args:
            project_data: Project document following the Project model schema
            overwrite: If True, update existing project with same code

        Returns:
            project_id: MongoDB ObjectId as string
        """
        try:
            # Check if project already exists
            if "code" in project_data and project_data["code"]:
                existing = await self.projects_collection.find_one(
                    {"code": project_data["code"]}
                )

                if existing:
                    if not overwrite:
                        raise ValueError(
                            f"Project with code '{project_data['code']}' already exists. "
                            "Set overwrite=True to update."
                        )

                    # Update existing project
                    project_data["updated_at"] = datetime.utcnow()
                    await self.projects_collection.update_one(
                        {"_id": existing["_id"]}, {"$set": project_data}
                    )
                    project_id = str(existing["_id"])
                    logger.info(f"Updated existing project: {project_id}")
                    return project_id

            # Insert new project
            project_data["created_at"] = datetime.utcnow()
            project_data["updated_at"] = datetime.utcnow()

            result = await self.projects_collection.insert_one(project_data)
            project_id = str(result.inserted_id)

            logger.info(f"Created new project: {project_id}")
            return project_id

        except Exception as e:
            logger.error(f"Error loading project: {str(e)}")
            raise

    async def load_project_with_base_case(
        self,
        project_data: Dict[str, Any],
        base_case_entities: List[Dict[str, Any]],
        reference_tables: Optional[List[Dict[str, Any]]] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Load a complete project including base case entities and reference tables.

        Args:
            project_data: Project document
            base_case_entities: List of entity documents (base case equipment)
            reference_tables: List of reference table documents (costs, sizing, etc.)
            overwrite: If True, update existing project

        Returns:
            Dictionary with project_id and counts of loaded items
        """
        try:
            # Load project first
            project_id = await self.load_project(project_data, overwrite)
            project_oid = ObjectId(project_id)

            # Load base case entities
            entity_ids = []
            if base_case_entities:
                for entity in base_case_entities:
                    entity["project_id"] = project_oid
                    entity["is_base_case"] = True
                    entity["scenario_id"] = None
                    entity["option_id"] = None
                    entity["created_at"] = datetime.utcnow()
                    entity["updated_at"] = datetime.utcnow()

                result = await self.entities_collection.insert_many(base_case_entities)
                entity_ids = [str(eid) for eid in result.inserted_ids]
                logger.info(f"Loaded {len(entity_ids)} base case entities")

            # Load reference tables
            table_ids = []
            if reference_tables:
                for table in reference_tables:
                    table["project_id"] = project_oid
                    table["created_at"] = datetime.utcnow()
                    table["updated_at"] = datetime.utcnow()

                result = await self.tables_collection.insert_many(reference_tables)
                table_ids = [str(tid) for tid in result.inserted_ids]
                logger.info(f"Loaded {len(table_ids)} reference tables")

            # Update project with base case snapshot
            base_case_snapshot = await self._create_base_case_snapshot(
                project_oid, entity_ids
            )

            await self.projects_collection.update_one(
                {"_id": project_oid},
                {
                    "$set": {
                        "base_case": base_case_snapshot,
                        "data_inventory.entity_count": len(entity_ids),
                        "data_inventory.entity_ids": entity_ids,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            return {
                "project_id": project_id,
                "entities_loaded": len(entity_ids),
                "tables_loaded": len(table_ids),
                "base_case_snapshot": base_case_snapshot,
            }

        except Exception as e:
            logger.error(f"Error loading project with base case: {str(e)}")
            raise

    async def _create_base_case_snapshot(
        self, project_id: ObjectId, entity_ids: List[str]
    ) -> Dict[str, Any]:
        """Create base case snapshot from loaded entities."""

        # Count entities by type
        pipeline = [
            {"$match": {"project_id": project_id, "is_base_case": True}},
            {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
        ]

        entity_counts = {}
        async for doc in self.entities_collection.aggregate(pipeline):
            entity_counts[doc["_id"]] = doc["count"]

        # Calculate total costs
        pipeline = [
            {"$match": {"project_id": project_id, "is_base_case": True}},
            {
                "$group": {
                    "_id": None,
                    "total_capex": {"$sum": "$cost_data.total_installed_cost"},
                    "total_opex": {"$sum": "$cost_data.total_annual_opex"},
                }
            },
        ]

        costs = {"total_capex_base": 0, "total_opex_annual_base": 0}
        async for doc in self.entities_collection.aggregate(pipeline):
            costs["total_capex_base"] = doc.get("total_capex", 0)
            costs["total_opex_annual_base"] = doc.get("total_opex", 0)

        return {
            "snapshot_date": datetime.utcnow(),
            "entity_ids": [ObjectId(eid) for eid in entity_ids],
            "entity_count_by_type": entity_counts,
            **costs,
        }

    async def update_project_metadata(
        self, project_id: str, metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific project metadata fields.

        Args:
            project_id: Project ID
            metadata_updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        try:
            metadata_updates["updated_at"] = datetime.utcnow()

            result = await self.projects_collection.update_one(
                {"_id": ObjectId(project_id)}, {"$set": metadata_updates}
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Updated project metadata: {project_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating project metadata: {str(e)}")
            raise

    async def delete_project(
        self, project_id: str, cascade: bool = True
    ) -> Dict[str, int]:
        """
        Delete a project and optionally its related data.

        Args:
            project_id: Project ID
            cascade: If True, delete all entities, scenarios, options, tables

        Returns:
            Dictionary with counts of deleted items
        """
        try:
            project_oid = ObjectId(project_id)
            counts = {
                "projects": 0,
                "entities": 0,
                "scenarios": 0,
                "options": 0,
                "tables": 0,
            }

            if cascade:
                # Delete related data
                entities_result = await self.entities_collection.delete_many(
                    {"project_id": project_oid}
                )
                counts["entities"] = entities_result.deleted_count

                scenarios_result = await self.db.scenarios.delete_many(
                    {"project_id": project_oid}
                )
                counts["scenarios"] = scenarios_result.deleted_count

                options_result = await self.db.options.delete_many(
                    {"project_id": project_oid}
                )
                counts["options"] = options_result.deleted_count

                tables_result = await self.tables_collection.delete_many(
                    {"project_id": project_oid}
                )
                counts["tables"] = tables_result.deleted_count

            # Delete project
            project_result = await self.projects_collection.delete_one(
                {"_id": project_oid}
            )
            counts["projects"] = project_result.deleted_count

            logger.info(f"Deleted project {project_id} and related data: {counts}")
            return counts

        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            raise

    async def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get summary statistics for a project."""
        try:
            project_oid = ObjectId(project_id)

            # Get entity counts
            entity_count = await self.entities_collection.count_documents(
                {"project_id": project_oid}
            )

            base_case_count = await self.entities_collection.count_documents(
                {"project_id": project_oid, "is_base_case": True}
            )

            # Get scenario/option counts
            scenario_count = await self.db.scenarios.count_documents(
                {"project_id": project_oid}
            )

            option_count = await self.db.options.count_documents(
                {"project_id": project_oid}
            )

            # Get table counts
            table_count = await self.tables_collection.count_documents(
                {"project_id": project_oid}
            )

            return {
                "project_id": project_id,
                "entity_count": entity_count,
                "base_case_entity_count": base_case_count,
                "scenario_count": scenario_count,
                "option_count": option_count,
                "table_count": table_count,
            }

        except Exception as e:
            logger.error(f"Error getting project summary: {str(e)}")
            raise
