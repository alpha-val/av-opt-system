"""Default ontology definitions."""

from typing import Dict, Any

# Core entity ontology
ENTITY_ONTOLOGY: Dict[str, Any] = {
    "schema_version": "0.1.0",
    "node_types": [
        # Physical substances and flows
        "Material",  # ore, reagents, bulk chemicals, fuels, water, consumables
        "Stream",  # material or energy flow with quantity over time or per tonne
        "WasteStream",  # streams that leave the system as waste or tailings
        # Energy
        "Energy",
        # Assets and infrastructure
        "Equipment",
        "Facility",
        "Location",
        # Processes
        "Process",  # flow sheet level / process definition
        "ProcessStep",  # single unit operation or step
        # Economic / decision layer
        "CostItem",
        "CostRule",
        "Scenario",
        "DecisionVariable",
        "Option",
        "Objective",
        "Constraint",
        "KPI",
        # Actors / context
        "Project",
        "Organization",
        "Labor",
        # Products and wastes
        "Product",
        "Waste",
        "Risk",
        # Governance / docs
        "Policy",
        "Assumption",
        "Limitation",
        "Document",
        "Chunk",
        "Table",
    ],
    "edge_types": [
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
        # Additional edge types
        "AFFECTS_COST",
        "AGGREGATES",
        "ALTERNATIVE_TO",
        "BASELINES",
        "BREAKS_DOWN_TO",
        "CONSTRAINS",
        "CONSUMES_STREAM",
        "CONTEMPORANEOUS_WITH",
        "CONTRACTED_TO",
        "DERIVED_FROM",
        "DRIVES",
        "ENABLES",
        "EXTRACTED_FROM",
        "FOLLOWS",
        "GOVERNED_BY",
        "HAS_COST",
        "HAS_FAILURE_MODE",
        "HAS_PART",
        "HAS_RISK",
        "HAS_STEP",
        "IMPACTS_KPI",
        "INCREASES_RISK",
        "INDEXED_BY",
        "MEASURED_BY",
        "MENTIONS",
        "MODIFIES",
        "OPERATED_BY",
        "OPTIMIZES_FOR",
        "OVERRIDES",
        "OWNED_BY",
        "PRODUCES_STREAM",
        "QUOTED_IN",
        "REDUCES_RISK",
        "REFERENCES",
        "REVISES",
        "SATISFIES",
        "SUPPLIED_BY",
        "TRIGGERS",
        "USES_MATERIAL",
        "VALIDATED_BY",
        "VERSION_OF",
    ],
    "node_properties": [
        # Identity
        "name",
        "id",
        "type",
        "short_description",
        "description",
        # Workspace
        "climate",
        "electrical_spec",
        "floor_type",
        "has_drainage",
        "location",
        "sq_ft",
        "zoning",
        # Recommendations
        "recommendations",
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
        "yield",
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
        "source",
        "transportation_mode",
        "unit",
        # Material / Stream
        "material_class",  # ore, process_reagent, bulk_chemical, fuel, water, etc.
        "phase",  # solid, liquid, gas, slurry, solution
        "composition",  # serialized composition/grade/purity (json string or dict)
        "density",
        "viscosity",
        "heating_value",  # for fuels
        "carbon_intensity",  # tCO2e per unit
        "unit_cost",
        "unit_cost_currency",
        "unit_cost_basis",  # per_tonne, per_m3, per_Nm3, per_kg, per_L, per_MWh
        "supplier_region",
        "stream_type",  # material or energy
        "basis",  # per_hour, per_day, per_year, per_tonne_ore, etc.
        "flow_rate",
        "flow_unit",  # "t/h", "Nm3/h", "kWh/t", etc.
        "solids_fraction",
        "temperature",
        "pressure",
        # Logistics
        "transport_distance_km",
        "transport_mode",
        "handling_requirements",
        "logistics_risk",
        # CostEstimate
        "cost",
        "cost_value",
        "cost_basis",
        "cost_type",
        "currency",
        "basis_year",
        "effective_life",
        "update_frequency",
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
        "created_at",
        "updated_at",
        "created_by",
        "extracted_from",
        "extraction_method",
        "rationale",
        "review_status",
        "reviewer_name",
        "source_doc",
        "source_page",
        "evidence_text",
    ],
    "edge_properties": [
        "source",
        "target",
        "type",
        "confidence",
        "source_doc",
        "extracted_from",
        "rationale",
        "date_created",
        "created_at",
        "updated_at",
        "extraction_method",
    ],
    "node_descriptions": {
        "Alternative": "Concrete alternative within an Option",
        "Assumption": "Explicit assumption supporting decisions",
        "Baseline": "Base configuration or assumptions",
        "Chunk": "Contiguous text span within a Document",
        "Constraint": "Technical, economic, or regulatory limit on variables, streams, or performance",
        "Consumable": "Consumable material",
        "CostDriver": "Driver of cost",
        "CostItem": "Atomic cost element (capex, opex, maintenance, etc.)",
        "CostRule": "Parametric relationship mapping drivers (capacity, throughput, material usage) to CostItem values",
        "DecisionVariable": "Formal variable that can be tuned in optimization or scenario analysis",
        "DecisionVariable": "Variable that can vary across scenarios",
        "Document": "Source document (report, manual, spec)",
        "EnergySource": "Source of energy",
        "Equipment": "Physical asset or equipment instance",
        "Facility": "Specific facility or plant location",
        "KPI": "Key performance indicator with formula",
        "Location": "Geospatial locality",
        "Material": "Physical substance or material",
        "Objective": "Quantitative objective (e.g., minimize cost, maximize NPV)",
        "Option": "Discrete design or operating choice that activates a configuration or rule set",
        "Organization": "Company, agency, or group",
        "Person": "Individual actor",
        "Process": "Process definition or flowsheet",
        "ProcessStep": "Atomic step of a Process",
        "Product": "Output product from a process",
        "Project": "Coherent endeavor with scope and timeline",
        "Reagent": "Chemical reagent used in process",
        "Risk": "Potential adverse event",
        "Scenario": "What-if overlay referencing a Baseline",
        "Table": "Structured table extracted from a Document",
        "WasteStream": "Waste or byproduct stream",
    },
    "edge_descriptions": {
        "CONSUMES_MATERIAL": "Process/equipment consumes a material",
        "FEEDS": "Entity feeds into another process/equipment",
        "HAS_EQUIPMENT": "Process or facility has equipment",
        "HAS_MATERIAL": "Process uses material",
        "HAS_SCENARIO": "Project has scenario",
        "INCLUDES_PROCESS": "Project or process includes sub-process",
        "LOCATED_IN": "Entity is located in a place",
        "NEXT": "Immediate successor in ordered set",
        "OUTPUTS": "Process outputs material or product",
        "PART_OF": "Child entity belongs to a parent",
        "POWERED_BY": "Equipment powered by energy source",
        "PRECEDES": "Event/step happens before another",
        "PRODUCES_MATERIAL": "Process produces a material",
        "RELATES_TO": "Generic relationship",
        "REQUIRES": "Entity requires another entity",
        "USES_EQUIPMENT": "Process uses equipment",
        "HAS_PART": "Entity contains child entities",
        "OPERATED_BY": "Asset/process operated by organization",
        "OWNED_BY": "Asset/project owned by organization",
        "AGGREGATES": "Summary aggregates details",
        "BREAKS_DOWN_TO": "Cost structure decomposes into components",
        "CONTRACTED_TO": "Contract links to counterparty",
        "GOVERNED_BY": "Entity governed by a reusable rule",
        "HAS_COST": "Entity has a cost item linked",
        "EXTRACTED_FROM": "Explicit lineage to source",
        "DERIVED_FROM": "Node derived from a source",
        "REFERENCES": "Cites another document or entity",
        "MENTIONS": "Text chunk mentions an entity",
        "BASELINES": "Scenario references its Baseline",
        "MODIFIES": "Option intends to change a target entity",
        "OPTIMIZES_FOR": "Scenario pursues an Objective",
        "CONSTRAINS": "Scenario imposes a Constraint",
        "SATISFIES": "Objective satisfied by KPI",
        "AFFECTS_COST": "Entity affects cost (positive or negative)",
        "IMPACTS_KPI": "Entity impacts KPI",
        "DRIVES": "CostDriver drives a CostItem or KPI",
    },
    "node_prop_examples": {
        "name": "Jaw Crusher Installation",
        "short_description": "Primary crushing unit installation",
        "capacity_unit": "TPH",
        "capacity_value": 500,
        "cost_value": 75000,
        "currency": "USD",
        "basis_year": 2020,
    },
    "edge_prop_examples": {
        "confidence": 0.92,
        "source_doc": "document_1kdl10",
        "extracted_from": "Section 3.2 - Process Description",
        "extraction_method": "LLM_v2",
    },
}

EXAMPLE_NODES_AND_EDGES = """
    --------------------------------------------------------------------------------
    OUTPUT (STRICT JSON SHAPE)
    --------------------------------------------------------------------------------
    - nodes: array of entities. Each node:
    {{
        "id": "uuid-or-stable",                 // Unique identifier for the node
        "type": "<EntityType>",                 // One of NODE_TYPES from the ontology
        "properties": {{
            "name": "string",                   // Human-readable name
            "created_at": "ISO-8601-timestamp", // e.g., "2024-01-01T12:00:00Z"
            "updated_at": "ISO-8601-timestamp", // e.g., "2024-01-01T12:00:00Z"
            "discipline": "string",             // Required; Discipline from the MSIO ontology
            "category": "string",               // Required; Category from the MSIO ontology
            "subcategory": "string",            // Required; Subcategory from the MSIO ontology
            "entity": "string",                // Required; Entity from the MSIO ontology
            "attribute_key": "attribute_value", // Example: "design_flowrate_value": 500
            "attribute_unit": "unit_value"      // Example: "design_flowrate_unit": "gpm"
            "attribute_key": "raw text value"   // Example: "Design flowrate": "500 gpm"
            "tableId": "t1",
            "rowIndex": 3,
            "colIndex": 5,
            "evidence_text": "short supporting snippet", // Evidence snippet
            "confidence": 0.0-1.0                       // Confidence score (0.0 to 1.0)
        }}
    }}
    - edges: array of relationships connecting the hierarchy:
    • Entity —PART_OF→ Subcategory
    • Subcategory —PART_OF→ Category
    • Category —PART_OF→ Discipline
    (Create nodes for Subcategory/Category/Discipline as needed if referenced.)
    Example edge:
    {{
        "id": "uuid-or-stable",
        "source": "<node_id_element>",
        "target": "<node_id_subcategory>",
        "type": "PART_OF",
        "properties": {{
            "created_at": "ISO-8601-timestamp",
            "updated_at": "ISO-8601-timestamp",
            "evidence_text": "short supporting snippet",s
            "confidence": 1.0
        }}
    }}
"""

# MSIO hierarchical ontology
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
                        {
                            "name": "Centrifugal",
                            "entity": "Base pump unit",
                            "attributes": [
                                "Design flowrate",
                                "Head",
                                "NPSH",
                                "Speed",
                                "Materials",
                                "Seal type",
                            ],
                            "notes": "Include datasheet, vendor, tag",
                        },
                        {
                            "name": "Positive Displacement",
                            "entity": "Gear",
                            "attributes": [
                                "Displacement",
                                "Max pressure",
                                "Viscosity limits",
                                "Materials",
                            ],
                        },
                        {
                            "name": "Positive Displacement",
                            "entity": "Diaphragm",
                            "attributes": [
                                "Displacement",
                                "Max pressure",
                                "Viscosity limits",
                                "Materials",
                            ],
                        },
                    ],
                },
                {
                    "name": "Vessels",
                    "subcategories": [
                        {
                            "name": "Pressure Vessel",
                            "entity": "Reactors",
                            "attributes": [
                                "Design pressure/temp",
                                "MAWP",
                                "Materials",
                                "Relief device",
                            ],
                        },
                        {
                            "name": "Pressure Vessel",
                            "entity": "Separators",
                            "attributes": [
                                "Design pressure/temp",
                                "MAWP",
                                "Materials",
                                "Relief device",
                            ],
                        },
                    ],
                },
                {
                    "name": "Tanks",
                    "subcategories": [
                        {
                            "name": "Storage Tank",
                            "entity": "Fixed Roof",
                            "attributes": [
                                "Capacity",
                                "Material",
                                "Coating",
                                "Bunding/containment",
                                "Height",
                                "Width",
                                "Aspect ratio",
                            ],
                        },
                        {
                            "name": "Storage Tank",
                            "entity": "Float Roof",
                            "attributes": [
                                "Capacity",
                                "Material",
                                "Coating",
                                "Bunding/containment",
                                "Height",
                                "Width",
                                "Aspect ratio",
                            ],
                        },
                    ],
                },
                {
                    "name": "Heat Exchangers",
                    "subcategories": [
                        {
                            "name": "Shell-and-tube",
                            "entity": "Shell-tube unit",
                            "attributes": [
                                "Heat duty",
                                "LMTD",
                                "Materials",
                                "Fouling factor",
                                "U-value",
                            ],
                        }
                    ],
                },
                {
                    "name": "Compressors/Blowers",
                    "subcategories": [
                        {
                            "name": "Centrifugal",
                            "entity": "Compressors",
                            "attributes": [
                                "Flow",
                                "Pressure ratio",
                                "Driver type",
                                "Lubrication",
                                "Interstage cooling",
                            ],
                        },
                        {
                            "name": "Turbo",
                            "entity": "Compressors",
                            "attributes": [
                                "Flow",
                                "Pressure ratio",
                                "Driver type",
                                "Lubrication",
                                "Interstage cooling",
                            ],
                        },
                    ],
                },
                {
                    "name": "Material Handling",
                    "subcategories": [
                        {
                            "name": "Conveyors/Hoists",
                            "entity": "Belt",
                            "attributes": [
                                "Capacity",
                                "Speed",
                                "Drive",
                                "Guards",
                                "Throughput",
                            ],
                        },
                        {
                            "name": "Conveyors/Hoists",
                            "entity": "Screw",
                            "attributes": [
                                "Capacity",
                                "Speed",
                                "Drive",
                                "Guards",
                                "Throughput",
                            ],
                        },
                    ],
                },
                {
                    "name": "Utilities",
                    "subcategories": [
                        {
                            "name": "Cooling Tower",
                            "entity": "Open",
                            "attributes": [
                                "Cooling duty",
                                "Cycles of concentration",
                                "Blowdown",
                            ],
                        },
                        {
                            "name": "Cooling Tower",
                            "entity": "Closed",
                            "attributes": [
                                "Cooling duty",
                                "Cycles of concentration",
                                "Blowdown",
                            ],
                        },
                    ],
                },
                {
                    "name": "Specialty",
                    "subcategories": [
                        {
                            "name": "Agitators",
                            "entity": "Top Entry",
                            "attributes": [
                                "Power",
                                "Tip speed",
                                "Seal type",
                                "Shaft material",
                            ],
                        },
                        {
                            "name": "Agitators",
                            "entity": "Side Entry",
                            "attributes": [
                                "Power",
                                "Tip speed",
                                "Seal type",
                                "Shaft material",
                            ],
                        },
                    ],
                },
                {
                    "name": "Process Equipment",
                    "subcategories": [
                        {
                            "name": "Grinding Mill",
                            "entity": "Ball",
                            "attributes": [
                                "Power",
                                "Throughput",
                                "Liner material",
                                "Grinding media",
                            ],
                        },
                        {
                            "name": "Grinding Mill",
                            "entity": "Rod",
                            "attributes": [
                                "Power",
                                "Throughput",
                                "Liner material",
                                "Grinding media",
                            ],
                        },
                        {
                            "name": "Grinding Mill",
                            "entity": "Mill",
                            "attributes": [
                                "Power",
                                "Throughput",
                                "Liner material",
                                "Grinding media",
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "Materials & Consumables",
            "categories": [
                {
                    "name": "Reagents",
                    "subcategories": [
                        {
                            "name": "Collectors",
                            "entity": "Reagent",
                            "attributes": [
                                "Dosage",
                                "Unit",
                                "pH window",
                                "Selectivity notes",
                            ],
                        },
                        {
                            "name": "Frothers",
                            "entity": "Reagent",
                            "attributes": [
                                "Dosage",
                                "Unit",
                                "pH window",
                                "Selectivity notes",
                            ],
                        },
                        {
                            "name": "Depressants",
                            "entity": "Reagent",
                            "attributes": [
                                "Dosage",
                                "Unit",
                                "pH window",
                                "Selectivity notes",
                            ],
                        },
                    ],
                },
                {
                    "name": "Bulk Chemicals",
                    "subcategories": [
                        {
                            "name": "Acids",
                            "entity": "Chemical",
                            "attributes": [
                                "Concentration",
                                "Material_class",
                                "Unit_cost",
                            ],
                        },
                        {
                            "name": "Bases",
                            "entity": "Chemical",
                            "attributes": [
                                "Concentration",
                                "Material_class",
                                "Unit_cost",
                            ],
                        },
                    ],
                },
                {
                    "name": "Fuels",
                    "subcategories": [
                        {
                            "name": "Diesel",
                            "entity": "Fuel",
                            "attributes": [
                                "Heating_value",
                                "Unit_cost",
                                "Carbon_intensity",
                            ],
                        },
                        {
                            "name": "Natural Gas",
                            "entity": "Fuel",
                            "attributes": [
                                "Heating_value",
                                "Unit_cost",
                                "Carbon_intensity",
                            ],
                        },
                    ],
                },
                {
                    "name": "Grinding Media",
                    "subcategories": [
                        {
                            "name": "Steel Balls",
                            "entity": "Media",
                            "attributes": [
                                "Size",
                                "Consumption_rate",
                                "Unit_cost",
                            ],
                        }
                    ],
                },
            ],
        },
        {
            "name": "Civil",
            "categories": [
                {
                    "name": "Site Works",
                    "subcategories": [
                        {
                            "name": "Grading",
                            "entity": "Cut/fill",
                            "attributes": [
                                "Finished grade",
                                "Slopes",
                                "Erosion control",
                                "Topsoil",
                            ],
                        }
                    ],
                },
                {
                    "name": "Access Roads/Paving",
                    "subcategories": [
                        {
                            "name": "Site roads",
                            "entity": "Pavement",
                            "attributes": [
                                "Pavement type",
                                "Width",
                                "Drainage",
                                "Loading",
                            ],
                        }
                    ],
                },
                {
                    "name": "Stormwater",
                    "subcategories": [
                        {
                            "name": "Retention Basins/Channels",
                            "entity": "Retention/Detention",
                            "attributes": [
                                "Detention volume",
                                "Outlet controls",
                                "SWPPP",
                            ],
                        }
                    ],
                },
                {
                    "name": "Utilities - Site",
                    "subcategories": [
                        {
                            "name": "Duct banks",
                            "entity": "Electrical ductbank",
                            "attributes": [
                                "Conduit size",
                                "Cover depth",
                                "Pull chambers",
                            ],
                        }
                    ],
                },
                {
                    "name": "Hydrology",
                    "subcategories": [
                        {
                            "name": "Culverts/Drainage",
                            "entity": "Culverts",
                            "attributes": [
                                "Size",
                                "Invert",
                                "Headwall",
                                "Scour protection",
                            ],
                        }
                    ],
                },
                {
                    "name": "Survey",
                    "subcategories": [
                        {
                            "name": "Topography",
                            "entity": "Benchmarking",
                            "attributes": [
                                "Datum",
                                "Coordinate system",
                                "Control points",
                            ],
                        }
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
                        {
                            "name": "Platforms/Walkways",
                            "entity": "Access platform",
                            "attributes": [
                                "Loading criteria",
                                "Handrails",
                                "Gratings",
                                "Access points",
                            ],
                        }
                    ],
                },
                {
                    "name": "Pipe Support",
                    "subcategories": [
                        {
                            "name": "Racks & Supports",
                            "entity": "Pipe rack",
                            "attributes": [
                                "Span",
                                "Load rating",
                                "Thermal movement allowances",
                            ],
                        }
                    ],
                },
                {
                    "name": "Buildings",
                    "subcategories": [
                        {
                            "name": "Enclosures",
                            "entity": "Control room",
                            "attributes": [
                                "Occupancy type",
                                "Fire rating",
                                "Service penetrations",
                            ],
                        },
                        {
                            "name": "Enclosures",
                            "entity": "MCC building",
                            "attributes": [
                                "Occupancy type",
                                "Fire rating",
                                "Service penetrations",
                            ],
                        },
                    ],
                },
                {
                    "name": "Foundations Interface",
                    "subcategories": [
                        {
                            "name": "Anchor/Embed Plates",
                            "entity": "Embed plate",
                            "attributes": [
                                "Plate size",
                                "Anchor bolt layout",
                                "Concrete strength",
                            ],
                        }
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
                        {
                            "name": "Footings",
                            "entity": "Spread footings",
                            "attributes": [
                                "Concrete class",
                                "Reinforcement",
                                "Bearing capacity",
                            ],
                        }
                    ],
                },
                {
                    "name": "Slabs",
                    "subcategories": [
                        {
                            "name": "Slab on grade",
                            "entity": "Equipment plinths",
                            "attributes": [
                                "Thickness",
                                "Joints",
                                "Surface finish",
                                "Load",
                            ],
                        }
                    ],
                },
                {
                    "name": "Retaining",
                    "subcategories": [
                        {
                            "name": "Retaining walls",
                            "entity": "Gravity",
                            "attributes": [
                                "Height",
                                "Surcharge",
                                "Drainage",
                                "Waterproofing",
                            ],
                        },
                        {
                            "name": "Retaining walls",
                            "entity": "Sheet pile",
                            "attributes": [
                                "Height",
                                "Surcharge",
                                "Drainage",
                                "Waterproofing",
                            ],
                        },
                    ],
                },
                {
                    "name": "Precast",
                    "subcategories": [
                        {
                            "name": "Manholes/Precast",
                            "entity": "Manhole chamber",
                            "attributes": ["Design load", "Gasket", "Access cover"],
                        }
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
                        {
                            "name": "Large Bore",
                            "entity": "Slurry",
                            "attributes": [
                                "Diameter",
                                "Schedule",
                                "Lining/lining material",
                                "Expansion allowances",
                            ],
                        },
                        {
                            "name": "Large Bore",
                            "entity": "Main headers",
                            "attributes": [
                                "Diameter",
                                "Schedule",
                                "Lining/lining material",
                                "Expansion allowances",
                            ],
                        },
                        {
                            "name": "Small Bore",
                            "entity": 'Instrument & Utility lines (<2")',
                            "attributes": [
                                "Material spec",
                                "Isolation valves",
                                "Tagging",
                                "Support spacing",
                            ],
                        },
                    ],
                },
                {
                    "name": "Materials",
                    "subcategories": [
                        {
                            "name": "Material selection",
                            "entity": "Carbon steel",
                            "attributes": [
                                "Specification (ASTM/ASME)",
                                "Corrosion allowance",
                                "Coating",
                            ],
                        },
                        {
                            "name": "Material selection",
                            "entity": "SS",
                            "attributes": [
                                "Specification (ASTM/ASME)",
                                "Corrosion allowance",
                                "Coating",
                            ],
                        },
                        {
                            "name": "Material selection",
                            "entity": "HDPE",
                            "attributes": [
                                "Specification (ASTM/ASME)",
                                "Corrosion allowance",
                                "Coating",
                            ],
                        },
                        {
                            "name": "Material selection",
                            "entity": "FRP",
                            "attributes": [
                                "Specification (ASTM/ASME)",
                                "Corrosion allowance",
                                "Coating",
                            ],
                        },
                    ],
                },
                {
                    "name": "Insulation",
                    "subcategories": [
                        {
                            "name": "Heat tracing",
                            "entity": "Insulation & HT",
                            "attributes": [
                                "Insulation type",
                                "Thickness",
                                "Heat tracing circuits",
                                "Control",
                            ],
                        }
                    ],
                },
                {
                    "name": "Testing",
                    "subcategories": [
                        {
                            "name": "Hydrotest & Pneumatic",
                            "entity": "Pressure testing",
                            "attributes": [
                                "Test pressure",
                                "Acceptance criteria",
                                "Duration",
                            ],
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
                        {
                            "name": "Flow meters",
                            "entity": "Coriolis",
                            "attributes": [
                                "Accuracy",
                                "Range",
                                "Mounting",
                                "Straight-run requirements",
                            ],
                        },
                        {
                            "name": "Flow meters",
                            "entity": "Ultrasonic",
                            "attributes": [
                                "Accuracy",
                                "Range",
                                "Mounting",
                                "Straight-run requirements",
                            ],
                        },
                    ],
                },
                {
                    "name": "Temperature & Pressure",
                    "subcategories": [
                        {
                            "name": "Transmitters",
                            "entity": "Temp & Pressure TX",
                            "attributes": [
                                "Range",
                                "Accuracy",
                                "Material",
                                "Isolation",
                            ],
                        }
                    ],
                },
                {
                    "name": "Analyzers & Safety",
                    "subcategories": [
                        {
                            "name": "Process analyzers",
                            "entity": "Gas detectors",
                            "attributes": [
                                "Calibration",
                                "Sample conditioning",
                                "Response time",
                            ],
                        },
                        {
                            "name": "Process analyzers",
                            "entity": "pH Analyzers",
                            "attributes": [
                                "Calibration",
                                "Sample conditioning",
                                "Response time",
                            ],
                        },
                    ],
                },
                {
                    "name": "Cabling & Termination",
                    "subcategories": [
                        {
                            "name": "Junction Boxes",
                            "entity": "Field junctions",
                            "attributes": [
                                "Cable types",
                                "Gland sizes",
                                "NEMA/Ingress rating",
                            ],
                        }
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
                        {
                            "name": "PLC / DCS / SCADA",
                            "entity": "Control platform",
                            "attributes": [
                                "I/O count",
                                "Redundancy",
                                "Vendor",
                                "Programming language",
                            ],
                        }
                    ],
                },
                {
                    "name": "Interfaces",
                    "subcategories": [
                        {
                            "name": "HMI / Historian",
                            "entity": "Operator stations",
                            "attributes": [
                                "Screens",
                                "Alarm philosophy",
                                "Trend requirements",
                            ],
                        }
                    ],
                },
                {
                    "name": "Network & Cyber",
                    "subcategories": [
                        {
                            "name": "Network switches / Firewalls",
                            "entity": "Industrial network",
                            "attributes": [
                                "Architecture",
                                "VLANs",
                                "Cybersecurity controls",
                            ],
                        }
                    ],
                },
                {
                    "name": "I/O",
                    "subcategories": [
                        {
                            "name": "Remote I/O panels",
                            "entity": "Field I/O",
                            "attributes": [
                                "Location",
                                "IP/analog",
                                "Termination",
                                "Power supply",
                            ],
                        }
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
                        {
                            "name": "Transformers",
                            "entity": "Step-down",
                            "attributes": ["kVA rating", "Cooling type", "Grounding"],
                        },
                        {
                            "name": "Transformers",
                            "entity": "Step-up",
                            "attributes": ["kVA rating", "Cooling type", "Grounding"],
                        },
                    ],
                },
                {
                    "name": "Switchgear",
                    "subcategories": [
                        {
                            "name": "MCC / SWGR",
                            "entity": "Motor control center",
                            "attributes": [
                                "AIC rating",
                                "Upstream protection",
                                "TB layouts",
                            ],
                        }
                    ],
                },
                {
                    "name": "Cabling",
                    "subcategories": [
                        {
                            "name": "Power & Control cable",
                            "entity": "Tray and routing",
                            "attributes": ["Tray fill", "Segregation", "Derating"],
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
                        {
                            "name": "Sprinkler / Hydrants",
                            "entity": "FP systems",
                            "attributes": [
                                "Design density",
                                "Hydrant spacing",
                                "Deluge zones",
                            ],
                        }
                    ],
                },
                {
                    "name": "Containment",
                    "subcategories": [
                        {
                            "name": "Spill bunding",
                            "entity": "Bunds",
                            "attributes": ["Capacity", "Drainage", "Liners"],
                        }
                    ],
                },
                {
                    "name": "Ventilation",
                    "subcategories": [
                        {
                            "name": "Fume / Dust extraction",
                            "entity": "Ducting & fans",
                            "attributes": ["Air changes", "Filtration", "Duct sizing"],
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
                        {
                            "name": "Air network",
                            "entity": "Compressors & Piping",
                            "attributes": ["Pressure", "Dewpoint", "Receiver sizing"],
                        }
                    ],
                },
                {
                    "name": "Cooling Water",
                    "subcategories": [
                        {
                            "name": "CW network",
                            "entity": "Pumps & Heat exchangers",
                            "attributes": [
                                "Flow",
                                "Temperature",
                                "Water treatment requirements",
                            ],
                        }
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
                        {
                            "name": "Inspections & Testing",
                            "entity": "Quality plan",
                            "attributes": [
                                "Hold points",
                                "Test records",
                                "Certificates",
                            ],
                        }
                    ],
                },
                {
                    "name": "Commissioning",
                    "subcategories": [
                        {
                            "name": "Pre-startup Safety Reviews",
                            "entity": "Commissioning plan",
                            "attributes": ["Loop checks", "SAT", "Punchlists"],
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
                    "subcategories": [
                        {"name": "Direct", "entity": "Direct"},
                        {"name": "Indirect", "entity": "Indirect"},
                    ],
                },
                {
                    "name": "Opex",
                    "subcategories": [{"name": "Operating Costs", "entity": "opex"}],
                },
                {
                    "name": "Contingency",
                    "subcategories": [{"name": "Contingency", "entity": "Contingency"}],
                },
            ],
        },
        {
            "name": "Miscellaneous",
            "categories": [
                {
                    "name": "Outside MSIO",
                    "subcategories": [
                        {"name": "Outside MSIO", "entity": "Outside MSIO"}
                    ],
                }
            ],
        },
    ],
}


def get_default_ontology() -> Dict[str, Any]:
    """Get default ontology structure."""
    return {
        "entity_ontology": ENTITY_ONTOLOGY,
        "msio_ontology": AV_MSIO_ONTOLOGY,
    }
