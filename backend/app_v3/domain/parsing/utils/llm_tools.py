"""LLM tools and utilities for entity extraction."""

from __future__ import annotations
import json
from typing import Dict, Any

from ...ontology.loader import get_ontology


def _get_ontology_dict() -> Dict[str, Any]:
    """
    Get ontology as a dictionary compatible with old TOOLS format.
    
    Converts OntologySchema to dict format expected by TOOLS.
    """
    ont = get_ontology()
    entity_ont = ont.entity_ontology
    
    return {
        "NODE_TYPES": entity_ont.node_types,
        "EDGE_TYPES": entity_ont.edge_types,
        "NODE_PROPERTIES": entity_ont.node_properties,
        "EDGE_PROPERTIES": entity_ont.edge_properties,
        "NODE_DESCRIPTIONS": entity_ont.node_descriptions,
        "EDGE_DESCRIPTIONS": entity_ont.edge_descriptions,
        "NODE_PROP_EXAMPLES": entity_ont.node_prop_examples,
        "EDGE_PROP_EXAMPLES": entity_ont.edge_prop_examples,
    }


# Get ontology for TOOLS definition
_ont = _get_ontology_dict()

# OpenAI function calling schemas for node/edge extraction
TOOLS = [
    # -------------------------------------------------------------------------
    # 1. Node extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_nodes",
            "description": "Extract nodes (entities) from the text according to ontology.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string", "enum": _ont["NODE_TYPES"]},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"}
                                        for p in _ont["NODE_PROPERTIES"]
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["type"],
                        },
                    }
                },
                "required": ["nodes"],
            },
        },
    },
    # -------------------------------------------------------------------------
    # 2. Edge extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_edges",
            "description": "Extract relationships (edges) between nodes according to ontology.",
            "parameters": {
                "type": "object",
                "properties": {
                    "edges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "type": {"type": "string", "enum": _ont["EDGE_TYPES"]},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"}
                                        for p in _ont["EDGE_PROPERTIES"]
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["source", "target", "type"],
                        },
                    }
                },
                "required": ["edges"],
            },
        },
    },
]


def sanitize_for_json(data):
    """Recursively convert sets to lists for JSON serialization."""
    if isinstance(data, set):
        return list(data)
    elif isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(v) for v in data]
    return data


def is_valid_json(json_string: str) -> bool:
    """Check if a string is valid JSON."""
    try:
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False

