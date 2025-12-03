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
# Filter out "Recommendation" from NODE_TYPES for objective-driven extraction
# Recommendations must be embedded in entity properties, not created as separate nodes
_objective_driven_node_types = [
    nt
    for nt in _ont["NODE_TYPES"]
    if nt.lower() not in ["recommendation", "recommendations"]
]

# OpenAI function calling schemas for node/edge extraction
# ! ! ! KEEP BELOW FOR TABULAR DATA EXTRACTION ! ! !
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
                                "type": {
                                    "type": "string",
                                    "enum": _objective_driven_node_types,
                                    "description": "Entity type from NODE_TYPES.",
                                },
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        # Include all ontology node properties
                                        **{
                                            p: {"type": "string"}
                                            for p in _ont["NODE_PROPERTIES"]
                                        },
                                        "cost": {
                                            "type": "object",
                                            "description": "Cost information for the entity. Include when cost information is available. If not available, still create the entity but keep cost properties as null.",
                                            "properties": {
                                                "cost_value": {
                                                    "type": ["number", "null"],
                                                    "description": "Numeric cost value for the entity. Include when cost information is available.",
                                                },
                                                "cost_currency": {
                                                    "type": ["string", "null"],
                                                    "description": "Currency code for the cost (e.g., 'USD', 'EUR'). Use ISO currency codes. Include when cost information is available.",
                                                },
                                                "cost_min": {
                                                    "type": ["number", "null"],
                                                    "description": "Minimum cost value. Use for cost ranges (e.g., '$12 - $25'). Default to cost_value if not present.",
                                                },
                                                "cost_max": {
                                                    "type": ["number", "null"],
                                                    "description": "Maximum cost value. Use for cost ranges (e.g., '$12 - $25').",
                                                },
                                                "cost_unit": {
                                                    "type": ["string", "null"],
                                                    "description": "Unit of the cost value (e.g., 'yd³', 'LF', 'SY', 'EA', 'LS'). Include when mentioned in the text.",
                                                },
                                                "cost_basis": {
                                                    "type": ["string", "null"],
                                                    "description": "Basis of the cost value (e.g., 'installed', 'silt fence', 'liner & basin'). Include when mentioned in the text.",
                                                },
                                                "cost_basis_year": {
                                                    "type": ["number", "null"],
                                                    "description": "Basis year for the cost estimate (e.g., 2020, 2024). Include if mentioned in the text.",
                                                },
                                                "cost_type": {
                                                    "type": ["string", "null"],
                                                    "enum": [
                                                        "CAPEX",
                                                        "OPEX",
                                                        "Total",
                                                        "Other",
                                                        None,
                                                    ],
                                                    "description": "Type of cost: CAPEX (capital expenditure), OPEX (operating expenditure), Total, or Other. Include when cost information is available.",
                                                },
                                                "annual_op_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Annual operating cost if applicable. Include when mentioned in the text.",
                                                },
                                                "reclamation_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Reclamation cost if applicable. Include when mentioned in the text.",
                                                },
                                                "cost_alternates": {
                                                    "type": ["array", "null"],
                                                    "description": "Array of additional cost ranges when text contains 'or / OR'. Each entry should have cost_min, cost_max, and cost_unit. Example: [{\"cost_min\": 1000, \"cost_max\": 8000, \"cost_unit\": \"LS\"}]",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "cost_min": {
                                                                "type": ["number", "null"],
                                                                "description": "Minimum cost value for this alternate range.",
                                                            },
                                                            "cost_max": {
                                                                "type": ["number", "null"],
                                                                "description": "Maximum cost value for this alternate range.",
                                                            },
                                                            "cost_unit": {
                                                                "type": ["string", "null"],
                                                                "description": "Unit for this alternate range.",
                                                            },
                                                            "cost_basis": {
                                                                "type": ["string", "null"],
                                                                "description": "Basis for this alternate range if mentioned.",
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                            "required": [],
                                        },
                                        # Explicitly add attributes array for objective-driven extraction (MANDATORY)
                                        "attributes": {
                                            "type": "array",
                                            "description": "MANDATORY: Array of technical and operational attributes for this entity. This field is required and must be present for all entities. Extract all relevant attributes. NOTE: Cost information (cost_value, cost_currency, cost_basis_year, cost_type) should be stored as direct properties, NOT in the attributes array.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Attribute name",
                                                    },
                                                    "value": {
                                                        "type": [
                                                            "number",
                                                            "string",
                                                            "null",
                                                        ],
                                                        "description": "Attribute value (numeric or string)",
                                                    },
                                                    "unit": {
                                                        "type": ["string"],
                                                        "description": "Unit of measurement, specification, or requirement",
                                                    },
                                                    "evidence_text": {
                                                        "type": ["string", "null"],
                                                        "description": "Text snippet, page reference, or section anchor where this attribute value was found",
                                                    },
                                                    "confidence": {
                                                        "type": "number",
                                                        "minimum": 0.0,
                                                        "maximum": 1.0,
                                                        "description": "Confidence score for this attribute (0.0 to 1.0)",
                                                    },
                                                },
                                                "required": ["name", "value", "unit"],
                                            },
                                        },
                                    },
                                    "additionalProperties": False,
                                    "required": [
                                        "name",
                                        "attributes",
                                        "cost",
                                        "discipline",
                                        "category",
                                        "subcategory",
                                        "entity",
                                        "outside_msio",
                                    ],
                                },
                            },
                            "required": ["id", "type", "properties"],
                        },
                    }
                },
                "required": ["nodes"],
            },
        },
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "extract_nodes",
    #         "description": "Extract nodes (entities) from the text according to ontology.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "nodes": {
    #                     "type": "array",
    #                     "items": {
    #                         "type": "object",
    #                         "properties": {
    #                             "id": {"type": "string"},
    #                             "type": {"type": "string", "enum": _ont["NODE_TYPES"]},
    #                             "properties": {
    #                                 "type": "object",
    #                                 "properties": {
    #                                     p: {"type": "string"}
    #                                     for p in _ont["NODE_PROPERTIES"]
    #                                 },
    #                                 "additionalProperties": False,
    #                             },
    #                         },
    #                         "required": ["type"],
    #                     },
    #                 }
    #             },
    #             "required": ["nodes"],
    #         },
    #     },
    # },
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

TOOLS_OBJECTIVE_DRIVEN = [
    # -------------------------------------------------------------------------
    # 1. Node extraction
    # -------------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "extract_nodes",
            "description": "Extract nodes (entities) from the text according to ontology. IMPORTANT: Recommendations must be embedded within entity properties.recommendations array, NOT created as separate nodes with type='Recommendation'. Only extract entity nodes (Equipment and Material) and embed recommendations within their properties.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "id": {"type": "string"},
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "enum": _objective_driven_node_types,
                                    "description": "Entity type from NODE_TYPES. MUST NOT be 'Recommendation' - recommendations are embedded in properties.recommendations array, not as separate nodes.",
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
                                            "description": "Array of recommendations for achieving the global objective that relate to this entity. IMPORTANT: When cost information is available for a recommendation, include estimated_cost_value, estimated_cost_currency, cost_type, cost_basis_year, cost_impact_direction, and cost_impact_magnitude fields.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "description": "Unique identifier for the recommendation",
                                                    },
                                                    "type": {
                                                        "type": "string",
                                                        "description": "Type of recommendation (e.g., 'Equipment Upgrade', 'Process Optimization', 'Operational Change', etc.)",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name or title of the recommendation",
                                                    },
                                                    "rationale": {
                                                        "type": "string",
                                                        "description": "Explanation of why this recommendation is relevant to achieving the global objective. Include a detailed rationale for the recommendation.",
                                                    },
                                                    "relevance": {
                                                        "type": "string",
                                                        "enum": [
                                                            "primary",
                                                            "secondary",
                                                            "other",
                                                        ],
                                                        "description": "Relevance level: primary (direct high-impact) and secondary (supporting/enabling)",
                                                    },
                                                    "change_direction": {
                                                        "type": "string",
                                                        "enum": [
                                                            "increase",
                                                            "decrease",
                                                            "no change",
                                                        ],
                                                        "description": "Direction of change needed for this entity",
                                                    },
                                                    "change_unit": {
                                                        "type": "string",
                                                        "description": "Unit of measurement for the change (e.g., 'gpm', 'tons/hr', 'units/day')",
                                                    },
                                                    "change_magnitude": {
                                                        "type": "string",
                                                        "description": "Magnitude of change (numeric value as string)",
                                                    },
                                                    "change_magnitude_unit": {
                                                        "type": "string",
                                                        "description": "Unit for the change magnitude",
                                                    },
                                                    "change_magnitude_direction": {
                                                        "type": "string",
                                                        "enum": [
                                                            "increase",
                                                            "decrease",
                                                            "no change",
                                                        ],
                                                        "description": "Direction of the magnitude change",
                                                    },
                                                    "evidence_text": {
                                                        "type": "string",
                                                        "description": "Elaborate text (~200 words) supporting the recommendation",
                                                    },
                                                    "evidence_prov": {
                                                        "type": "string",
                                                        "description": "Providing the source of the evidence (e.g., 'Section 3.2.1', 'Figure 4', 'Table 2', 'Page 100', 'Appendix A', 'Reference 1', 'Reference 2', etc.)",
                                                    },
                                                    "confidence": {
                                                        "type": "number",
                                                        "minimum": 0.0,
                                                        "maximum": 1.0,
                                                        "description": "Confidence score for this recommendation (0.0 to 1.0)",
                                                    },
                                                },
                                                "required": [
                                                    "id",
                                                    "type",
                                                    "name",
                                                    "rationale",
                                                    "relevance",
                                                    "evidence_text",
                                                    "evidence_prov",
                                                ],
                                            },
                                        },
                                        "cost": {
                                            "type": "object",
                                            "description": "Cost information for the entity. Include when cost information is available.",
                                            "properties": {
                                                "cost_value": {
                                                    "type": ["number", "null"],
                                                    "description": "Numeric cost value for the entity. Include when cost information is available.",
                                                },
                                                "cost_currency": {
                                                    "type": ["string", "null"],
                                                    "description": "Currency code for the cost (e.g., 'USD', 'EUR'). Use ISO currency codes. Include when cost information is available.",
                                                },
                                                "cost_basis_year": {
                                                    "type": ["number", "null"],
                                                    "description": "Basis year for the cost estimate (e.g., 2020, 2024). Include if mentioned in the text.",
                                                },
                                                "cost_type": {
                                                    "type": ["string", "null"],
                                                    "enum": [
                                                        "CAPEX",
                                                        "OPEX",
                                                        "Total",
                                                        "Other",
                                                        None,
                                                    ],
                                                    "description": "Type of cost: CAPEX (capital expenditure), OPEX (operating expenditure), Total, or Other. Include when cost information is available.",
                                                },
                                                "annual_op_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Annual operating cost if applicable. Include when mentioned in the text.",
                                                },
                                                "reclamation_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Reclamation cost if applicable. Include when mentioned in the text.",
                                                },
                                                "annual_op_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Annual operating cost if applicable. Include when mentioned in the text.",
                                                },
                                                "reclamation_cost": {
                                                    "type": ["number", "null"],
                                                    "description": "Reclamation cost if applicable. Include when mentioned in the text.",
                                                },
                                                "cost_impact_direction": {
                                                    "type": ["string", "null"],
                                                    "description": "Direction of the cost impact: increase, decrease, or no change.",
                                                },
                                                "cost_impact_magnitude": {
                                                    "type": ["number", "null"],
                                                    "description": "Magnitude of the cost impact (numeric value as string). Include when cost information is available.",
                                                },
                                            },
                                            "required": [
                                                "cost_value",
                                                "cost_currency",
                                                "cost_basis_year",
                                                "cost_type",
                                            ],
                                        },
                                        # Explicitly add attributes array for objective-driven extraction (MANDATORY)
                                        "attributes": {
                                            "type": "array",
                                            "description": "MANDATORY: Array of technical and operational attributes for this entity. This field is required and must be present for all entities. Extract all relevant attributes. NOTE: Cost information (cost_value, cost_currency, cost_basis_year, cost_type) should be stored as direct properties, NOT in the attributes array.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Attribute name",
                                                    },
                                                    "value": {
                                                        "type": [
                                                            "number",
                                                            "string",
                                                            "null",
                                                        ],
                                                        "description": "Attribute value (numeric or string)",
                                                    },
                                                    "unit": {
                                                        "type": ["string", "null"],
                                                        "description": "Unit of measurement for the attribute (if applicable)",
                                                    },
                                                    "evidence_text": {
                                                        "type": ["string", "null"],
                                                        "description": "Text snippet, page reference, or section anchor where this attribute value was found",
                                                    },
                                                    "confidence": {
                                                        "type": "number",
                                                        "minimum": 0.0,
                                                        "maximum": 1.0,
                                                        "description": "Confidence score for this attribute (0.0 to 1.0)",
                                                    },
                                                },
                                                "required": ["name", "value", "unit", "evidence_text", "confidence"],
                                            },
                                        },
                                    },
                                    "additionalProperties": False,
                                    "required": ["name", "attributes", "cost", "recommendations", "discipline", "category", "subcategory", "entity", "outside_msio"],
                                },
                            },
                            "required": ["id", "type", "properties"],
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

_nullable_string = {"type": ["string", "null"]}
_nullable_number = {"type": ["number", "null"]}
_nullable_bool = {"type": ["boolean", "null"]}

_capacity_metric_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": _nullable_number,
        "unit": _nullable_string,
        "basis": _nullable_string,
    },
    "required": ["name"],
    "additionalProperties": False,
}

_operating_condition_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": _nullable_number,
        "unit": _nullable_string,
        "description": _nullable_string,
    },
    "required": ["name"],
    "additionalProperties": False,
}

_decision_lever_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"},
        "description": _nullable_string,
        "baseline_value": {"type": ["number", "string", "null"]},
        "baseline_unit": _nullable_string,
        "baseline_text": _nullable_string,
        "change_relevance_to_objective": _nullable_string,
        "is_discrete": {"type": ["boolean", "null"]},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "description": _nullable_string,
                },
                "required": ["label"],
                "additionalProperties": False,
            },
        },
        "plausible_range": {
            "type": ["object", "null"],
            "properties": {
                "min": _nullable_number,
                "max": _nullable_number,
                "unit": _nullable_string,
                "source_text": _nullable_string,
            },
            "additionalProperties": False,
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": _nullable_string,
                    "description": _nullable_string,
                },
                "additionalProperties": False,
            },
        },
    },
    "required": ["name", "category"],
    "additionalProperties": False,
}

_constraint_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "type": _nullable_string,
        "expression": _nullable_string,
        "operator": _nullable_string,
        "lhs_quantity": _nullable_string,
        "rhs_quantity_or_value": _nullable_string,
        "unit": _nullable_string,
        "source_text": _nullable_string,
    },
    "required": ["name"],
    "additionalProperties": False,
}

_component_lookup_schema = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        # "msio_discipline": {"type": "string"},
        # "msio_category": _nullable_string,
        # "msio_subcategory": _nullable_string,
        # "msio_entity": _nullable_string,
        "key_attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": _nullable_string,
                    "unit": _nullable_string,
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        "quantity": _nullable_number,
    },
    "required": ["role", "msio_discipline"],
    "additionalProperties": False,
}

_cost_item_schema = {
    "type": "object",
    "properties": {
        "role": _nullable_string,
        "description": _nullable_string,
        "cost_method": {
            "type": "string",
            "enum": [
                "vendor_table",
                "capacity_scaled",
                "weight_scaled",
                "fixed",
                "unit_cost_times_quantity",
                "other",
            ],
        },
        "scaling_basis": _nullable_string,
        "quantity": {"type": ["number", "null"]},
        "quantity_unit": _nullable_string,
        "quantity_source": _nullable_string,
        "unit_cost_reference": {
            "type": ["object", "null"],
            "properties": {
                "source_type": _nullable_string,
                "discipline_sheet": _nullable_string,
                "unit_cost_unit": _nullable_string,
                "range_position": _nullable_string,
            },
            "additionalProperties": False,
        },
        "pre_contingency_cost": _nullable_number,
        "notes": _nullable_string,
    },
    "required": ["cost_method"],
    "additionalProperties": False,
}

_cost_model_settings_schema = {
    "type": "object",
    "properties": {
        "primary_method": {
            "type": ["string", "null"],
            "enum": [
                "factored_top_down",
                "bottom_up_unit_cost",
                "hybrid",
                None,
            ],
        },
        "unit_cost_source_file": _nullable_string,
        "tank_cost_source_file": _nullable_string,
        "uses_standard_sizes": _nullable_bool,
        "standard_size_selection_rule": _nullable_string,
        "contingency_policy": {
            "type": ["object", "null"],
            "properties": {
                "percent": _nullable_number,
                "applies_to": _nullable_string,
                "source_text": _nullable_string,
            },
            "additionalProperties": False,
        },
        "scaling_factors": {
            "type": ["object", "null"],
            "properties": {
                "capacity_ratio": {
                    "type": ["object", "null"],
                    "properties": {
                        "enabled": _nullable_bool,
                        "base_capacity_value": _nullable_number,
                        "base_capacity_unit": _nullable_string,
                        "resized_capacity_value": _nullable_number,
                        "resized_capacity_unit": _nullable_string,
                        "ratio_value": _nullable_number,
                        "source_text": _nullable_string,
                    },
                    "additionalProperties": False,
                },
                "weight_ratio": {
                    "type": ["object", "null"],
                    "properties": {
                        "enabled": _nullable_bool,
                        "base_weight_value": _nullable_number,
                        "base_weight_unit": _nullable_string,
                        "resized_weight_value": _nullable_number,
                        "resized_weight_unit": _nullable_string,
                        "ratio_value": _nullable_number,
                        "source_text": _nullable_string,
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

_cost_breakdown_schema = {
    "type": "object",
    "properties": {
        "currency": _nullable_string,
        "basis_year": {"type": ["integer", "null"]},
        "items": {
            "type": "array",
            "items": _cost_item_schema,
        },
        "subtotal_pre_contingency": _nullable_number,
        "total_with_contingency": _nullable_number,
    },
    "additionalProperties": False,
}

_cost_reduction_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": _nullable_string,
        "changed_levers": {
            "type": "array",
            "items": {"type": "string"},
        },
        "cost_model_reference": _nullable_string,
        "estimated_pre_contingency_cost": _nullable_number,
        "estimated_total_cost": _nullable_number,
        "currency": _nullable_string,
        "basis_year": {"type": ["integer", "null"]},
    },
    "required": ["name"],
    "additionalProperties": False,
}

_scenario_output_schema = {
    "type": "object",
    "properties": {
        "baseline": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "object",
                    "properties": {
                        "name": _nullable_string,
                        "location": _nullable_string,
                        "design_status": _nullable_string,
                        "service_description": _nullable_string,
                    },
                    "additionalProperties": False,
                },
                "system_overview": {
                    "type": "object",
                    "properties": {
                        "primary_function": _nullable_string,
                        "primary_units_or_trains": _nullable_string,
                        "main_inputs_or_outputs": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "operating_mode": _nullable_string,
                        "interfaces_or_dependencies": _nullable_string,
                    },
                    "additionalProperties": True,
                },
                "performance_metrics": {
                    "type": "object",
                    "properties": {
                        "primary_metrics": {
                            "type": "array",
                            "items": _capacity_metric_schema,
                        },
                        "secondary_metrics": {
                            "type": "array",
                            "items": _capacity_metric_schema,
                        },
                    },
                    "additionalProperties": False,
                },
                "operating_conditions": {
                    "type": "array",
                    "items": _operating_condition_schema,
                },
                "physical_configuration": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "materials_and_construction": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "component": _nullable_string,
                            "material": _nullable_string,
                            "notes": _nullable_string,
                        },
                        "additionalProperties": False,
                    },
                },
                "structural_and_foundation": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "controls_and_automation": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "power_and_utilities": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "safety_access_and_maintenance": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "compliance_and_regulatory": {
                    "type": "object",
                    "properties": {
                        "codes_and_standards": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "regulatory_requirements": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "environmental_or_policy_limits": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "notes": _nullable_string,
                    },
                    "additionalProperties": True,
                },
                "schedule_and_execution": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "open_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": _nullable_string,
                            "impacted_area": _nullable_string,
                        },
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": True,
        },
        "objective": {
            "type": "object",
            "properties": {
                "objective_text": {"type": "string"},
                "objective_type": {"type": "string"},
                "target_metric_name": _nullable_string,
                "target_direction": _nullable_string,
                "target_delta_type": _nullable_string,
                "target_delta_value": {"type": ["number", "null"]},
                "target_unit": _nullable_string,
                "time_basis_or_scope": _nullable_string,
                "secondary_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["objective_text", "objective_type"],
            "additionalProperties": False,
        },
        "decision_levers": {
            "type": "array",
            "items": _decision_lever_schema,
        },
        # "constraints_and_rules": {
        #     "type": "array",
        #     "items": _constraint_schema,
        # },
        "components_for_tabular_lookup": {
            "type": "array",
            "items": _component_lookup_schema,
        },
        # "costs": {
        #     "type": "object",
        #     "properties": {
        #         "cost_model_settings": _cost_model_settings_schema,
        #         "baseline": _cost_breakdown_schema,
        #         "alternative_cost_models": {
        #             "type": "array",
        #             "items": {
        #                 "type": "object",
        #                 "properties": {
        #                     "name": {"type": "string"},
        #                     "cost_model_settings": _cost_model_settings_schema,
        #                     "items": {
        #                         "type": "array",
        #                         "items": _cost_item_schema,
        #                     },
        #                     "subtotal_pre_contingency": _nullable_number,
        #                     "total_with_contingency": _nullable_number,
        #                 },
        #                 "required": ["name"],
        #                 "additionalProperties": False,
        #             },
        #         },
        #         "cost_reduction_scenarios": {
        #             "type": "array",
        #             "items": _cost_reduction_schema,
        #         },
        #     },
        #     "additionalProperties": False,
        # },
        "meta": {
            "type": "object",
            "properties": {
                "notes": _nullable_string,
            },
            "additionalProperties": True,
        },
    },
    "required": [
        "baseline",
        "objective",
        "decision_levers",
        "constraints_and_rules",
        "components_for_tabular_lookup",
        "costs",
        "meta",
    ],
}

TOOLS_SCENARIO_ANALYSIS = [
    {
        "type": "function",
        "function": {
            "name": "submit_scenario_analysis",
            "description": "Submit the structured scenario analysis JSON that matches the SCENARIO_PROMPT contract (baseline reconstruction, objectives, decision levers, constraints, component lookup keys, and cost structures).",
            "parameters": _scenario_output_schema,
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
