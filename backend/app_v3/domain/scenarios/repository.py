"""
Scenario repository for MongoDB operations.

This module provides database operations for scenarios stored in the "scenarios" collection.
"""

from typing import List, Optional, Dict, Any
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
        print(f"[SCENARIO : : : Create] > {data}")
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
            "global_objective_unit": data.global_objective_unit,  # Can be None
            "objective_description": data.objective_description,  # Can be None
            "configuration": data.configuration or {},
            "created_at": _now(),
            "updated_at": _now(),
        }
        
        logger.info(f"Creating scenario document with global_objective_unit: {data.global_objective_unit} (type: {type(data.global_objective_unit)})")

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
                    global_objective_unit=doc.get("global_objective_unit"),
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
            global_objective_unit=doc.get("global_objective_unit"),
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
        if patch.global_objective_unit is not None:
            update_doc["global_objective_unit"] = patch.global_objective_unit
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


async def clear_scenario_data(scenario_id: str) -> dict:
    """
    Clear all data associated with a scenario, but keep the scenario itself.
    
    This deletes all related data including:
    - Entities with properties.scenario_id matching scenario_id
    - Relations with properties.scenario_id matching scenario_id
    - Base case recommendations with scenario_id matching scenario_id
    - Cost estimates with scenario_id matching scenario_id
    - Scenario analysis results with scenario_id matching scenario_id
    - Pinecone vectors with scenario_id filter
    
    The scenario document itself is not deleted.
    
    Args:
        scenario_id: String representation of MongoDB ObjectId
        
    Returns:
        Dictionary with deletion counts for each collection
        
    Note:
        This is a destructive operation. Use with caution.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        # Get scenario to retrieve project_id
        collection = db().scenarios
        scenario = collection.find_one({"_id": ObjectId(scenario_id)})
        if not scenario:
            logger.warning(f"Scenario not found for data clearing: {scenario_id}")
            return {
                "scenario_id": scenario_id,
                "error": "Scenario not found",
                "deleted_counts": {},
            }
        
        project_id = scenario.get("project_id")
        
        deleted_counts = {
            "entities": 0,
            "relations": 0,
            "base_case_recommendations": 0,
            "cost_estimates": 0,
            "scenario_cost_estimates": 0,
            "scenario_analysis_results": 0,
            "vectors": 0,
        }
        
        # Delete entities with properties.scenario_id matching scenario_id
        entities_collection = db().entities
        entities_deleted = entities_collection.delete_many(
            {"properties.scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["entities"] = entities_deleted
        if entities_deleted > 0:
            logger.info(f"Deleted {entities_deleted} entities for scenario: {scenario_id}")
        
        # Delete relations with properties.scenario_id matching scenario_id
        relations_collection = db().relations
        relations_deleted = relations_collection.delete_many(
            {"properties.scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["relations"] = relations_deleted
        if relations_deleted > 0:
            logger.info(f"Deleted {relations_deleted} relations for scenario: {scenario_id}")
        
        # Delete base case recommendations with scenario_id matching scenario_id
        base_case_recommendations_collection = db().base_case_recommendations
        recommendations_deleted = base_case_recommendations_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["base_case_recommendations"] = recommendations_deleted
        if recommendations_deleted > 0:
            logger.info(f"Deleted {recommendations_deleted} recommendations for scenario: {scenario_id}")
        
        # Delete cost estimates with scenario_id matching scenario_id
        cost_estimates_collection = db().cost_estimates
        cost_estimates_deleted = cost_estimates_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["cost_estimates"] = cost_estimates_deleted
        if cost_estimates_deleted > 0:
            logger.info(f"Deleted {cost_estimates_deleted} cost estimates for scenario: {scenario_id}")
        
        # Delete scenario cost estimates with scenario_id matching scenario_id
        scenario_cost_estimates_collection = db().scenario_cost_estimates
        scenario_cost_estimates_deleted = scenario_cost_estimates_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["scenario_cost_estimates"] = scenario_cost_estimates_deleted
        if scenario_cost_estimates_deleted > 0:
            logger.info(f"Deleted {scenario_cost_estimates_deleted} scenario cost estimates for scenario: {scenario_id}")
        
        # Delete scenario analysis results with scenario_id matching scenario_id
        scenario_analysis_results_collection = db().scenario_analysis_results
        analysis_results_deleted = scenario_analysis_results_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        deleted_counts["scenario_analysis_results"] = analysis_results_deleted
        if analysis_results_deleted > 0:
            logger.info(f"Deleted {analysis_results_deleted} scenario analysis results for scenario: {scenario_id}")
        
        # Delete vectors from Pinecone with scenario_id filter
        if project_id:
            try:
                from ...domain.parsing.storage.vector_store import delete_vectors_by_filter
                vectors_deleted = delete_vectors_by_filter(
                    project_id=project_id,
                    filter_dict={"scenario_id": {"$eq": scenario_id}}
                )
                deleted_counts["vectors"] = vectors_deleted
                if vectors_deleted != 0:
                    logger.info(
                        f"Deleted {vectors_deleted} Pinecone vectors for scenario {scenario_id} "
                        f"in project {project_id}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to delete Pinecone vectors for scenario {scenario_id}: {e}. "
                    f"Continuing with data clearing."
                )
        else:
            logger.warning(
                f"Scenario {scenario_id} has no project_id. "
                f"Skipping Pinecone vector deletion."
            )
        
        logger.info(
            f"Cleared data for scenario {scenario_id}: "
            f"{entities_deleted} entities, {relations_deleted} relations, "
            f"{recommendations_deleted} recommendations, {cost_estimates_deleted} cost estimates, "
            f"{scenario_cost_estimates_deleted} scenario cost estimates, "
            f"{analysis_results_deleted} scenario analysis results, "
            f"{deleted_counts.get('vectors', 0)} vectors"
        )
        
        return {
            "scenario_id": scenario_id,
            "deleted_counts": deleted_counts,
        }
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error clearing scenario data {scenario_id}: {e}", exc_info=True)
        raise


async def upsert_scenario_analysis_result(
    scenario_id: str,
    project_id: str,
    workflow: str,
    job_id: str,
    result: Dict[str, Any],
    context: Dict[str, Any],
) -> bool:
    """
    Store or update the latest scenario analysis result for a workflow version.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        collection = db().scenario_analysis_results
        now = _now()

        update_doc = {
            "scenario_id": scenario_id,
            "project_id": project_id,
            "workflow": workflow,
            "job_id": job_id,
            "result": result,
            "context": context,
            "updated_at": now,
        }

        collection.update_one(
            {"scenario_id": scenario_id, "workflow": workflow},
            {"$set": update_doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

        logger.info(
            f"Stored scenario analysis result for scenario {scenario_id} (workflow={workflow})"
        )
        return True
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            f"Error storing scenario analysis result for scenario {scenario_id}: {e}",
            exc_info=True,
        )
        raise


async def get_latest_scenario_analysis_result(
    scenario_id: str, workflow: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest stored scenario analysis result.
    """
    try:
        if not ObjectId.is_valid(scenario_id):
            raise ValueError(f"Invalid scenario_id format: {scenario_id}")

        collection = db().scenario_analysis_results
        query: Dict[str, Any] = {"scenario_id": scenario_id}
        if workflow:
            query["workflow"] = workflow

        # Try sorting by updated_at first, fall back to created_at if updated_at doesn't exist
        # Use a compound sort that handles missing fields gracefully
        document = collection.find_one(
            query,
            sort=[
                ("updated_at", -1),
                ("created_at", -1),
            ],
        )
        
        # If no document found with updated_at, try with created_at only
        if not document:
            document = collection.find_one(
                query,
                sort=[("created_at", -1)],
            )
        
        if not document:
            logger.debug(
                f"No scenario analysis result found for scenario_id={scenario_id}, workflow={workflow}"
            )
            return None

        document["_id"] = str(document["_id"])
        return document
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching scenario analysis result for scenario {scenario_id}: {e}",
            exc_info=True,
        )
        raise


async def delete_scenario(scenario_id: str) -> bool:
    """
    Delete a scenario and cascade delete associated cost estimates, scenario analysis results, and Pinecone vectors.
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

        # Delete scenario cost estimates
        scenario_cost_estimates_collection = db().scenario_cost_estimates
        scenario_cost_estimates_deleted = scenario_cost_estimates_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        if scenario_cost_estimates_deleted > 0:
            logger.info(f"Deleted {scenario_cost_estimates_deleted} scenario cost estimates for scenario: {scenario_id}")

        # Delete scenario analysis results
        scenario_analysis_results_collection = db().scenario_analysis_results
        analysis_results_deleted = scenario_analysis_results_collection.delete_many(
            {"scenario_id": scenario_id}
        ).deleted_count
        if analysis_results_deleted > 0:
            logger.info(f"Deleted {analysis_results_deleted} scenario analysis results for scenario: {scenario_id}")

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
