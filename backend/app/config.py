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
    "CostEstimate",
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
    "HAS_COST",  # * → CostEstimate
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
    "location",
    "climate",
    "zoning",
    "electrical_spec",
    "floor_type",
    "water_source",
    "has_drainage",
    "sq_ft",
    # Scenario
    "shelf_life_days",
    "cold_chain_required",
    "sanitation_risk",
    "sensitivity_factor",
    "regulatory_zone",
    # Process
    "capacity_unit",
    "capacity_value",
    "shift_pattern",
    "labor_required",
    "batch_size",
    "throughput_bottles_hr",
    # Equipment
    "model",
    "capacity",
    "power_rating",
    "requires_utilities",
    "annual_op_cost",
    "life_expectancy_years",
    "supplier",
    # Material
    "form",
    "unit",
    "quantity",
    "source",
    "shelf_life_days",
    "packaging_type",
    "recyclable",
    # CostEstimate
    "cost_value",
    "currency",
    "cost_type",
    "cost_basis",
    "effective_life",
    "source",
    # Provenance
    "confidence",  # score from LLM extraction
    "source_doc",  # name or path to the source document
    "extracted_from",  # text fragment or section
    "rationale",  # optional explanation (e.g., from chain-of-thought)
    "date_created",  # timestamp when relationship was extracted
    "extraction_method",  # "LLM", "regex", "manual", etc.
]

EDGE_PROPERTIES = [
    "confidence",  # score from LLM extraction
    "source_doc",  # name or path to the source document
    "extracted_from",  # text fragment or section
    "rationale",  # optional explanation (e.g., from chain-of-thought)
    "date_created",  # timestamp when relationship was extracted
    "extraction_method",  # "LLM", "regex", "manual", etc.
]
