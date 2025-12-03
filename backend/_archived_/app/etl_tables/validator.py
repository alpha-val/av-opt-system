from typing import Dict, Any, List


def validate_kg_structure(
    kg_data: Dict[str, Any], ontology: Dict[str, Any]
) -> List[str]:
    """
    Validate extracted KG against ontology rules.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    valid_node_types = set(ontology.get("NODE_TYPES", []))
    valid_edge_types = set(ontology.get("EDGE_TYPES", []))

    # Validate nodes
    for node in kg_data.get("nodes", []):
        node_id = node.get("id", "unknown")

        # Check required fields
        if not node.get("id"):
            errors.append(f"Node missing 'id'")
        if not node.get("type"):
            errors.append(f"Node {node_id} missing 'type'")
        elif node["type"] not in valid_node_types:
            errors.append(f"Node {node_id} has invalid type: {node['type']}")

        # Check properties
        props = node.get("properties", {})
        if not isinstance(props, dict):
            errors.append(f"Node {node_id} properties must be dict")

        # Check name for non-structural nodes
        if node.get("type") not in ("Table", "TableRow") and "name" not in props:
            errors.append(f"Node {node_id} missing 'name' property")

    # Validate edges
    node_ids = {n.get("id") for n in kg_data.get("nodes", [])}
    for edge in kg_data.get("edges", []):
        # Check required fields
        if not edge.get("source"):
            errors.append("Edge missing 'source'")
        if not edge.get("target"):
            errors.append("Edge missing 'target'")
        if not edge.get("type"):
            errors.append("Edge missing 'type'")
        elif edge["type"] not in valid_edge_types:
            errors.append(f"Edge has invalid type: {edge['type']}")

        # Check endpoints exist
        if edge.get("source") not in node_ids:
            errors.append(f"Edge source not in nodes: {edge.get('source')}")
        if edge.get("target") not in node_ids:
            errors.append(f"Edge target not in nodes: {edge.get('target')}")

    return errors
