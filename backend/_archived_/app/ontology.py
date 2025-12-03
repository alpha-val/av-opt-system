from __future__ import annotations
from typing import Dict, Any

# Built-in light ontology for nodes and relations
ENTITY_ONTOLOGY: Dict[str, Any] = {
    "SCHEMA_VERSION": "0.1.0",
    "NODE_TYPES": [
        "Equipment",
        "Material",
        "Process",
        "Scenario",
        "Project",
    ],
    "EDGE_TYPES": [
        "CONSUMES_MATERIAL",
        "FEEDS",
        "HAS_EQUIPMENT",
        "HAS_MATERIAL",
        "HAS_SCENARIO",
        "INCLUDES_PROCESS",
        "LOCATED_IN",
        "NEXT",
        "OUTPUTS",
        "PART_OF",
        "POWERED_BY",
        "PRECEDES",
        "PRODUCES_MATERIAL",
        "RELATES_TO",
        "REQUIRES",
        "USES_EQUIPMENT",
    ],
    "NODE_PROPERTIES": [
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
        "cost",
        "cost_basis",
        "cost_type",
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
    ],
    "EDGE_PROPERTIES": [
        "confidence",  # score from LLM extraction
        "source_doc",  # name or path to the source document
        "extracted_from",  # text fragment or section
        "rationale",  # optional explanation (e.g., from chain-of-thought)
        "date_created",  # timestamp when relationship was extracted
        "extraction_method",  # "LLM", "regex", "manual", etc.
    ],
    "NODE_PROP_EXAMPLES": {
        # Identity
        "name": "Jaw Crusher Installation",
        "short_description": "Primary crushing unit installation for processing plant",
        "ontology_path": "Project > Process > Equipment",
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
        "cost": "75000",
        "cost_basis": "vendor_quote",
        "cost_type": "capital",
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
    },
    "EDGE_PROP_EXAMPLES": {
        "confidence": 0.92,  # extraction confidence score from 0 to 1
        "source_doc": "document_1kdl10",
        "extracted_from": "Section 3.2 - Process Description",
        "rationale": "Relation inferred from process inclusion statement in feasibility report",
        "date_created": "2025-08-08T10:15:00Z",  # ISO 8601 timestamp
        "extraction_method": "LLM_v2",  # could be LLM, regex, manual, etc.
    },
}

# Systems ontology for mechanical equipment in mining / industrial settings
AV_MSIO_ONTOLOGY: Dict[str, Any] = {
    "ontology_name": "ALPHA-VAL-MINING-STRUCTURED-INDUSTRIAL-ONTOLOGY",
    "version": "0.1",
    "description": "Ontology for classifying industrial equipment, civil works, structural components, piping, instrumentation, control systems, electrical systems, safety/environmental systems, utilities, construction/commissioning activities, and cost elements in mining and heavy industry projects.",
    "disciplines": [
        {
            "name": "Mechanical Equipment",
            "categories": [
                {
                    "name": "Pumps",
                    "subcategories": [
                        {"name": "Centrifugal", "entities": ["Base pump unit"]},
                        {
                            "name": "Positive Displacement",
                            "entities": ["Gear", "Diaphragm"],
                        },
                    ],
                },
                {
                    "name": "Vessels",
                    "subcategories": [
                        {
                            "name": "Pressure Vessel",
                            "entities": ["Reactors", "Separators"],
                        }
                    ],
                },
                {
                    "name": "Tanks",
                    "subcategories": [
                        {"name": "Storage Tank", "entities": ["Fixed", "Float Roof"]}
                    ],
                },
                {
                    "name": "Heat Exchangers",
                    "subcategories": [
                        {"name": "Shell-and-tube", "entities": ["Shell-tube unit"]}
                    ],
                },
                {
                    "name": "Compressors/Blowers",
                    "subcategories": [
                        {"name": "Centrifugal/Turbo", "entities": ["Compressors"]}
                    ],
                },
                {
                    "name": "Material Handling",
                    "subcategories": [
                        {"name": "Conveyors/Hoists", "entities": ["Belt", "Screw"]}
                    ],
                },
                {
                    "name": "Utilities",
                    "subcategories": [
                        {"name": "Cooling Tower", "entities": ["Open", "Closed"]}
                    ],
                },
                {
                    "name": "Specialty",
                    "subcategories": [
                        {"name": "Agitators", "entities": ["Top", "Side Entry"]}
                    ],
                },
                {
                    "name": "Process Equipment",
                    "subcategories": [
                        {"name": "Grinding Mill", "entities": ["Ball", "Rod", "Mill"]}
                    ],
                },
            ],
        },
        {
            "name": "Civil",
            "categories": [
                {
                    "name": "Site Works",
                    "subcategories": [{"name": "Grading", "entities": ["Cut", "fill"]}],
                },
                {
                    "name": "Access",
                    "subcategories": [
                        {"name": "Roads/Paving", "entities": ["Site roads"]}
                    ],
                },
                {
                    "name": "Stormwater",
                    "subcategories": [
                        {"name": "Retention", "entities": ["Basins", "Channels"]}
                    ],
                },
                {
                    "name": "Utilities - Site",
                    "subcategories": [
                        {"name": "Duct banks", "entities": ["Electrical ductbank"]}
                    ],
                },
                {
                    "name": "Hydrology",
                    "subcategories": [
                        {"name": "Culverts/Drainage", "entities": ["Culverts"]}
                    ],
                },
                {
                    "name": "Survey",
                    "subcategories": [
                        {"name": "Topography", "entities": ["Benchmarking"]}
                    ],
                },
            ],
        },
        {
            "name": "Structural",
            "categories": [
                {
                    "name": "Steelwork",
                    "subcategories": [
                        {"name": "Platforms/Walkways", "entities": ["Access platform"]}
                    ],
                },
                {
                    "name": "Pipe Support",
                    "subcategories": [
                        {"name": "Racks & Supports", "entities": ["Pipe rack"]}
                    ],
                },
                {
                    "name": "Buildings",
                    "subcategories": [
                        {
                            "name": "Enclosures",
                            "entities": ["Control room", "MCC building"],
                        }
                    ],
                },
                {
                    "name": "Foundations Interface",
                    "subcategories": [
                        {"name": "Anchor/Embed Plates", "entities": ["Embed plate"]}
                    ],
                },
            ],
        },
        {
            "name": "Concrete",
            "categories": [
                {
                    "name": "Foundations",
                    "subcategories": [
                        {"name": "Footings", "entities": ["Spread footings"]}
                    ],
                },
                {
                    "name": "Slabs",
                    "subcategories": [
                        {"name": "Slab on grade", "entities": ["Equipment plinths"]}
                    ],
                },
                {
                    "name": "Retaining",
                    "subcategories": [
                        {
                            "name": "Retaining walls",
                            "entities": ["Gravity", "Sheet pile"],
                        }
                    ],
                },
                {
                    "name": "Precast",
                    "subcategories": [
                        {"name": "Manholes/Precast", "entities": ["Manhole chamber"]}
                    ],
                },
            ],
        },
        {
            "name": "Piping",
            "categories": [
                {
                    "name": "Process Lines",
                    "subcategories": [
                        {"name": "Large Bore", "entities": ["Slurry", "Main headers"]},
                        {
                            "name": "Small Bore",
                            "entities": ['Instrument & Utility lines (<2")'],
                        },
                    ],
                },
                {
                    "name": "Materials",
                    "subcategories": [
                        {
                            "name": "Carbon steel / SS / HDPE / FRP",
                            "entities": ["Material selection"],
                        }
                    ],
                },
                {
                    "name": "Insulation",
                    "subcategories": [
                        {"name": "Heat tracing", "entities": ["Insulation & HT"]}
                    ],
                },
                {
                    "name": "Testing",
                    "subcategories": [
                        {
                            "name": "Hydrotest & Pneumatic",
                            "entities": ["Pressure testing"],
                        }
                    ],
                },
            ],
        },
        {
            "name": "Instrumentation",
            "categories": [
                {
                    "name": "Flow / Level",
                    "subcategories": [
                        {"name": "Flow meters", "entities": ["Coriolis", "Ultrasonic"]}
                    ],
                },
                {
                    "name": "Temperature & Pressure",
                    "subcategories": [
                        {"name": "Transmitters", "entities": ["Temp & Pressure TX"]}
                    ],
                },
                {
                    "name": "Analyzers & Safety",
                    "subcategories": [
                        {"name": "Gas detectors, pH", "entities": ["Analyzers"]}
                    ],
                },
                {
                    "name": "Cabling & Termination",
                    "subcategories": [
                        {"name": "Junction Boxes", "entities": ["Field junctions"]}
                    ],
                },
            ],
        },
        {
            "name": "Control",
            "categories": [
                {
                    "name": "Control Systems",
                    "subcategories": [
                        {"name": "PLC / DCS / SCADA", "entities": ["Control platform"]}
                    ],
                },
                {
                    "name": "Interfaces",
                    "subcategories": [
                        {"name": "HMI / Historian", "entities": ["Operator stations"]}
                    ],
                },
                {
                    "name": "Network & Cyber",
                    "subcategories": [
                        {
                            "name": "Network switches / Firewalls",
                            "entities": ["Industrial network"],
                        }
                    ],
                },
                {
                    "name": "I/O",
                    "subcategories": [
                        {"name": "Remote I/O panels", "entities": ["Field I", "O"]}
                    ],
                },
            ],
        },
        {
            "name": "Electrical",
            "categories": [
                {
                    "name": "Distribution",
                    "subcategories": [
                        {"name": "Transformers", "entities": ["Step-down", "step-up"]}
                    ],
                },
                {
                    "name": "Switchgear",
                    "subcategories": [
                        {"name": "MCC / SWGR", "entities": ["Motor control center"]}
                    ],
                },
                {
                    "name": "Cabling",
                    "subcategories": [
                        {
                            "name": "Power & Control cable",
                            "entities": ["Tray and routing"],
                        }
                    ],
                },
            ],
        },
        {
            "name": "Safety/Environment",
            "categories": [
                {
                    "name": "Fire Protection",
                    "subcategories": [
                        {"name": "Sprinkler / Hydrants", "entities": ["FP systems"]}
                    ],
                },
                {
                    "name": "Containment",
                    "subcategories": [{"name": "Spill bunding", "entities": ["Bunds"]}],
                },
                {
                    "name": "Ventilation",
                    "subcategories": [
                        {
                            "name": "Fume / Dust extraction",
                            "entities": ["Ducting & fans"],
                        }
                    ],
                },
            ],
        },
        {
            "name": "Utilities",
            "categories": [
                {
                    "name": "Compressed Air",
                    "subcategories": [
                        {"name": "Air network", "entities": ["Compressors & Piping"]}
                    ],
                },
                {
                    "name": "Cooling Water",
                    "subcategories": [
                        {"name": "CW network", "entities": ["Pumps & Heat exchangers"]}
                    ],
                },
            ],
        },
        {
            "name": "Construction/Commissioning",
            "categories": [
                {
                    "name": "QA/QC",
                    "subcategories": [
                        {"name": "Inspections & Testing", "entities": ["Quality plan"]}
                    ],
                },
                {
                    "name": "Commissioning",
                    "subcategories": [
                        {
                            "name": "Pre-startup Safety Reviews",
                            "entities": ["Commissioning plan"],
                        }
                    ],
                },
            ],
        },
        {
            "name": "Cost",
            "categories": [
                {
                    "name": "Capex",
                    "subcategories": [{"name": "Direct/ Indirect", "entities": []}],
                },
                {"name": "Opex", "subcategories": []},
                {"name": "Contingency", "subcategories": []},
            ],
        },
    ],
}


def load_ontology() -> Dict[str, Any]:
    """
    If user provides a `user_ontology.py` in PYTHONPATH with `ONTOLOGY` dict,
    we import and merge; otherwise return DEFAULT_ONTOLOGY.
    """
    try:
        from user_ontology import ONTOLOGY as USER_ONTOLOGY  # type: ignore

        # Simple shallow merge (user overrides built-ins)
        merged = ENTITY_ONTOLOGY.copy()
        for k, v in USER_ONTOLOGY.items():
            merged[k] = v
        return merged
    except Exception:
        return ENTITY_ONTOLOGY
