"""
Cost estimate repository for MongoDB operations.

This module provides database operations for cost estimates stored in the "cost_estimates" collection.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging

from ...adapters.mongo.client import db
from .schemas import CostEstimateCreate, CostEstimateUpdate, CostEstimateOut

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


async def create_cost_estimate(data: CostEstimateCreate) -> CostEstimateOut:
    """
    Create a new cost estimate in the MongoDB collection.
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
            "scenario_id": data.scenario_id,
            "created_at": _now(),
            "updated_at": _now(),
        }

        # Insert into MongoDB
        collection = db().cost_estimates
        result = collection.insert_one(doc)
        cost_estimate_id = str(result.inserted_id)

        # Update the document to set id field to match _id (replacing temporary ID)
        collection.update_one(
            {"_id": result.inserted_id}, {"$set": {"id": cost_estimate_id}}
        )

        logger.info(f"Created cost estimate: {cost_estimate_id} for scenario: {data.scenario_id}")

        # Fetch and return the created cost estimate
        return await get_cost_estimate(cost_estimate_id)

    except InvalidId as e:
        logger.error(f"Invalid scenario_id format: {data.scenario_id}")
        raise ValueError(f"Invalid scenario_id format: {data.scenario_id}") from e
    except Exception as e:
        logger.error(f"Error creating cost estimate: {e}", exc_info=True)
        raise


async def list_cost_estimates(scenario_id: Optional[str] = None) -> List[CostEstimateOut]:
    """
    List all cost estimates, optionally filtered by scenario_id.
    """
    try:
        collection = db().cost_estimates
        query = {}
        if scenario_id:
            query["scenario_id"] = scenario_id

        cursor = collection.find(query).sort("created_at", -1)
        cost_estimates = []

        for doc in cursor:
            try:
                # Use id field if it exists, otherwise fall back to _id
                cost_estimate_id = doc.get("id") or str(doc["_id"])
                cost_estimate = CostEstimateOut(
                    id=cost_estimate_id,
                    name=doc.get("name", ""),
                    description=doc.get("description"),
                    scenario_id=doc.get("scenario_id", ""),
                    created_at=doc.get("created_at", _now()),
                    updated_at=doc.get("updated_at", _now()),
                )
                cost_estimates.append(cost_estimate)
            except Exception as e:
                logger.warning(f"Error parsing cost estimate document: {e}")
                continue

        logger.info(f"Listed {len(cost_estimates)} cost estimates" + (f" for scenario: {scenario_id}" if scenario_id else ""))
        return cost_estimates

    except Exception as e:
        logger.error(f"Error listing cost estimates: {e}", exc_info=True)
        raise


async def get_cost_estimate(cost_estimate_id: str) -> Optional[CostEstimateOut]:
    """
    Get a cost estimate by ID.
    """
    try:
        # Validate ObjectId format
        try:
            ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")

        collection = db().cost_estimates
        doc = collection.find_one({"_id": ObjectId(cost_estimate_id)})

        if not doc:
            logger.warning(f"Cost estimate not found: {cost_estimate_id}")
            return None

        # Use id field if it exists, otherwise fall back to _id
        cost_estimate_id_str = doc.get("id") or str(doc["_id"])
        cost_estimate = CostEstimateOut(
            id=cost_estimate_id_str,
            name=doc.get("name", ""),
            description=doc.get("description"),
            scenario_id=doc.get("scenario_id", ""),
            created_at=doc.get("created_at", _now()),
            updated_at=doc.get("updated_at", _now()),
        )

        # Compute the cost estimate
        
        return cost_estimate

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error getting cost estimate: {e}", exc_info=True)
        raise


async def update_cost_estimate(
    cost_estimate_id: str, data: CostEstimateUpdate
) -> CostEstimateOut:
    """
    Update an existing cost estimate.
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")

        collection = db().cost_estimates

        # Check if cost estimate exists
        existing = collection.find_one({"_id": object_id})
        if not existing:
            raise ValueError(f"Cost estimate not found: {cost_estimate_id}")

        # Build update document with only provided fields
        update_doc = {"updated_at": _now()}
        if data.name is not None:
            update_doc["name"] = data.name
        if data.description is not None:
            update_doc["description"] = data.description

        # Update in MongoDB
        collection.update_one({"_id": object_id}, {"$set": update_doc})

        logger.info(f"Updated cost estimate: {cost_estimate_id}")

        # Fetch and return the updated cost estimate
        return await get_cost_estimate(cost_estimate_id)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error updating cost estimate: {e}", exc_info=True)
        raise


async def delete_cost_estimate(cost_estimate_id: str) -> bool:
    """
    Delete a cost estimate by ID.
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")

        collection = db().cost_estimates
        result = collection.delete_one({"_id": object_id})

        if result.deleted_count == 0:
            logger.warning(f"Cost estimate not found for deletion: {cost_estimate_id}")
            return False

        logger.info(f"Deleted cost estimate: {cost_estimate_id}")
        return True

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error deleting cost estimate: {e}", exc_info=True)
        raise


async def update_cost_estimate_metadata(
    cost_estimate_id: str, metadata: dict
) -> CostEstimateOut:
    """
    Update the metadata field of a cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        metadata: Metadata dictionary to store (e.g., cost comparison report)
        
    Returns:
        Updated cost estimate object
        
    Raises:
        ValueError: If cost estimate not found or invalid ID format
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")

        collection = db().cost_estimates

        # Check if cost estimate exists
        existing = collection.find_one({"_id": object_id})
        if not existing:
            raise ValueError(f"Cost estimate not found: {cost_estimate_id}")

        # Update metadata field
        update_doc = {
            "updated_at": _now(),
            "metadata": metadata,
        }

        collection.update_one({"_id": object_id}, {"$set": update_doc})

        logger.info(f"Updated metadata for cost estimate: {cost_estimate_id}")

        # Fetch and return the updated cost estimate
        return await get_cost_estimate(cost_estimate_id)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error updating cost estimate metadata: {e}", exc_info=True)
        raise

