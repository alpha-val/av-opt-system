"""
Scenario repository for MongoDB operations.

This module provides database operations for scenarios stored in the "scenarios" collection.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging

from ...adapters.mongo.client import db
from .schemas import ScenarioCreate, ScenarioUpdate, ScenarioOut, ScenarioStatus

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


async def create_scenario(data: ScenarioCreate) -> ScenarioOut:
    """
    Create a new scenario in the MongoDB collection.
    """
    try:
        # Generate a temporary unique ID to satisfy the unique index constraint during insertion
        # We'll update it to match _id after insertion
        from bson import ObjectId
        temp_id = str(ObjectId())
        
        # Build document for insertion
        # Include id field with temporary value to satisfy unique index
        doc = {
            "id": temp_id,  # Temporary ID to satisfy unique index
            "name": data.name,
            "description": data.description,
            "project_id": data.project_id,
            "status": (
                data.status.value if hasattr(data.status, "value") else data.status
            ),
            "global_objective_type": data.global_objective_type,  # Can be None
            "global_objective_target": data.global_objective_target,  # Can be None
            "objective_description": data.objective_description,  # Can be None
            "configuration": data.configuration or {},
            "created_at": _now(),
            "updated_at": _now(),
        }

        # Insert into MongoDB
        collection = db().scenarios
        result = collection.insert_one(doc)
        scenario_id = str(result.inserted_id)

        # Update the document to set id field to match _id (replacing temporary ID)
        collection.update_one(
            {"_id": result.inserted_id}, {"$set": {"id": scenario_id}}
        )

        logger.info(f"Created scenario: {scenario_id} for project: {data.project_id}")

        # Fetch and return the created scenario
        return await get_scenario(scenario_id)

    except InvalidId as e:
        logger.error(f"Invalid project_id format: {data.project_id}")
        raise ValueError(f"Invalid project_id format: {data.project_id}") from e
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        raise


async def list_scenarios(project_id: Optional[str] = None) -> List[ScenarioOut]:
    """
    List all scenarios, optionally filtered by project_id.
    """
    try:
        collection = db().scenarios
        query = {}
        if project_id:
            query["project_id"] = project_id

        cursor = collection.find(query).sort("created_at", -1)
        scenarios = []

        for doc in cursor:
            try:
                # Use id field if it exists, otherwise fall back to _id
                scenario_id = doc.get("id") or str(doc["_id"])
                scenario = ScenarioOut(
                    id=scenario_id,
                    name=doc.get("name", ""),
                    description=doc.get("description"),
                    project_id=doc.get("project_id", ""),
                    status=doc.get("status", ScenarioStatus.DRAFT.value),
                    global_objective_type=doc.get("global_objective_type"),
                    global_objective_target=doc.get("global_objective_target"),
                    objective_description=doc.get("objective_description"),
                    configuration=doc.get("configuration", {}),
                    created_at=doc.get("created_at", _now()),
                    updated_at=doc.get("updated_at", _now()),
                )
                scenarios.append(scenario)
            except Exception as e:
                logger.warning(f"Error parsing scenario document {doc.get('_id')}: {e}")
                continue

        logger.info(
            f"Listed {len(scenarios)} scenarios"
            + (f" for project: {project_id}" if project_id else "")
        )
        return scenarios

    except Exception as e:
        logger.error(f"Error listing scenarios: {e}", exc_info=True)
        raise


async def get_scenario(scenario_id: str) -> Optional[ScenarioOut]:
    """
    Get a scenario by ID.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        collection = db().scenarios
        doc = collection.find_one({"_id": ObjectId(scenario_id)})

        if not doc:
            logger.warning(f"Scenario not found: {scenario_id}")
            return None

        # Use id field if it exists, otherwise fall back to _id
        doc_id = doc.get("id") or str(doc["_id"])
        scenario = ScenarioOut(
            id=doc_id,
            name=doc.get("name", ""),
            description=doc.get("description"),
            project_id=doc.get("project_id", ""),
            status=doc.get("status", ScenarioStatus.DRAFT.value),
            global_objective_type=doc.get("global_objective_type"),
            global_objective_target=doc.get("global_objective_target"),
            objective_description=doc.get("objective_description"),
            configuration=doc.get("configuration", {}),
            created_at=doc.get("created_at", _now()),
            updated_at=doc.get("updated_at", _now()),
        )

        return scenario

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario {scenario_id}: {e}", exc_info=True)
        raise


async def update_scenario(
    scenario_id: str, patch: ScenarioUpdate
) -> Optional[ScenarioOut]:
    """
    Update a scenario.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        collection = db().scenarios

        # Build update document (only include fields that are not None)
        update_doc = {"updated_at": _now()}
        if patch.name is not None:
            update_doc["name"] = patch.name
        if patch.description is not None:
            update_doc["description"] = patch.description
        if patch.status is not None:
            update_doc["status"] = (
                patch.status.value if hasattr(patch.status, "value") else patch.status
            )
        if patch.global_objective_type is not None:
            update_doc["global_objective_type"] = patch.global_objective_type
        if patch.global_objective_target is not None:
            update_doc["global_objective_target"] = patch.global_objective_target
        if patch.objective_description is not None:
            update_doc["objective_description"] = patch.objective_description
        if patch.configuration is not None:
            update_doc["configuration"] = patch.configuration

        result = collection.update_one(
            {"_id": ObjectId(scenario_id)}, {"$set": update_doc}
        )

        if result.matched_count == 0:
            logger.warning(f"Scenario not found for update: {scenario_id}")
            return None

        logger.info(f"Updated scenario: {scenario_id}")
        return await get_scenario(scenario_id)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error updating scenario {scenario_id}: {e}", exc_info=True)
        raise


async def delete_scenario(scenario_id: str) -> bool:
    """
    Delete a scenario and cascade delete associated cost estimates and Pinecone vectors.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        collection = db().scenarios
        
        # Get scenario to retrieve project_id before deletion
        scenario = collection.find_one({"_id": ObjectId(scenario_id)})
        if not scenario:
            logger.warning(f"Scenario not found for deletion: {scenario_id}")
            return False
        
        project_id = scenario.get("project_id")
        
        # Delete associated cost estimates first
        cost_estimates_collection = db().cost_estimates
        cost_estimates_deleted = cost_estimates_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        if cost_estimates_deleted > 0:
            logger.info(f"Deleted {cost_estimates_deleted} cost estimates for scenario: {scenario_id}")

        # Delete vectors from Pinecone with scenario_id filter
        if project_id:
            try:
                from ...domain.parsing.storage.vector_store import delete_vectors_by_filter
                vectors_deleted = delete_vectors_by_filter(
                    project_id=project_id,
                    filter_dict={"scenario_id": {"$eq": scenario_id}}
                )
                if vectors_deleted != 0:
                    logger.info(
                        f"Deleted Pinecone vectors for scenario {scenario_id} "
                        f"in project {project_id}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to delete Pinecone vectors for scenario {scenario_id}: {e}. "
                    f"Continuing with scenario deletion."
                )
        else:
            logger.warning(
                f"Scenario {scenario_id} has no project_id. "
                f"Skipping Pinecone vector deletion."
            )

        # Delete the scenario document
        result = collection.delete_one({"_id": ObjectId(scenario_id)})

        if result.deleted_count == 0:
            logger.warning(f"Scenario not found for deletion: {scenario_id}")
            return False

        logger.info(f"Deleted scenario: {scenario_id}")
        return True

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario {scenario_id}: {e}", exc_info=True)
        raise
