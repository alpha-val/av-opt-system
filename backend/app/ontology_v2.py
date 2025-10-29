# alpha_val_ontology.py
from __future__ import annotations
from typing import Dict, Any, List

ONTOLOGY_V2: Dict[str, Any] = {
    "SCHEMA_VERSION": "0.2.0",
    "NAME": "Alpha-Val Ontology (Core + Mining & Process Extension)",
    "DESCRIPTION": (
        "Typed, self-documenting core ontology with domain extensions. "
        "Includes explicit table lineage (cell-level provenance) and unit "
        "normalization conventions to support robust base-case extraction."
    ),
    "LICENSE": "Alpha-Val 2025. All rights reserved.",
    # -----------------------------
    # Type System (formal property typing)
    # -----------------------------
    "SCALAR_TYPES": {
        "string": {"py": "str"},
        "text": {"py": "str"},
        "int": {"py": "int"},
        "float": {"py": "float"},
        "bool": {"py": "bool"},
        "iso_date": {"format": "YYYY-MM-DD"},
        "iso_datetime": {"format": "YYYY-MM-DDTHH:MM:SSZ"},
        "currency_code": {"enum": "ISO-4217"},
        "unit_code": {"note": "UCUM or SI; canonicalized via UNITS_NORMALIZATION"},
        "enum": {"note": "Use with enum_name in field spec"},
        "id": {"note": "stable unique identifier"},
        "url": {"note": "URI or URL"},
    },
    "COMPLEX_TYPES": {
        "Quantity": {
            "description": "Standard quantity with value and unit; may include basis.",
            "shape": {"value": "float", "unit": "unit_code", "basis": "string?"},
        },
        "Money": {
            "description": "Monetary amount with explicit currency year.",
            "shape": {
                "amount": "float",
                "currency": "currency_code",
                "currencyYear": "int",
                "basisRegion": "string?",
                "basisSource": "string?",
            },
        },
        "Provenance": {
            "description": "Extraction provenance bundle (text or table).",
            "shape": {
                "sourceDoc": "string",
                "sourcePage": "int?",
                "extractionMethod": "string",  # e.g., LLM, tabular
                "createdBy": "string",
                "createdAt": "iso_datetime?",
            },
        },
        "TableCellRef": {
            "description": "Precise table lineage for a property or node coming from a table.",
            "shape": {
                "tableId": "id",  # id of the Table node
                "rowIndex": "int?",  # 0-based (or as parsed)
                "colIndex": "int?",  # 0-based (or as parsed)
                "headerPath": "string?",  # e.g., 'Capacity > TPH' or ['Capacity','TPH']
                "originalText": "string?",  # exact cell content
            },
        },
        "Evidence": {
            "description": "Evidence snippets and links to raw attributes.",
            "shape": {
                "originalAttribute": "string?",  # e.g., "flow_rate:500 gals/hr"
                "contextSnippet": "string?",
                "tableRef": "TableCellRef?",
            },
        },
        "KeyValue": {
            "description": "Generic labeled value bag.",
            "shape": {"key": "string", "value": "string"},
        },
    },
    # -----------------------------
    # Core Vocab (minimal, generalizable)
    # -----------------------------
    "CORE": {
        "NODE_TYPES": [
            "Assumption",
            "Baseline",
            "Chunk",
            "Constraint",
            "Contract",
            "CostItem",
            "CostRule",
            "Currency",
            "Document",
            "EscalationIndex",
            "Equipment",
            "Event",
            "FailureMode",
            "Figure",
            "GenericAsset",
            "GenericProcess",
            "GenericProcessStep",
            "KPI",
            "Location",
            "Material",
            "Measurement",
            "Milestone",
            "Objective",
            "Option",
            "Organization",
            "Person",
            "Project",
            "Quote",
            "Requirement",
            "Risk",
            "Scenario",
            "Schedule",
            "Sensor",
            "Site",
            "Table",
            "WorkOrder",
            "DecisionVariable",  # Explicit variable that can vary across scenarios (e.g., throughput setpoint)
            "Lever",  # A tunable lever (e.g., vendor selection, layout, energy source)
            "Alternative",  # A concrete alternative within a lever (e.g., Vendor A vs Vendor B)
            "CostDriver",  # A driver of cost (power, reagents, labor, freight, maintenance)
            "Uncertainty",  # Distributional/epistemic uncertainty that affects outcomes
            "DataGap",  # Missing or low-confidence datum noted in report
            "Vendor",  # Supplier or counterparty organization
        ],
        "EDGE_TYPES": [
            # Structure & ownership
            "HAS_PART",
            "LOCATED_IN",
            "OPERATED_BY",
            "OWNED_BY",
            "PART_OF",
            # Process & temporal
            "CONTEMPORANEOUS_WITH",
            "FOLLOWS",
            "HAS_STEP",
            "NEXT",
            "PRECEDES",
            # Cost & economics
            "AGGREGATES",
            "BREAKS_DOWN_TO",
            "CONTRACTED_TO",
            "GOVERNED_BY",
            "HAS_COST",
            "INDEXED_BY",
            "QUOTED_IN",
            "SUPPLIED_BY",
            # Data lineage
            "DERIVED_FROM",
            "EXTRACTED_FROM",
            "MENTIONS",
            "REFERENCES",
            "REVISES",
            "VALIDATED_BY",
            "VERSION_OF",
            # Scenario semantics
            "BASELINES",
            "CONSTRAINS",
            "MODIFIES",
            "OPTIMIZES_FOR",
            "OVERRIDES",
            "SATISFIES",
            # Risk & reliability
            "HAS_FAILURE_MODE",
            "HAS_RISK",
            "MEASURED_BY",
            "TRIGGERS",
            "AFFECTS_COST",  # X AFFECTS_COST CostItem (positive or negative effect)
            "IMPACTS_KPI",  # X IMPACTS_KPI KPI (directional impact)
            "ALTERNATIVE_TO",  # Alternative ↔ Alternative (mutually exclusive peers)
            "ENABLES",  # Lever/Option ENABLES a capability or step
            "DRIVES",  # CostDriver DRIVES CostItem or KPI
            "REDUCES_RISK",  # X REDUCES_RISK Risk
            "INCREASES_RISK",  # X INCREASES_RISK Risk
        ],
        "DESCRIPTIONS": {
            "NODES": {
                "Assumption": "Explicit assumption supporting decisions.",
                "Baseline": "Declared base configuration/assumptions.",
                "Chunk": "Contiguous text span within a Document.",
                "Constraint": "Bound or requirement expression (e.g., powerKw <= 2000).",
                "Contract": "Commercial agreement.",
                "CostItem": "One-off observed/quoted cost attached to an entity.",
                "CostRule": "Reusable estimation method (factor, curve, regression).",
                "Currency": "Currency reference (ISO-4217).",
                "Document": "Source doc (report, manual, spec).",
                "Equipment": "Physical asset or equipment instance.",
                "EscalationIndex": "Index/series used to rebase monetary values.",
                "Event": "Temporal occurrence (maintenance, failure, approval).",
                "FailureMode": "Defined way an asset can fail.",
                "Figure": "Figure or image reference from a Document.",
                "GenericAsset": "Any asset (physical or logical) when domain class is unknown.",
                "GenericProcess": "Process definition (e.g., workflow or flowsheet).",
                "GenericProcessStep": "Atomic step of a GenericProcess.",
                "KPI": "Metric definition with formula and unit.",
                "Location": "Geospatial locality (country/region/city).",
                "Material": "Physical substance or material.",
                "Measurement": "Observed quantity at a time from a Sensor.",
                "Milestone": "Significant point with date(s).",
                "Objective": "Optimization goal (min/max a KPI).",
                "Option": "Change proposal applied over a Baseline/Scenario target.",
                "Organization": "Company, agency, or group.",
                "Person": "Individual actor (author, engineer, reviewer).",
                "Project": "Coherent endeavor with scope, budget, timeline.",
                "Quote": "Supplier quotation envelope for prices/terms.",
                "Requirement": "Functional/non-functional requirement text.",
                "Risk": "Potential adverse event, with probability and impact.",
                "Scenario": "What-if overlay referencing a Baseline.",
                "Schedule": "Plan of activities with temporal bounds.",
                "Sensor": "Source of measurements.",
                "Site": "Specific facility/plant/mine location; LOCATED_IN Location.",
                "Table": "Structured table extracted from a Document.",
                "WorkOrder": "Instruction to perform a maintenance or project task.",
            },
            "EDGES": {
                "AGGREGATES": "Summary row aggregates details (tables).",
                "BASELINES": "Scenario references its Baseline.",
                "BREAKS_DOWN_TO": "Cost structure decomposes into components.",
                "CONSTRAINS": "Scenario imposes a Constraint.",
                "CONTEMPORANEOUS_WITH": "Happens within the same time window.",
                "CONTRACTED_TO": "Contract links to counterparty.",
                "DERIVED_FROM": "Node derived or transformed from a source.",
                "EXTRACTED_FROM": "Explicit lineage to a Table/Chunk cell or passage.",
                "FOLLOWS": "Inverse of PRECEDES.",
                "GOVERNED_BY": "Entity governed by a reusable rule (CostRule).",
                "HAS_COST": "Entity has a cost item linked.",
                "HAS_FAILURE_MODE": "Asset associated with a FailureMode.",
                "HAS_PART": "Inverse of PART_OF.",
                "HAS_RISK": "Entity associated with a Risk.",
                "HAS_STEP": "Process contains this step.",
                "INDEXED_BY": "Monetary series or time-series linked to index/currency.",
                "LOCATED_IN": "Entity is located in a place/site.",
                "MEASURED_BY": "Entity measured by a Sensor/Measurement.",
                "MENTIONS": "Text chunk mentions an entity.",
                "MODIFIES": "Option intends to change a target entity.",
                "NEXT": "Immediate successor in an ordered set (e.g., next row).",
                "OPERATED_BY": "Asset/process operated by an organization/person.",
                "OPTIMIZES_FOR": "Scenario pursues an Objective.",
                "OVERRIDES": "Option overrides specific properties of a target.",
                "OWNED_BY": "Asset/project owned by organization/person.",
                "PART_OF": "Child entity belongs to a parent (step→process, asset→site).",
                "PRECEDES": "Event/step happens before another.",
                "QUOTED_IN": "CostItem is contained in a Quote.",
                "REFERENCES": "Cites another document or entity.",
                "REVISES": "Newer node revises an older node.",
                "SATISFIES": "Objective satisfied by KPI.",
                "SUPPLIED_BY": "Quote provided by Vendor/Organization.",
                "TRIGGERS": "Event triggers another event or work order.",
                "VALIDATED_BY": "Quality assurance reference.",
                "VERSION_OF": "Belongs to same logical identity across versions.",
            },
        },
    },
    # -----------------------------
    # Extension Modules
    # -----------------------------
    "EXTENSIONS": {
        "mining_process": {
            "description": "Mining & process industry specializations layered over Core.",
            "NODE_TYPES_ADD": [
                "Area",
                "Byproduct",
                "Chemical",
                "Consumable",
                "EnergySource",
                "Equipment",
                "EquipmentVariant",
                "Facility",
                "Manufacturer",
                "Material",
                "Ore",
                "Permit",
                "Process",
                "ProcessStep",
                "Product",
                "Reagent",
                "Regulator",
                "Utility",
                "Vendor",
                "WasteStream",
                "WaterSource",
            ],
            "EDGE_TYPES_ADD": [
                "CONSUMES",
                "COOLED_BY",
                "DISPOSES_TO",
                "FEEDS",
                "HEATED_BY",
                "MONITORED_BY",
                "PERMITTED_BY",
                "POWERED_BY",
                "PRODUCES",
                "RECYCLES",
                "REGULATED_BY",
                "REQUIRES",
                "USES_UTILITY",
            ],
            "DESCRIPTIONS_ADD": {
                "NODES": {
                    "Facility": "Plant or mine complex; PART_OF Project; LOCATED_IN Site.",
                    "Area": "Logical subdivision (crushing, grinding, flotation).",
                    "Process": "Flowsheet process (specialized GenericProcess).",
                    "ProcessStep": "Unit step in a flowsheet (crushing, milling, screening).",
                    "Equipment": "Equipment instance with hierarchical classification via properties: equipment_class='Equipment/Crusher/Gyratory', equipment_kind enum in {'Rotating','Fixed','Mobile','Electrical','Control'}.",
                    "EquipmentVariant": "Catalog/model family (size, power ranges).",
                    "Material": "Generic material; subclass via material_class (e.g., 'Ore','Reagent','Product').",
                    "Ore": "Material with grades (e.g., Au g/t, Cu %).",
                    "Product": "Material that is a target output of the process.",
                    "Byproduct": "Secondary material produced alongside the main product.",
                    "WasteStream": "Material stream disposed after processing; may include composition.",
                    "Consumable": "Material consumed in operations (non-product).",
                    "Reagent": "Material consumed during processing (chemical reagent).",
                    "Utility": "Power, water, air, steam services.",
                    "EnergySource": "Fuel or electricity supply source.",
                    "WaterSource": "Water intake source (well, river, municipal).",
                    "Chemical": "Chemical substance used as reagent/consumable.",
                    "Permit": "Formal approval from Regulator; PERMITTED_BY links.",
                    "Regulator": "Authority granting or enforcing permits.",
                    "Manufacturer": "Organization making Equipment/parts.",
                    "Vendor": "Supplier/quote issuer.",
                },
                "EDGES": {
                    "FEEDS": "Stream goes into a step or equipment.",
                    "PRODUCES": "Step/equipment produces a stream.",
                    "CONSUMES": "Entity consumes material or utility.",
                    "RECYCLES": "Stream is recycled to earlier stage.",
                    "DISPOSES_TO": "Waste stream disposal destination.",
                    "REQUIRES": "Requires a condition, material, or resource.",
                    "USES_UTILITY": "Consumes utility during operation.",
                    "POWERED_BY": "Powered by specific energy source.",
                    "COOLED_BY": "Cooled by utility/system.",
                    "HEATED_BY": "Heated by utility/system.",
                    "PERMITTED_BY": "Activity/entity is permitted by Permit.",
                    "REGULATED_BY": "Governed by regulator or regulation.",
                    "MONITORED_BY": "Measured or monitored by a Sensor.",
                },
            },
        }
    },
    # -----------------------------
    # Global (minimal) properties
    # -----------------------------
    "NODE_PROPERTIES": [
        # Identiy
        "name",
        "short_description",
        "tags",
        "status",
        "schema_version",
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
        "provenance",
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
        "confidence",
        "provenance",
        "valid_from",
        "valid_to",
    ],
    # -----------------------------
    # Enumerations
    # -----------------------------
    "ENUMS": {
        "status": ["draft", "active", "deprecated"],
        "equipment_kind": ["Rotating", "Fixed", "Mobile", "Electrical", "Control"],
        "lifecycle_state": [
            "concept",
            "pre-feasibility",
            "feasibility",
            "design",
            "construction",
            "commissioning",
            "operations",
            "closure",
        ],
        "estimate_class": [
            "AACE_Class_5",
            "AACE_Class_4",
            "AACE_Class_3",
            "AACE_Class_2",
            "AACE_Class_1",
        ],
        "risk_severity": ["low", "medium", "high", "critical"],
        "risk_probability": [
            "rare",
            "unlikely",
            "possible",
            "likely",
            "almost_certain",
        ],
        "objective_direction": ["minimize", "maximize", "target"],
        "unit_variant_kind": ["imperial", "metric"],
    },
    # -----------------------------
    # Templates (typed, scoped fields)
    # -----------------------------
    "TEMPLATES": {
        # ---- Core ----
        "Project": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "status": {"type": "enum", "enum_name": "status"},
            },
            "optional": {
                "owner": {"type": "string"},
                "operator": {"type": "string"},
                "siteRef": {"type": "id"},
                "lifecycleState": {"type": "enum", "enum_name": "lifecycle_state"},
                "tic": {"type": "Money"},
                "provenance": {"type": "Provenance"},
            },
        },
        "GenericAsset": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "attributes": {"type": "KeyValue"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "GenericProcess": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "GenericProcessStep": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "sequenceOrder": {"type": "int"},
                "duty": {"type": "text?"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Document": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "uri": {"type": "url"},
            },
            "optional": {
                "docType": {"type": "string"},
                "publicationDate": {"type": "iso_date"},
                "authors": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Table": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "parentDocId": {"type": "id"},
            },
            "optional": {
                "caption": {"type": "text"},
                "schemaHint": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "CostItem": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "price": {"type": "Money"},
            },
            "optional": {
                "costBasis": {"type": "string"},
                "estimateClass": {"type": "enum", "enum_name": "estimate_class"},
                "errorPlusPct": {"type": "float"},
                "errorMinusPct": {"type": "float"},
                "effectiveDate": {"type": "iso_date"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "CostRule": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "method": {"type": "text"},
            },
            "optional": {
                "applicability": {"type": "text"},
                "specVersion": {"type": "string"},
                "provenance": {"type": "Provenance"},
            },
        },
        "EscalationIndex": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "indexCode": {"type": "string"},
                "region": {"type": "string"},
            },
            "optional": {
                "baseYear": {"type": "int"},
                "seriesId": {"type": "string"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Scenario": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "description": {"type": "text"},
                "priority": {"type": "int"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Option": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "overlayPriority": {"type": "int"},
                "assumptions": {"type": "text"},
                "constraintsExpr": {"type": "text"},
                "expectedEffect": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Objective": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "direction": {"type": "enum", "enum_name": "objective_direction"},
            },
            "optional": {
                "targetValue": {"type": "float"},
                "targetUnit": {"type": "unit_code"},
                "weight": {"type": "float"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Constraint": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "expression": {"type": "string"},
            },
            "optional": {
                "severity": {"type": "string"},
                "rationale": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "KPI": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "formula": {"type": "text"},
            },
            "optional": {
                "unit": {"type": "unit_code"},
                "direction": {"type": "enum", "enum_name": "objective_direction"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Event": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "time": {"type": "TimeWindow"},
                "short_description": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "WorkOrder": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "issuedAt": {"type": "iso_datetime"},
                "status": {"type": "enum", "enum_name": "status"},
                "provenance": {"type": "Provenance"},
            },
        },
        "FailureMode": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "description": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Sensor": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "locationRef": {"type": "id"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Measurement": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "observed": {"type": "Quantity"},
            },
            "optional": {
                "observedAt": {"type": "iso_datetime"},
                "sensorRef": {"type": "id"},
                "provenance": {"type": "Provenance"},
            },
        },
        # ---- Mining & Process Extension ----
        "Facility": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "siteRef": {"type": "id"},
            },
            "optional": {
                "powerRequirement": {"type": "Quantity"},
                "waterRequirement": {"type": "Quantity"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Process": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "flowSheetId": {"type": "string"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "ProcessStep": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "sequenceOrder": {"type": "int"},
                "duty": {"type": "text"},
                "evidence": {"type": "Evidence"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Equipment": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                # classification (replaces flat types)
                "equipment_class": {
                    "type": "string"
                },  # e.g., "Equipment/Crusher/Gyratory"
                "equipment_kind": {"type": "enum", "enum_name": "equipment_kind"},
                "manufacturer": {"type": "string"},
                "model": {"type": "string"},
                # Preferred typed quantities
                "powerKw": {"type": "Quantity"},
                "throughput": {"type": "Quantity"},
                # Normalized attribute pairs for tables / free text with units
                "capacity_value": {"type": "float"},
                "capacity_unit": {"type": "unit_code"},
                "capacity_value_min": {"type": "float"},
                "capacity_value_max": {"type": "float"},
                "capacity_unit_imperial": {"type": "unit_code"},
                "capacity_unit_metric": {"type": "unit_code"},
                "capacity_adjustment": {"type": "string"},  # e.g., "-50%", "2x", "base"
                "dimensions": {"type": "text"},
                "mass": {"type": "Quantity"},
                "availabilityPct": {"type": "float"},
                # Evidence & lineage
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "EquipmentVariant": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "class_code": {"type": "string"},
            },
            "optional": {
                "sizeRange": {"type": "text"},
                "powerRange": {"type": "text"},
                "capacityRange": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Material": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "material_class": {"type": "string"},
                "grade": {"type": "Quantity"},
                "bulkDensity": {"type": "Quantity"},
                "moisture": {"type": "Quantity"},
                # Optional normalized fields if present in tables
                "price": {"type": "Money"},
                "price_value": {"type": "float"},
                "price_unit": {"type": "unit_code"},
                "composition": {"type": "KeyValue"},  # or list in practice
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "WasteStream": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "composition": {"type": "KeyValue"},
                "disposalMethod": {"type": "string"},
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Utility": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "utility_type": {"type": "string"},
                "supplyRate": {"type": "Quantity"},
                "flow_rate_value": {"type": "float"},
                "flow_rate_unit": {"type": "unit_code"},
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Permit": {
            "required": {
                "stable_id": {"type": "id"},
                "name": {"type": "string"},
                "issuingAuthority": {"type": "string"},
                "validFrom": {"type": "iso_date"},
            },
            "optional": {
                "validTo": {"type": "iso_date"},
                "permitNumber": {"type": "string"},
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Vendor": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "country": {"type": "string"},
                "contact": {"type": "text"},
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Manufacturer": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "country": {"type": "string"},
                "contact": {"type": "text"},
                "evidence": {"type": "Evidence"},
                "tableRef": {"type": "TableCellRef"},
                "provenance": {"type": "Provenance"},
            },
        },
        "DecisionVariable": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "domain": {"type": "string"},  # e.g., "continuous: [200, 2000] tph"
                "unit": {"type": "unit_code"},
                "defaultValue": {"type": "float"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Lever": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "category": {
                    "type": "string"
                },  # e.g., "Vendor", "Technology", "Layout", "EnergySource", "Maintenance"
                "description": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Alternative": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "leverRef": {"type": "id"},
                "assumptions": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
        "CostDriver": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "driverType": {
                    "type": "string"
                },  # e.g., "power", "reagents", "labor", "freight", "maintenance"
                "unit": {"type": "unit_code"},
                "provenance": {"type": "Provenance"},
            },
        },
        "Uncertainty": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "distribution": {
                    "type": "string"
                },  # e.g., "normal(mu, sigma)", "triangular(a,b,c)"
                "low": {"type": "float"},
                "high": {"type": "float"},
                "mode": {"type": "float"},
                "provenance": {"type": "Provenance"},
            },
        },
        "DataGap": {
            "required": {"stable_id": {"type": "id"}, "name": {"type": "string"}},
            "optional": {
                "missingField": {"type": "string"},
                "context": {"type": "text"},
                "provenance": {"type": "Provenance"},
            },
        },
    },
    # -----------------------------
    # Global Objectives Specification
    # -----------------------------
    "GLOBAL_OBJECTIVES_SPEC": {
        "description": "Declarative categories to summarize global objects from a base case report for optionality and cost-alternative analysis.",
        "categories": {
            "kpis": {
                "node_types": ["KPI"],
                "edges_in": ["SATISFIES", "OPTIMIZES_FOR"],  # where KPI is target
                "fields": ["name", "formula", "unit", "direction"],
            },
            "key_entities": {
                "node_types": ["Equipment", "Material", "Process", "Scenario", "GenericAsset", "GenericProcess"],
                "fields": ["name", "short_description"],
            },
            "constraints": {
                "node_types": ["Constraint"],
                "edges_in": ["CONSTRAINS"],
                "fields": ["name", "expression", "severity", "rationale"],
            },
            "cost": {
                "node_types": ["CostItem"],
                "edges_in": [
                    "HAS_COST",
                    "BREAKS_DOWN_TO",
                    "DERIVED_FROM",
                    "INDEXED_BY",
                ],
                "fields": [
                    "name",
                    "price",
                    "estimateClass",
                    "effectiveDate",
                    "costBasis",
                ],
            },
            "risk": {
                "node_types": ["Risk"],
                "edges_in": ["HAS_RISK", "REDUCES_RISK", "INCREASES_RISK"],
                "fields": ["name", "risk_severity", "risk_probability"],
            },
            "options": {
                "node_types": ["Lever"],
                "edges_out": ["ENABLES", "AFFECTS_COST", "IMPACTS_KPI"],
                "fields": ["name", "category", "description"],
            },
            "alternatives": {
                "node_types": ["Alternative"],
                "edges_out": ["ALTERNATIVE_TO", "AFFECTS_COST", "IMPACTS_KPI"],
                "fields": ["name", "leverRef", "assumptions"],
            },
            "decision_variables": {
                "node_types": ["DecisionVariable"],
                "fields": ["name", "domain", "unit", "defaultValue"],
            },
            "cost_drivers": {
                "node_types": ["CostDriver"],
                "edges_out": ["DRIVES", "AFFECTS_COST"],
                "fields": ["name", "driverType", "unit"],
            },
            "uncertainties": {
                "node_types": ["Uncertainty"],
                "fields": ["name", "distribution", "low", "mode", "high"],
            },
            "assumptions": {
                "node_types": ["Assumption"],
                "fields": ["name", "short_description"],
            },
            "schedule": {
                "node_types": ["Schedule", "Milestone", "Event"],
                "edges_out": ["PRECEDES", "FOLLOWS", "CONTEMPORANEOUS_WITH", "NEXT"],
                "fields": ["name", "time", "short_description"],
            },
            "permits": {
                "node_types": ["Permit"],
                "edges_in": ["PERMITTED_BY", "REGULATED_BY"],
                "fields": [
                    "name",
                    "issuingAuthority",
                    "validFrom",
                    "validTo",
                    "permitNumber",
                ],
            },
            "data_gaps": {
                "node_types": ["DataGap"],
                "fields": ["name", "missingField", "context"],
            },
        },
        # The required output shape the extractor must populate under meta.global_objectives
        "output_shape": {
            "kpis": [],
            "key_entities": [],
            "constraints": [],
            "cost": [],
            "risk": [],
            "options": [],
            "alternatives": [],
            "decision_variables": [],
            "cost_drivers": [],
            "uncertainties": [],
            "assumptions": [],
            "schedule": [],
            "permits": [],
            "data_gaps": [],
        },
    },
    # -----------------------------
    # Cost Model & Policies (unchanged spirit, typed)
    # -----------------------------
    "COST_MODEL": {
        "CostShape": {
            "fields": [
                "Money.amount",
                "Money.currency",
                "Money.currencyYear",
                "basisRegion?",
                "basisSource?",
                "estimate_class?",
                "errorPlusPct?",
                "errorMinusPct?",
                "effectiveDate?",
            ],
            "policy": "Keep source-year nominal; rebase via derived CostItem + :DERIVED_FROM with EscalationIndex.",
        },
        "BreakdownShape": {
            "example": {
                "capex": {
                    "direct": {
                        "equipment": 0.0,
                        "materials": 0.0,
                        "labor": 0.0,
                        "freight": 0.0,
                        "taxes": 0.0,
                    },
                    "indirect": {
                        "engineering": 0.0,
                        "constructionMgmt": 0.0,
                        "contingency": 0.0,
                    },
                },
                "opex": {
                    "power": 0.0,
                    "water": 0.0,
                    "reagents": 0.0,
                    "labor": 0.0,
                    "maintenance": 0.0,
                },
            }
        },
        "EscalationPolicy": {
            "fields": ["index_code", "from_year", "to_year", "factor"],
            "rule": "Create derived CostItem; never overwrite source.",
        },
        "CostRulePolicy": {
            "intent": "Use CostRule only for reusable methods; not for one-off prices.",
            "linking": "Link CostRule to governed targets via :GOVERNED_BY.",
            "versioning": "Use specVersion; new versions connect via :REVISES.",
        },
    },
    # -----------------------------
    # Units & Normalization (expanded)
    # -----------------------------
    "METRIC_NORMALIZATION": {
        "quantity_shape": {"value": "float", "unit": "unit_code", "basis": "string?"},
        "units_standard": "UCUM or SI; store raw and normalized fields",
        "power_unit": "kW",
        "throughput_unit_examples": ["tph", "t/d", "m3/h"],
        "price_unit_examples": ["USD/t", "USD/kg", "USD/MWh", "USD/kL"],
        "grade_unit_examples": ["%", "g/t", "ppm"],
        "policy": [
            "Preserve source units; add normalized SI (…Norm) when helpful.",
            "Always include currency and currencyYear for monetary values.",
            "Prefer power in kW and throughput in tph for normalized fields.",
        ],
    },
    # -----------------------------
    # Units Normalization (canonical map + aliases for tables & text)
    # -----------------------------
    "UNITS_NORMALIZATION": {
        "canonical_map": {
            "barrels per day": "bbl/day",
            "barrels/day": "bbl/day",
            "bbl/day": "bbl/day",
            "bpd": "bbl/day",
            "centimeters": "cm",
            "cm": "cm",
            "cubic feet": "ft3",
            "cubic feet per second": "ft3/s",
            "cubic feet/second": "ft3/s",
            "cubic meters per second": "m3/s",
            "cubic meters/second": "m3/s",
            "cubic meters per hour": "m3/hr",
            "cubic meters": "m3",
            "cubic meters/hour": "m3/hr",
            "feet": "ft",
            "feet per second": "ft/s",
            "ft": "ft",
            "ft/s": "ft/s",
            "gallons": "gals",
            "gal/hr": "gals/hr",
            "gallons per hour": "gals/hr",
            "gallons/hour": "gals/hr",
            "gallons/min": "gals/min",
            "gals": "gallons",
            "gals/min": "gals/min",
            "gph": "gals/hr",
            "gpm": "gals/min",
            "inches": "in",
            "in": "in",
            "kg/s": "kg/s",
            "kgph": "kg/hr",
            "kg/hr": "kg/hr",
            "kilograms per hour": "kg/hr",
            "kilograms": "kg",
            "kilograms/hour": "kg/hr",
            "kph": "kg/hr",
            "L/min": "L/min",
            "lb": "lbs",
            "lb/hr": "lb/hr",
            "lbs/hr": "lb/hr",
            "liters per minute": "L/min",
            "liters": "L",
            "liters/minute": "L/min",
            "Lpm": "L/min",
            "m3/hr": "m3/hr",
            "m3h": "m3/hr",
            "pounds per hour": "lb/hr",
            "pounds": "lbs",
            "pounds/hour": "lb/hr",
            "pph": "lb/hr",
            "tons per day": "tons/day",
            "tons/day": "tons/day",
            "tpd": "tons/day",
            "TPH": "tons/hr",
        },
        "attribute_conventions": {
            "numeric_suffix": "_value",
            "unit_suffix": "_unit",
            "min_suffix": "_value_min",
            "max_suffix": "_value_max",
            "unit_imperial_suffix": "_unit_imperial",
            "unit_metric_suffix": "_unit_metric",
        },
        "examples": {
            "flow_rate": {
                "value_field": "flow_rate_value",
                "unit_field": "flow_rate_unit",
            },
            "capacity": {
                "value_field": "capacity_value",
                "unit_field": "capacity_unit",
                "min_field": "capacity_value_min",
                "max_field": "capacity_value_max",
                "unit_imperial_field": "capacity_unit_imperial",
                "unit_metric_field": "capacity_unit_metric",
                "adjustment_field": "capacity_adjustment",
            },
        },
    },
    # -----------------------------
    # Table Model & Policy hooks (for validators)
    # -----------------------------
    "TABLE_MODEL": {
        "provenance_required_fields": ["tableId", "rowIndex", "colIndex"],
        "naming_rules": [
            "Prefer explicit, distinguishing names synthesized from key attributes.",
            "Within a table scope, names must be unique.",
        ],
        "edge_rules": {
            "use_NEXT_for_row_order": True,
            "use_AGGREGATES_for_totals": True,
            "always_add_EXTRACTED_FROM_to_Table_or_Chunk": True,
        },
    },
    # -----------------------------
    # Quality Gate (graph hygiene)
    # -----------------------------
    "QUALITY_GATE": {
        "edges_must_use_declared_types": True,
        "allow_singleton_nodes": True,
        "require_provenance_fields": ["sourceDoc", "extractionMethod", "createdBy"],
        "reject_if_missing_required_template_fields": True,
    },
    # -----------------------------
    # Synonyms & Extraction Hints
    # -----------------------------
    "SYNONYMS": {
        "Equipment": ["asset", "machine", "unit", "subsystem", "package", "skid"],
        "Material": [
            "consumable",
            "reagent",
            "chemical",
            "feed",
            "product",
            "ore",
            "concentrate",
        ],
        "Utility": ["service", "power", "electricity", "water", "air", "steam"],
        "CostItem": ["price", "cost", "quote", "budget", "estimate", "allowance"],
        "CostRule": [
            "factor",
            "scaling_law",
            "curve",
            "regression",
            "parametric",
            "index",
        ],
        "Permit": ["approval", "license", "authorization"],
        "Document": [
            "report",
            "NI43-101",
            "SK1300",
            "PEA",
            "FS",
            "DFS",
            "datasheet",
            "manual",
            "brochure",
        ],
        "Option": ["alternative", "variant", "case", "scenario option"],
        "Objective": ["goal", "target", "KPI target"],
        "Constraint": ["limit", "bound", "cap", "requirement"],
    },
    "EXTRACTION_HINTS": {
        "entity_patterns": [
            "Equipment: Manufacturer/Model/Size near kW, tph, dimensions; map to Equipment with equipment_class path.",
            "Material: Purity/grade + $/t or price → Material.price (Money).",
            "CostItem: Currency symbol + numeric + unit (USD/t, USD/kW, etc.) → attach via :HAS_COST.",
            "Utility: kWh, MWh, m3/h, L/s tokens near 'power','water','air' → Utility with supplyRate.",
            "Permit: Authority names, permit numbers, validity dates → Permit.",
        ],
        "table_column_aliases": {
            "throughput": ["capacity", "rate", "tph", "t/d"],
            "powerKw": ["power", "installed power", "motor kW", "kW"],
            "price": ["price", "cost", "$/t", "USD/t", "USD/kg"],
            "leadTimeDays": ["lead time", "delivery time", "weeks ARO"],
        },
    },
    # -----------------------------
    # Minimal graph patterns (validation aides)
    # -----------------------------
    "PATTERNS": {
        "EquipmentWithCost": {
            "nodes": ["Equipment", "CostItem", "Vendor?", "Quote?"],
            "edges": [
                ["Equipment", "HAS_COST", "CostItem"],
                ["CostItem", "QUOTED_IN", "Quote?", "optional"],
                ["Quote?", "SUPPLIED_BY", "Vendor?", "optional"],
            ],
        },
        "MaterialPriceSeries": {
            "nodes": ["Material", "Currency"],
            "edges": [["Material", "INDEXED_BY", "Currency"]],
        },
        "ScenarioOverlay": {
            "nodes": [
                "Baseline",
                "Scenario",
                "Option",
                "Objective",
                "Constraint?",
                "KPI",
            ],
            "edges": [
                ["Scenario", "BASELINES", "Baseline"],
                ["Scenario", "MODIFIES", "Option"],
                ["Option", "OVERRIDES", "Equipment|Process|CostItem"],
                ["Scenario", "OPTIMIZES_FOR", "Objective"],
                ["Objective", "SATISFIES", "KPI"],
                ["Scenario", "CONSTRAINS", "Constraint?", "optional"],
            ],
        },
        "TemporalChain": {
            "nodes": ["Event", "Event"],
            "edges": [["Event", "PRECEDES", "Event"]],
        },
        "TableAggregation": {
            "nodes": ["Table", "GenericAsset?", "CostItem?"],
            "edges": [
                ["GenericAsset?", "AGGREGATES", "GenericAsset?", "optional"],
                ["CostItem?", "AGGREGATES", "CostItem?", "optional"],
            ],
        },
    },
    # -----------------------------
    # Defaults and fallbacks
    # -----------------------------
    "DEFAULTS": {
        "currency": "USD",
        "currency_year": 2025,
        "estimate_class": "AACE_Class_4",
        "extraction_method": "LLM",
    },
    # Examples
    "EXAMPLES": {
        "ACCE": {
            "name": "Primary Crusher Installation",
            "price": {"amount": 3_200_000, "currency": "USD", "currencyYear": 2015},
            "estimateClass": "AACE_Class_4",
        }
    },
}


# Other references

# AACE Estimate Class Definitions
AACE_ESTIMATE_CLASS_DEFINITION = {
    "AACE_CLASS_REFERENCE": [
        {
            "class": "AACE_Class_5",
            "name": "Concept / Screening Estimate",
            "definition_level": "0–2% of full project definition",
            "purpose": "Concept screening, order-of-magnitude estimate, early feasibility.",
            "methods": [
                "Stochastic or parametric models",
                "Equipment-factored or capacity-factored estimating",
                "Analogous cost ratios or scaling exponents",
            ],
            "expected_accuracy": {
                "low": -50,
                "high": +100,
                "typical_range": "−20 % to −50 % / +30 % to +100 %",
            },
            "recommended_use": "Early screening of alternatives; establish feasibility and go/no-go decisions.",
            "confidence_level": 0.3,
            "notes": "Minimal scope definition; relies on high-level capacity and factor models. Often used for quick scenario comparisons.",
        },
        {
            "class": "AACE_Class_4",
            "name": "Feasibility / Study Estimate",
            "definition_level": "1–15% of full project definition",
            "purpose": "Feasibility study, preliminary technical-economic analysis.",
            "methods": [
                "Parametric models with limited design data",
                "Equipment factored or semi-detailed estimating",
                "Preliminary process and layout information",
            ],
            "expected_accuracy": {
                "low": -30,
                "high": +50,
                "typical_range": "−15 % to −30 % / +20 % to +50 %",
            },
            "recommended_use": "Screen viable process routes, develop project options for selection.",
            "confidence_level": 0.45,
            "notes": "Adds process flow and layout basis; sufficient for conceptual comparisons.",
        },
        {
            "class": "AACE_Class_3",
            "name": "Budget / Authorization Estimate",
            "definition_level": "10–40% of full project definition",
            "purpose": "Budget approval, funding requests, project authorization.",
            "methods": [
                "Semi-detailed estimating",
                "Unit-cost methods",
                "Partial quantity take-off",
            ],
            "expected_accuracy": {
                "low": -20,
                "high": +30,
                "typical_range": "−10 % to −20 % / +10 % to +30 %",
            },
            "recommended_use": "Establish budget baseline; support project sanction or authorization for expenditure (AFE).",
            "confidence_level": 0.7,
            "notes": "Used for control planning and comparative option analysis.",
        },
        {
            "class": "AACE_Class_2",
            "name": "Control / Definitive Estimate",
            "definition_level": "30–75% of full project definition",
            "purpose": "Control estimate, tender evaluation, project execution planning.",
            "methods": [
                "Detailed deterministic estimating",
                "Comprehensive quantity take-off",
                "Discipline-specific costing",
            ],
            "expected_accuracy": {
                "low": -15,
                "high": +20,
                "typical_range": "−5 % to −15 % / +5 % to +20 %",
            },
            "recommended_use": "Bid preparation, project control baseline, contractor negotiation.",
            "confidence_level": 0.85,
            "notes": "Used where design maturity allows deterministic estimating; forms basis of control budgets.",
        },
        {
            "class": "AACE_Class_1",
            "name": "Check / Bid / Definitive Estimate",
            "definition_level": "65–100% of full project definition",
            "purpose": "Final control, tender, or contract estimate.",
            "methods": [
                "Detailed deterministic estimating",
                "Full quantity take-off",
                "Vendor quotes and specific labor/material rates",
            ],
            "expected_accuracy": {
                "low": -10,
                "high": +15,
                "typical_range": "−3 % to −10 % / +3 % to +15 %",
            },
            "recommended_use": "Contract award, detailed cost control, and change management.",
            "confidence_level": 0.95,
            "notes": "Highest maturity and accuracy; based on nearly complete design. Suitable for binding bids or control budgets.",
        },
    ]
}
