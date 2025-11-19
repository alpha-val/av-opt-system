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
    # -------------------------------------------------------------------------
    # 3. Recommendations extraction (with entity specifications)
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_recommendations",
            "description": "Extract recommendations for system redesign based on global objectives, including detailed specifications of relevant entities to extract",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "recommendation_id": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "description": "Category type (e.g., 'Equipment Upgrade', 'Process Optimization', 'Operational Change', 'Infrastructure', 'Material Change', 'Control System', 'Energy Efficiency', 'Maintenance Strategy', 'Safety Enhancement', 'Environmental Improvement')",
                                },
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "rationale": {"type": "string"},
                                "priority": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                },
                                "recommendation_category": {
                                    "type": "string",
                                    "enum": ["primary", "secondary", "other"],
                                    "description": "Classification of recommendation importance: 'primary' for high-impact direct solutions, 'secondary' for supporting changes, 'other' for alternative approaches",
                                },
                                "estimated_impact": {"type": "string"},
                                "implementation_complexity": {"type": "string"},
                                "estimated_cost_range": {
                                    "type": "string",
                                    "description": "Rough cost estimate range (e.g., 'Low: $10K-$50K', 'Medium: $50K-$200K', 'High: $200K-$500K', 'Very High: $500K+')",
                                },
                                "time_to_implement": {
                                    "type": "string",
                                    "description": "Estimated implementation timeline (e.g., '1-3 months', '3-6 months', '6-12 months', '12+ months')",
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of recommendation_ids that this recommendation depends on",
                                },
                                "alternative_to": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of recommendation_ids that this recommendation is an alternative to",
                                },
                            },
                            "required": [
                                "recommendation_id",
                                "type",
                                "title",
                                "description",
                                "priority",
                                "recommendation_category",
                            ],
                        },
                    },
                    "relevant_entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique identifier for the entity node",
                                },
                                "type": {
                                    "type": "string",
                                    "enum": _ont["NODE_TYPES"],
                                    "description": "Entity type from NODE_TYPES",
                                },
                                "properties": {
                                    "type": "object",
                                    "properties": dict(
                                        # Include all NODE_PROPERTIES
                                        {
                                            p: {"type": "string"}
                                            for p in _ont["NODE_PROPERTIES"]
                                        },
                                        **{
                                            # MSIO classification fields (required)
                                            "discipline": {
                                                "type": "string",
                                                "description": "MSIO Discipline name",
                                            },
                                            "category": {
                                                "type": "string",
                                                "description": "MSIO Category name",
                                            },
                                            "subcategory": {
                                                "type": "string",
                                                "description": "MSIO Subcategory name",
                                            },
                                            "entity": {
                                                "type": "string",
                                                "description": "MSIO Entity name",
                                            },
                                            # Additional fields for extraction guidance
                                            "expected_attributes": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "List of attribute names that should be extracted for this entity",
                                            },
                                            "evidence_locations": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Text snippets, page references, or section anchors where this entity is mentioned",
                                            },
                                            "extraction_rationale": {
                                                "type": "string",
                                                "description": "Explanation of why this entity is relevant to the recommendations",
                                            },
                                            "extraction_priority": {
                                                "type": "string",
                                                "enum": ["high", "medium", "low"],
                                                "description": "Priority level for extracting this entity",
                                            },
                                        },
                                    ),
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["id", "type", "properties"],
                        },
                    },
                },
                "required": ["recommendations", "relevant_entities"],
            },
        },
    },  # -------------------------------------------------------------------------
    # 4. Structured report extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_structured_report",
            "description": "Extract structured base case report summary with sections, equipment, materials, costs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_case_extract": {
                        "type": "object",
                        "description": "Structured extraction of base case document",
                        "properties": {
                            "doc_header": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "sections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "anchor": {"type": "string"},
                                        "subsections": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "process_flows": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "design_criteria": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "equipment": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "materials": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "instrumentation_controls": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "site_data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "codes_standards": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "policies_recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "constraints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "costs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": True,
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "risks_uncertainties": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "provenance": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                        },
                        "additionalProperties": True,
                    }
                },
                "required": ["base_case_extract"],
            },
        },
    },
]

# OpenAI function calling schemas for node/edge extraction
# Filter out "Recommendation" from NODE_TYPES for objective-driven extraction
# Recommendations must be embedded in entity properties, not created as separate nodes
_objective_driven_node_types = [
    nt for nt in _ont["NODE_TYPES"] 
    if nt.lower() not in ["recommendation", "recommendations"]
]

TOOLS_OBJECTIVE_DRIVEN = [
    # -------------------------------------------------------------------------
    # 1. Node extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_nodes",
            "description": "Extract nodes (entities) from the text according to ontology. IMPORTANT: Recommendations must be embedded within entity properties.recommendations array, NOT created as separate nodes with type='Recommendation'. Only extract entity nodes (Equipment, Process, Material, etc.) and embed recommendations within their properties.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {
                                    "type": "string", 
                                    "enum": _objective_driven_node_types,
                                    "description": "Entity type from NODE_TYPES. MUST NOT be 'Recommendation' - recommendations are embedded in properties.recommendations array, not as separate nodes."
                                },
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        # Include all ontology node properties
                                        **{
                                            p: {"type": "string"}
                                            for p in _ont["NODE_PROPERTIES"]
                                        },
                                        # Explicitly add recommendations array for objective-driven extraction
                                        "recommendations": {
                                            "type": "array",
                                            "description": "Array of recommendations for achieving the global objective that relate to this entity",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "description": "Unique identifier for the recommendation"
                                                    },
                                                    "type": {
                                                        "type": "string",
                                                        "description": "Type of recommendation (e.g., 'Equipment Upgrade', 'Process Optimization', 'Operational Change', etc.)"
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name or title of the recommendation"
                                                    },
                                                    "rationale": {
                                                        "type": "string",
                                                        "description": "Explanation of why this recommendation is relevant to achieving the global objective"
                                                    },
                                                    "relevance": {
                                                        "type": "string",
                                                        "enum": ["primary", "secondary", "other"],
                                                        "description": "Relevance level: primary (direct high-impact), secondary (supporting/enabling), or other (alternative/innovative)"
                                                    },
                                                    "change_direction": {
                                                        "type": "string",
                                                        "enum": ["increase", "decrease", "no change"],
                                                        "description": "Direction of change needed for this entity"
                                                    },
                                                    "change_unit": {
                                                        "type": "string",
                                                        "description": "Unit of measurement for the change (e.g., 'gpm', 'tons/hr', 'units/day')"
                                                    },
                                                    "change_magnitude": {
                                                        "type": "string",
                                                        "description": "Magnitude of change (numeric value as string)"
                                                    },
                                                    "change_magnitude_unit": {
                                                        "type": "string",
                                                        "description": "Unit for the change magnitude"
                                                    },
                                                    "change_magnitude_direction": {
                                                        "type": "string",
                                                        "enum": ["increase", "decrease", "no change"],
                                                        "description": "Direction of the magnitude change"
                                                    },
                                                    "evidence_text": {
                                                        "type": "string",
                                                        "description": "Text snippet, page reference, or section anchor that supports this recommendation"
                                                    },
                                                    "confidence": {
                                                        "type": "number",
                                                        "minimum": 0.0,
                                                        "maximum": 1.0,
                                                        "description": "Confidence score for this recommendation (0.0 to 1.0)"
                                                    }
                                                },
                                                "required": ["id", "type", "name", "rationale", "relevance"],
                                            }
                                        },
                                        # Explicitly add attributes array for objective-driven extraction (MANDATORY)
                                        "attributes": {
                                            "type": "array",
                                            "description": "MANDATORY: Array of attributes for this entity (e.g., capacity_value, capacity_unit, description, etc.). This field is required and must be present for all entities.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Attribute name (e.g., 'capacity_value', 'capacity_unit', 'description')"
                                                    },
                                                    "value": {
                                                        "type": ["number", "string", "null"],
                                                        "description": "Attribute value (numeric or string)"
                                                    },
                                                    "unit": {
                                                        "type": ["string", "null"],
                                                        "description": "Unit of measurement for the attribute (if applicable)"
                                                    },
                                                    "evidence_text": {
                                                        "type": ["string", "null"],
                                                        "description": "Text snippet, page reference, or section anchor where this attribute value was found"
                                                    },
                                                    "confidence": {
                                                        "type": "number",
                                                        "minimum": 0.0,
                                                        "maximum": 1.0,
                                                        "description": "Confidence score for this attribute (0.0 to 1.0)"
                                                    }
                                                },
                                                "required": ["name"],
                                            }
                                        }
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
    # -------------------------------------------------------------------------
    # 3. Structured report extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_structured_report",
            "description": "Extract structured base case report summary with sections, equipment, materials, costs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_case_extract": {
                        "type": "object",
                        "description": "Structured extraction of base case document",
                        "properties": {
                            "doc_header": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "sections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "anchor": {"type": "string"},
                                        "subsections": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "process_flows": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "design_criteria": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "equipment": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "materials": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "instrumentation_controls": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "site_data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "codes_standards": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "policies_recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "constraints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "costs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": True,
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "risks_uncertainties": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": True,
                                            },
                                        },
                                        "descriptive_text": {"type": "string"},
                                    },
                                    "additionalProperties": True,
                                },
                            },
                            "provenance": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                        },
                        "additionalProperties": True,
                    }
                },
                "required": ["base_case_extract"],
            },
        },
    },
]

TOOLS_RECOMMENDATIONS = [
    # -------------------------------------------------------------------------
    # 1. Recommendations extraction (with entity specifications)
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_recommendations",
            "description": "Extract recommendations for system redesign based on global objectives, including detailed specifications of relevant entities to extract",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "recommendation_id": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "description": "Category type (e.g., 'Equipment Upgrade', 'Process Optimization', 'Operational Change', 'Infrastructure', 'Material Change', 'Control System', 'Energy Efficiency', 'Maintenance Strategy', 'Safety Enhancement', 'Environmental Improvement')",
                                },
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "rationale": {"type": "string"},
                                "priority": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                },
                                "recommendation_category": {
                                    "type": "string",
                                    "enum": ["primary", "secondary", "other"],
                                    "description": "Classification of recommendation importance: 'primary' for high-impact direct solutions, 'secondary' for supporting changes, 'other' for alternative approaches",
                                },
                                "estimated_impact": {"type": "string"},
                                "implementation_complexity": {"type": "string"},
                                "estimated_cost_range": {
                                    "type": "string",
                                    "description": "Rough cost estimate range (e.g., 'Low: $10K-$50K', 'Medium: $50K-$200K', 'High: $200K-$500K', 'Very High: $500K+')",
                                },
                                "time_to_implement": {
                                    "type": "string",
                                    "description": "Estimated implementation timeline (e.g., '1-3 months', '3-6 months', '6-12 months', '12+ months')",
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of recommendation_ids that this recommendation depends on",
                                },
                                "alternative_to": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of recommendation_ids that this recommendation is an alternative to",
                                },
                            },
                            "required": [
                                "recommendation_id",
                                "type",
                                "title",
                                "description",
                                "priority",
                                "recommendation_category",
                            ],
                        },
                    },
                    "relevant_entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique identifier for the entity node",
                                },
                                "type": {
                                    "type": "string",
                                    "enum": _ont["NODE_TYPES"],
                                    "description": "Entity type from NODE_TYPES",
                                },
                                "properties": {
                                    "type": "object",
                                    "properties": dict(
                                        # Include all NODE_PROPERTIES
                                        {
                                            p: {"type": "string"}
                                            for p in _ont["NODE_PROPERTIES"]
                                        },
                                        **{
                                            # MSIO classification fields (required)
                                            "discipline": {
                                                "type": "string",
                                                "description": "MSIO Discipline name",
                                            },
                                            "category": {
                                                "type": "string",
                                                "description": "MSIO Category name",
                                            },
                                            "subcategory": {
                                                "type": "string",
                                                "description": "MSIO Subcategory name",
                                            },
                                            "entity": {
                                                "type": "string",
                                                "description": "MSIO Entity name",
                                            },
                                            # Additional fields for extraction guidance
                                            "expected_attributes": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "List of attribute names that should be extracted for this entity",
                                            },
                                            "evidence_locations": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Text snippets, page references, or section anchors where this entity is mentioned",
                                            },
                                            "extraction_rationale": {
                                                "type": "string",
                                                "description": "Explanation of why this entity is relevant to the recommendations",
                                            },
                                            "extraction_priority": {
                                                "type": "string",
                                                "enum": ["high", "medium", "low"],
                                                "description": "Priority level for extracting this entity",
                                            },
                                        },
                                    ),
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["id", "type", "properties"],
                        },
                    },
                },
                "required": ["recommendations", "relevant_entities"],
            },
        },
    },  # -------------------------------------------------------------------------
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
