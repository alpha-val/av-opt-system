from __future__ import annotations
import os
from typing import Dict, List

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "auth": (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
}
# --------------------------------------------------------------
#  config.py   –  Knowledge-graph ontology (v0.2.0)
# --------------------------------------------------------------

SCHEMA_VERSION = "0.1.0"

NODE_TYPES = [
    "Equipment",
    "Material",
    "Process",
    "Provenance",
    "Scenario",
    "Workspace",
    # "Cost",
]

EDGE_TYPES = [
    # hierarchy
    "HAS_SCENARIO",  # Workspace  → Scenario
    "INCLUDES_PROCESS",  # Scenario   → Process
    # process layout
    "USES_EQUIPMENT",  # Process    → Equipment
    "CONSUMES_MATERIAL",  # Process    → Material (input)
    "PRODUCES_MATERIAL",  # Process    → Material (output)
    # costing
    # "HAS_COST",  # * → CostEstimate
    # data‑cleaning
    "SIMILAR_TO",  # low‑confidence duplicate link
    # provenance
    "HAS_PROVENANCE",  # * → Provenance
]


NODE_PROPERTIES = [
    # Identiy
    "name",
    "short_description",
    # Workspace
    "climate",
    "electrical_spec",
    "floor_type",
    "has_drainage",
    "location",
    "sq_ft",
    "zoning",
    # Scenario
    "shelf_life_days",
    "cold_chain_required",
    "sanitation_risk",
    "sensitivity_factor",
    "regulatory_zone",
    # Process
    "capacity_unit",
    "capacity_value",
    "labor_required",
    "batch_size",
    "throughput",
    # Equipment
    "annual_op_cost",
    "capacity",
    "height",
    "installation_year",
    "life_expectancy_years",
    "model",
    "model_brand",
    "model_year",
    "power_rating",
    "requires_utilities",
    "supplier",
    "weight",
    "width",
    # Requirements
    "capital_requirement",
    "labor_requirement",
    "permit_requirements",
    "power_requirement",
    "water_requirement",
    # Material
    "form",
    "hazard_class",
    "packaging_type",
    "quantity",
    "recyclable",
    "shelf_life_days",
    "source",
    "transportation_mode",
    "unit",
    # Logistics
    "transport_distance_km",
    "transport_mode",
    "handling_requirements",
    "logistics_risk",
    # CostEstimate
    "cost_basis",
    "cost_type",
    "cost_value",
    "currency",
    "effective_life",
    "source",
    "update_frequency",  # monthly, quarterly, annual
    # Environmental / Regulatory
    "carbon_tax_applicability",
    "compliance_level",
    "emissions_intensity",
    "permitting_status",
    "reclamation_cost",
    "tailings_volume",
    "waste_volume",
    # Provenance
    "confidence",
    "date_created",
    "created_by",
    "extracted_from",
    "extraction_method",
    "rationale",
    "review_status",  # reviewed, pending, rejected
    "reviewer_name",
    "source_doc",
]

EDGE_PROPERTIES = [
    "confidence",  # score from LLM extraction
    "source_doc",  # name or path to the source document
    "extracted_from",  # text fragment or section
    "rationale",  # optional explanation (e.g., from chain-of-thought)
    "date_created",  # timestamp when relationship was extracted
    "extraction_method",  # "LLM", "regex", "manual", etc.
]
