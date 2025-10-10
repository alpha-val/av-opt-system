from typing import List, Dict, Any, Optional
from pymongo import UpdateOne
from ..bronze_store import _db
import logging
import datetime

logger = logging.getLogger(__name__)


def store_silver_nodes(
    nodes: List[Dict[str, Any]],
    project_id: str,
    doc_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> int:
    """
    Store nodes in Silver collection with upsert.

    Args:
        nodes: List of node dictionaries OR dict with 'nodes' key
        project_id: Project identifier
        doc_id: Optional document identifier
        user_id: Optional user identifier

    Returns:
        Number of nodes written
    """
    # Handle nested structure: {'nodes': [...]]} or {'nodes': {'nodes': [...]}}
    if isinstance(nodes, dict):
        if "nodes" in nodes:
            nodes = nodes["nodes"]
            # Check if still nested
            if isinstance(nodes, dict) and "nodes" in nodes:
                nodes = nodes["nodes"]

    if not nodes:
        logger.warning("[TABULAR_STORE] No nodes to store")
        return 0

    if not isinstance(nodes, list):
        logger.error(f"[TABULAR_STORE] Invalid nodes type: {type(nodes)}")
        return 0

    logger.info(f"[TABULAR_STORE] Processing {len(nodes)} nodes")

    try:
        operations = []
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        for node in nodes:
            # Validate node structure
            if not isinstance(node, dict):
                logger.warning(f"[TABULAR_STORE] Skipping non-dict node: {type(node)}")
                continue

            if not node.get("id"):
                logger.warning(f"[TABULAR_STORE] Skipping node without id: {node}")
                continue

            # Get properties and clean them
            properties = node.get("properties", {})
            if isinstance(properties, dict):
                properties = properties.copy()
            else:
                properties = {}

            # Add metadata to properties
            if doc_id:
                properties["doc_id"] = doc_id
            if user_id:
                properties["user_id"] = user_id
            properties["project_id"] = project_id
            properties["updated_at"] = timestamp
            properties["created_at"] = timestamp
            properties["artifact_type"] = "tabular_data"

            # Build node document
            node_doc = {
                "_id": node["id"],
                "id": node["id"],
                "type": node.get("type", "Unknown"),
                "properties": properties,
            }

            # Add metadata if present
            if "metadata" in node and isinstance(node["metadata"], dict):
                node_doc["metadata"] = node["metadata"]

            operations.append(
                UpdateOne(
                    {"_id": node["id"], "project_id": project_id},
                    {
                        "$set": node_doc,
                    },
                    upsert=True,
                )
            )

        if not operations:
            logger.warning("[TABULAR_STORE] No valid nodes to store after filtering")
            return 0

        # Execute bulk write
        result = _db.entities.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count

        logger.info(
            f"[TABULAR_STORE] Stored {count} nodes (upserted: {result.upserted_count}, modified: {result.modified_count})"
        )
        return count

    except Exception as e:
        logger.error(f"[TABULAR_STORE] Failed to store nodes: {e}")
        import traceback

        traceback.print_exc()
        return 0


def store_silver_edges(
    edges: List[Dict[str, Any]],
    project_id: str,
    doc_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> int:
    """
    Store edges in Silver collection with upsert.

    Args:
        edges: List of edge dictionaries OR dict with 'edges' key
        project_id: Project identifier
        doc_id: Optional document identifier
        user_id: Optional user identifier

    Returns:
        Number of edges written
    """
    # Handle nested structure: {'edges': [...]]} or {'edges': {'edges': [...]}}
    if isinstance(edges, dict):
        if "edges" in edges:
            edges = edges["edges"]
            # Check if still nested
            if isinstance(edges, dict) and "edges" in edges:
                edges = edges["edges"]

    if not edges:
        logger.warning("[TABULAR_STORE] No edges to store")
        return 0

    if not isinstance(edges, list):
        logger.error(f"[TABULAR_STORE] Invalid edges type: {type(edges)}")
        return 0

    logger.info(f"[TABULAR_STORE] Processing {len(edges)} edges")

    try:
        operations = []
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        for edge in edges:
            # Validate edge structure
            if not isinstance(edge, dict):
                logger.warning(f"[TABULAR_STORE] Skipping non-dict edge: {type(edge)}")
                continue

            source = edge.get("source")
            target = edge.get("target")
            edge_type = edge.get("type")

            if not source or not target or not edge_type:
                logger.warning(f"[TABULAR_STORE] Skipping incomplete edge: {edge}")
                continue

            # Generate deterministic edge ID
            edge_id = f"{source}__{edge_type}__{target}"

            # Get properties and clean them
            properties = edge.get("properties", {})
            if isinstance(properties, dict):
                properties = properties.copy()
            else:
                properties = {}

            # Add metadata to properties
            if doc_id:
                properties["doc_id"] = doc_id
            if user_id:
                properties["user_id"] = user_id

            properties["project_id"] = project_id
            properties["updated_at"] = timestamp
            properties["created_at"] = timestamp
            properties["artifact_type"] = "tabular_data"

            # Build edge document
            edge_doc = {
                "_id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "properties": properties,
            }

            # Add metadata if present
            if "metadata" in edge and isinstance(edge["metadata"], dict):
                edge_doc["metadata"] = edge["metadata"]

            operations.append(
                UpdateOne(
                    {"_id": edge_id, "project_id": project_id},
                    {
                        "$set": edge_doc,
                    },
                    upsert=True,
                )
            )

        if not operations:
            logger.warning("[TABULAR_STORE] No valid edges to store after filtering")
            return 0

        # Execute bulk write
        result = _db.relations.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count

        logger.info(
            f"[TABULAR_STORE] Stored {count} edges (upserted: {result.upserted_count}, modified: {result.modified_count})"
        )
        return count

    except Exception as e:
        logger.error(f"[TABULAR_STORE] Failed to store edges: {e}")
        import traceback

        traceback.print_exc()
        return 0


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

        logger.info(f"[TABULAR_STORE] Retrieved {len(nodes)} nodes")
        return nodes

    except Exception as e:
        logger.error(f"[TABULAR_STORE] Failed to retrieve nodes: {e}")
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

        logger.info(f"[TABULAR_STORE] Retrieved {len(edges)} edges")
        return edges

    except Exception as e:
        logger.error(f"[TABULAR_STORE] Failed to retrieve edges: {e}")
        return []
