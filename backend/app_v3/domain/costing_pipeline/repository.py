"""
Repository for scenario_cost_estimates collection.

This module provides database operations for component-based cost estimates
stored in the "scenario_cost_estimates" collection.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging

from ...adapters.mongo.client import db
from .schemas import ComponentCostEstimateCreate, ComponentCostEstimateOut

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


async def create_scenario_cost_estimate(
    data: ComponentCostEstimateCreate,
    project_id: str,
) -> ComponentCostEstimateOut:
    """
    Create a new scenario cost estimate in the MongoDB collection.
    
    Args:
        data: Cost estimate creation data
        project_id: Project identifier
        
    Returns:
        Created cost estimate object
    """
    try:
        # Generate a temporary unique ID to satisfy the unique index constraint during insertion
        temp_id = str(ObjectId())
        
        # Build document for insertion
        # Convert components list to dict format for storage
        components_dict = {
            comp.component_id: {
                "lever_values": comp.lever_values,
                "lever_types": comp.lever_types,
            }
            for comp in data.components
        }
        
        doc = {
            "id": temp_id,  # Temporary ID to satisfy unique index
            "name": data.name,
            "description": data.description,
            "scenario_id": data.scenario_id,
            "project_id": project_id,
            "components_config": {
                "components": components_dict,
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        
        # Insert into MongoDB
        collection = db().scenario_cost_estimates
        result = collection.insert_one(doc)
        cost_estimate_id = str(result.inserted_id)
        
        # Update the document to set id field to match _id (replacing temporary ID)
        collection.update_one(
            {"_id": result.inserted_id}, {"$set": {"id": cost_estimate_id}}
        )
        
        logger.info(
            f"Created scenario cost estimate: {cost_estimate_id} for scenario: {data.scenario_id}"
        )
        
        # Fetch and return the created cost estimate
        return await get_scenario_cost_estimate(cost_estimate_id)
        
    except InvalidId as e:
        logger.error(f"Invalid scenario_id format: {data.scenario_id}")
        raise ValueError(f"Invalid scenario_id format: {data.scenario_id}") from e
    except Exception as e:
        logger.error(f"Error creating scenario cost estimate: {e}", exc_info=True)
        raise


async def list_scenario_cost_estimates(
    scenario_id: Optional[str] = None,
) -> List[ComponentCostEstimateOut]:
    """
    List all scenario cost estimates, optionally filtered by scenario_id.
    
    Args:
        scenario_id: Optional scenario ID to filter cost estimates
        
    Returns:
        List of cost estimate objects
    """
    try:
        collection = db().scenario_cost_estimates
        query = {}
        if scenario_id:
            query["scenario_id"] = scenario_id
        
        cursor = collection.find(query).sort("created_at", -1)
        cost_estimates = []
        
        for doc in cursor:
            try:
                # Use id field if it exists, otherwise fall back to _id
                cost_estimate_id = doc.get("id") or str(doc["_id"])
                cost_estimate = ComponentCostEstimateOut(
                    id=cost_estimate_id,
                    name=doc.get("name", ""),
                    description=doc.get("description"),
                    scenario_id=doc.get("scenario_id", ""),
                    project_id=doc.get("project_id"),
                    created_at=doc.get("created_at", _now()).isoformat(),
                    updated_at=doc.get("updated_at", _now()).isoformat(),
                    components_config=doc.get("components_config"),
                    cost_report=doc.get("cost_report"),
                    metadata=doc.get("metadata"),
                )
                cost_estimates.append(cost_estimate)
            except Exception as e:
                logger.warning(f"Error parsing cost estimate document: {e}")
                continue
        
        logger.info(
            f"Listed {len(cost_estimates)} scenario cost estimates"
            + (f" for scenario: {scenario_id}" if scenario_id else "")
        )
        return cost_estimates
        
    except Exception as e:
        logger.error(f"Error listing scenario cost estimates: {e}", exc_info=True)
        raise


async def get_scenario_cost_estimate(
    cost_estimate_id: str,
) -> Optional[ComponentCostEstimateOut]:
    """
    Get a scenario cost estimate by ID.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        
    Returns:
        Cost estimate object if found, None otherwise
    """
    try:
        # Validate ObjectId format
        try:
            ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")
        
        collection = db().scenario_cost_estimates
        doc = collection.find_one({"_id": ObjectId(cost_estimate_id)})
        
        if not doc:
            logger.warning(f"Scenario cost estimate not found: {cost_estimate_id}")
            return None
        
        # Use id field if it exists, otherwise fall back to _id
        cost_estimate_id_str = doc.get("id") or str(doc["_id"])
        cost_estimate = ComponentCostEstimateOut(
            id=cost_estimate_id_str,
            name=doc.get("name", ""),
            description=doc.get("description"),
            scenario_id=doc.get("scenario_id", ""),
            project_id=doc.get("project_id"),
            created_at=doc.get("created_at", _now()).isoformat(),
            updated_at=doc.get("updated_at", _now()).isoformat(),
            components_config=doc.get("components_config"),
            cost_report=doc.get("cost_report"),
            metadata=doc.get("metadata"),
        )
        
        return cost_estimate
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario cost estimate: {e}", exc_info=True)
        raise


async def update_scenario_cost_estimate_metadata(
    cost_estimate_id: str,
    cost_report: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ComponentCostEstimateOut:
    """
    Update the cost_report and/or metadata fields of a scenario cost estimate.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        cost_report: Cost comparison report dictionary
        metadata: Additional metadata dictionary
        
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
        
        collection = db().scenario_cost_estimates
        
        # Check if cost estimate exists
        existing = collection.find_one({"_id": object_id})
        if not existing:
            raise ValueError(f"Scenario cost estimate not found: {cost_estimate_id}")
        
        # Build update document
        update_doc = {"updated_at": _now()}
        if cost_report is not None:
            update_doc["cost_report"] = cost_report
        if metadata is not None:
            update_doc["metadata"] = metadata
        
        collection.update_one({"_id": object_id}, {"$set": update_doc})
        
        logger.info(f"Updated metadata for scenario cost estimate: {cost_estimate_id}")
        
        # Fetch and return the updated cost estimate
        return await get_scenario_cost_estimate(cost_estimate_id)
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            f"Error updating scenario cost estimate metadata: {e}", exc_info=True
        )
        raise


async def delete_scenario_cost_estimate(cost_estimate_id: str) -> bool:
    """
    Delete a scenario cost estimate by ID.
    
    Args:
        cost_estimate_id: Cost estimate identifier
        
    Returns:
        True if deleted, False if not found
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(cost_estimate_id)
        except Exception:
            raise ValueError(f"Invalid cost_estimate_id format: {cost_estimate_id}")
        
        collection = db().scenario_cost_estimates
        result = collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            logger.warning(
                f"Scenario cost estimate not found for deletion: {cost_estimate_id}"
            )
            return False
        
        logger.info(f"Deleted scenario cost estimate: {cost_estimate_id}")
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario cost estimate: {e}", exc_info=True)
        raise

