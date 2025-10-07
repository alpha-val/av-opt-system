from typing import List, Dict, Any, Optional
import logging
from pymongo import UpdateOne
import datetime
from ..bronze_store import _db

logger = logging.getLogger(__name__)


def store_silver_nodes(nodes: List[Dict[str, Any]], project_id: str) -> int:
    """
    Store nodes in Silver collection with upsert.

    Args:
        nodes: List of node dictionaries with id, type, properties
        project_id: Project identifier

    Returns:
        Number of nodes written
    """
    if not nodes:
        logger.warning("[SILVER_STORE] No nodes to store")
        return 0

    try:

        # Prepare bulk operations
        operations = []
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        for node in nodes:
            if not node.get("id"):
                logger.warning(f"[SILVER_STORE] Skipping node without id: {node}")
                continue

            # Build node document WITHOUT created_at in $set
            node_doc = {
                "_id": node["id"],
                "id": node["id"],
                "type": node.get("type", "Unknown"),
                "properties": node.get("properties", {}),
                "project_id": project_id,
                "updated_at": timestamp,  # Only updated_at in $set
            }

            # Add metadata if present
            if "metadata" in node:
                node_doc["metadata"] = node["metadata"]

            operations.append(
                UpdateOne(
                    {"_id": node["id"], "project_id": project_id},
                    {
                        "$set": node_doc,  # Does NOT include created_at
                        "$setOnInsert": {"created_at": timestamp},  # Only set on insert
                    },
                    upsert=True,
                )
            )

        if not operations:
            logger.warning("[SILVER_STORE] No valid nodes to store")
            return 0

        # Execute bulk write
        result = _db.silver_nodes.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count

        logger.info(
            f"[SILVER_STORE] Stored {count} nodes (upserted: {result.upserted_count}, modified: {result.modified_count})"
        )
        return count

    except Exception as e:
        logger.error(f"[SILVER_STORE] Failed to store nodes: {e}")
        import traceback

        traceback.print_exc()
        return 0


def store_silver_edges(edges: List[Dict[str, Any]], project_id: str) -> int:
    """
    Store edges in Silver collection with upsert.

    Args:
        edges: List of edge dictionaries with source, target, type
        project_id: Project identifier

    Returns:
        Number of edges written
    """
    if not edges:
        logger.warning("[SILVER_STORE] No edges to store")
        return 0

    try:
        # Prepare bulk operations
        operations = []
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            edge_type = edge.get("type")

            if not source or not target or not edge_type:
                logger.warning(f"[SILVER_STORE] Skipping incomplete edge: {edge}")
                continue

            # Generate deterministic edge ID
            edge_id = f"{source}__{edge_type}__{target}"

            # Build edge document WITHOUT created_at in $set
            edge_doc = {
                "_id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "properties": edge.get("properties", {}),
                "project_id": project_id,
                "updated_at": timestamp,  # Only updated_at in $set
            }

            # Add metadata if present
            if "metadata" in edge:
                edge_doc["metadata"] = edge["metadata"]

            operations.append(
                UpdateOne(
                    {"_id": edge_id, "project_id": project_id},
                    {
                        "$set": edge_doc,  # Does NOT include created_at
                        "$setOnInsert": {"created_at": timestamp},  # Only set on insert
                    },
                    upsert=True,
                )
            )

        if not operations:
            logger.warning("[SILVER_STORE] No valid edges to store")
            return 0

        # Execute bulk write
        result = _db.silver_edges.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count

        logger.info(
            f"[SILVER_STORE] Stored {count} edges (upserted: {result.upserted_count}, modified: {result.modified_count})"
        )
        return count

    except Exception as e:
        logger.error(f"[SILVER_STORE] Failed to store edges: {e}")
        import traceback

        traceback.print_exc()
        return 0


def ensure_silver_indexes():
    """
    Create indexes for Silver collections to optimize queries.
    """
    try:
        # Node indexes
        _db.silver_nodes.create_index([("project_id", 1)])
        _db.silver_nodes.create_index([("type", 1)])
        _db.silver_nodes.create_index([("project_id", 1), ("type", 1)])
        _db.silver_nodes.create_index([("properties.name", 1)])
        _db.silver_nodes.create_index([("properties.row_index", 1)])
        _db.silver_nodes.create_index([("created_at", -1)])

        # Edge indexes
        _db.silver_edges.create_index([("project_id", 1)])
        _db.silver_edges.create_index([("type", 1)])
        _db.silver_edges.create_index([("source", 1)])
        _db.silver_edges.create_index([("target", 1)])
        _db.silver_edges.create_index([("source", 1), ("type", 1)])
        _db.silver_edges.create_index([("target", 1), ("type", 1)])
        _db.silver_edges.create_index([("project_id", 1), ("type", 1)])
        _db.silver_edges.create_index([("created_at", -1)])

        logger.info("[SILVER_STORE] Indexes ensured")

    except Exception as e:
        logger.error(f"[SILVER_STORE] Failed to create indexes: {e}")


def get_silver_nodes(
    project_id: str, node_type: Optional[str] = None, limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Retrieve nodes from Silver collection.

    Args:
        project_id: Project identifier
        node_type: Optional filter by node type
        limit: Maximum nodes to return

    Returns:
        List of node documents
    """
    try:
        query = {"project_id": project_id}
        if node_type:
            query["type"] = node_type

        cursor = _db.silver_nodes.find(query).limit(limit)
        nodes = list(cursor)

        logger.info(f"[SILVER_STORE] Retrieved {len(nodes)} nodes")
        return nodes

    except Exception as e:
        logger.error(f"[SILVER_STORE] Failed to retrieve nodes: {e}")
        return []


def get_silver_edges(
    project_id: str,
    edge_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Retrieve edges from Silver collection.

    Args:
        project_id: Project identifier
        edge_type: Optional filter by edge type
        source_id: Optional filter by source node
        target_id: Optional filter by target node
        limit: Maximum edges to return

    Returns:
        List of edge documents
    """
    try:

        query = {"project_id": project_id}
        if edge_type:
            query["type"] = edge_type
        if source_id:
            query["source"] = source_id
        if target_id:
            query["target"] = target_id

        cursor = _db.silver_edges.find(query).limit(limit)
        edges = list(cursor)

        logger.info(f"[SILVER_STORE] Retrieved {len(edges)} edges")
        return edges

    except Exception as e:
        logger.error(f"[SILVER_STORE] Failed to retrieve edges: {e}")
        return []
