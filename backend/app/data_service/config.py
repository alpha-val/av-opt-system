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
    "Costrule",
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

# EXAMPLES
NODE_PROP_EXAMPLES = {
    # Identity
    "name": "Jaw Crusher Installation",
    "short_description": "Primary crushing unit installation for processing plant",
    # Workspace
    "climate": "temperate",
    "electrical_spec": "480V / 60Hz / 3-phase",
    "floor_type": "reinforced_concrete",
    "has_drainage": True,
    "location": "Plant Site - Building A",
    "sq_ft": 1250,
    "zoning": "industrial",
    # Scenario
    "shelf_life_days": 365,
    "cold_chain_required": False,
    "sanitation_risk": "low",
    "sensitivity_factor": 0.25,
    "regulatory_zone": "Zone 3",
    # Process
    "capacity_unit": "TPH",
    "capacity_value": 500,
    "labor_required": 4,
    "batch_size": 50,
    "throughput": 480,
    # Equipment
    "annual_op_cost": 125000,
    "capacity": "500 TPH",
    "height": 4.5,
    "installation_year": 2022,
    "life_expectancy_years": 15,
    "model": "JC-500",
    "model_brand": "MineTech",
    "model_year": 2021,
    "power_rating": "250 kW",
    "requires_utilities": True,
    "supplier": "Global Mining Supply Co.",
    "weight": 3500,
    "width": 2.1,
    # Requirements
    "capital_requirement": 750000,
    "labor_requirement": 3,
    "permit_requirements": ["Environmental Clearance", "Construction Permit"],
    "power_requirement": "250 kW",
    "water_requirement": "50 m³/day",
    # Material
    "form": "crushed_rock",
    "hazard_class": "non-hazardous",
    "packaging_type": "bulk",
    "quantity": 5000,
    "recyclable": True,
    "shelf_life_days": 365,
    "source": "Local Quarry",
    "transportation_mode": "truck",
    "unit": "ton",
    # Logistics
    "transport_distance_km": 45,
    "transport_mode": "road",
    "handling_requirements": "standard",
    "logistics_risk": "low",
    # CostEstimate
    "cost_basis": "vendor_quote",
    "cost_type": "capital",
    "cost_value": 750000,
    "currency": "USD",
    "effective_life": 15,
    "source": "Internal Estimate",
    "update_frequency": "annual",
    # Environmental / Regulatory
    "carbon_tax_applicability": True,
    "compliance_level": "ISO 14001",
    "emissions_intensity": 0.12,
    "permitting_status": "approved",
    "reclamation_cost": 50000,
    "tailings_volume": 0,
    "waste_volume": 200,
    # Provenance
    "confidence": 0.9,
    "date_created": "2025-08-08",
    "created_by": "system_admin",
    "extracted_from": "technical_specifications.pdf",
    "extraction_method": "NLP_extraction_v2",
    "rationale": "Vendor supplied technical data",
    "review_status": "reviewed",
    "reviewer_name": "John Doe",
    "source_doc": "document_1kdl10",
}

EDGE_PROP_EXAMPLES = {
    "confidence": 0.92,  # extraction confidence score from 0 to 1
    "source_doc": "document_1kdl10",
    "extracted_from": "Section 3.2 - Process Description",
    "rationale": "Relation inferred from process inclusion statement in feasibility report",
    "date_created": "2025-08-08T10:15:00Z",  # ISO 8601 timestamp
    "extraction_method": "LLM_v2",  # could be LLM, regex, manual, etc.
}
