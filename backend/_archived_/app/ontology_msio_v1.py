# mining_systems_inputs_ontology.py
from __future__ import annotations
from typing import Dict, Any, List

MSIO: Dict[str, Any] = {
    "SCHEMA_VERSION": "0.9.0",
    "NAME": "Mining Systems & Inputs Ontology (MSIO)",
    "DESCRIPTION": (
        "A prescriptive, hierarchical ontology specializing in extraction from "
        "base-case mining and processing reports. Organizes systems, subsystems, "
        "packages, equipment, bulks, and operating inputs to scaffold scenarios "
        "and options analysis. Designed to be used with Alpha-Val Ontology."
    ),
    # -------------------------------------------------------------------------
    # 0) MAPPINGS to Alpha-Val ontology (so extracted items align to graph schema)
    # -------------------------------------------------------------------------
    "MAPPINGS": {
        "System": {"node_type": "GenericAsset"},
        "Subsystem": {"node_type": "GenericAsset"},
        "Package": {"node_type": "GenericAsset"},
        "EquipmentItem": {"node_type": "Equipment"},  # use equipment_class path
        "BulkItem": {"node_type": "GenericAsset"},  # piping/electrical/structural/etc.
        "MaterialInput": {"node_type": "Material"},
        "UtilityInput": {"node_type": "Utility"},
        "LaborCategory": {"node_type": "GenericAsset"},
        "CostBasisItem": {"node_type": "CostItem"},
        "Vendor": {"node_type": "Vendor"},
        "Manufacturer": {"node_type": "Manufacturer"},
        "Document": {"node_type": "Document"},
    },
    "EDGE_MAP": {
        "PART_OF": "PART_OF",
        "FEEDS": "FEEDS",
        "PRODUCES": "PRODUCES",
        "CONSUMES": "CONSUMES",
        "USES_UTILITY": "USES_UTILITY",
        "HAS_COST": "HAS_COST",
        "SUPPLIED_BY": "SUPPLIED_BY",
        "MANUFACTURED_BY": "SUPPLIED_BY",  # or OWNED_BY/REFERENCES per your main graph conventions
        "LOCATED_IN": "LOCATED_IN",
    },
    # -------------------------------------------------------------------------
    # 1) TAXONOMY (hierarchical classification with path codes)
    # -------------------------------------------------------------------------
    "TAXONOMY": {
        # Top-level pillars you requested
        "Equipment": {
            "code": "EQUIP",
            "children": {
                "Mechanical": {
                    "code": "EQUIP/MECH",
                    "children": {
                        "Crushing": {
                            "code": "EQUIP/MECH/CRU",
                            "children": {
                                "PrimaryGyratory": "Equipment/Crusher/Gyratory",
                                "JawPrimary": "Equipment/Crusher/Jaw",
                                "ConeSecondary": "Equipment/Crusher/Cone",
                                "HPGR": "Equipment/Crusher/HPGR",
                            },
                        },
                        "Grinding": {
                            "code": "EQUIP/MECH/GRD",
                            "children": {
                                "SAGMill": "Equipment/Mill/SAG",
                                "BallMill": "Equipment/Mill/Ball",
                                "RodMill": "Equipment/Mill/Rod",
                                "Tower/Stirred": "Equipment/Mill/Stirred",
                            },
                        },
                        "Classification": {
                            "code": "EQUIP/MECH/CLS",
                            "children": {
                                "Screen": "Equipment/Classifier/Screen",
                                "CycloneCluster": "Equipment/Classifier/Cyclone",
                            },
                        },
                        "Flotation": {
                            "code": "EQUIP/MECH/FLO",
                            "children": {
                                "MechanicalCells": "Equipment/Flotation/Cell/Mechanical",
                                "ColumnCells": "Equipment/Flotation/Cell/Column",
                                "AirSystem": "Equipment/Flotation/Air",
                            },
                        },
                        "Thickening": {
                            "code": "EQUIP/MECH/THK",
                            "children": {
                                "HighRateThickener": "Equipment/Thickener/HighRate",
                                "HighDensityThickener": "Equipment/Thickener/HighDensity",
                                "PasteThickener": "Equipment/Thickener/Paste",
                            },
                        },
                        "Filtration": {
                            "code": "EQUIP/MECH/FIL",
                            "children": {
                                "PressureFilter": "Equipment/Filter/Pressure",
                                "VacuumBelt": "Equipment/Filter/VacuumBelt",
                                "DiscFilter": "Equipment/Filter/Disc",
                            },
                        },
                        "MaterialsHandling": {
                            "code": "EQUIP/MECH/MH",
                            "children": {
                                "ApronFeeder": "Equipment/Handling/ApronFeeder",
                                "VibratoryFeeder": "Equipment/Handling/VibratoryFeeder",
                                "Conveyor": "Equipment/Conveyor/Belt",
                                "StackerReclaimer": "Equipment/Handling/StackerReclaimer",
                                "BinsHoppers": "Equipment/Handling/BinHopper",
                            },
                        },
                        "Pumping": {
                            "code": "EQUIP/MECH/PMP",
                            "children": {
                                "Centrifugal": "Equipment/Pump/Centrifugal",
                                "PositiveDisplacement": "Equipment/Pump/PD",
                                "SlurryPumps": "Equipment/Pump/Slurry",
                            },
                        },
                        "Tanks/Vessels": {
                            "code": "EQUIP/MECH/TNK",
                            "children": {
                                "AgitatedTank": "Equipment/Tank/Agitated",
                                "StorageTank": "Equipment/Tank/Storage",
                                "ThickenerFeedWell": "Equipment/Tank/FeedWell",
                            },
                        },
                    },
                },
                "Electrical": {
                    "code": "EQUIP/ELEC",
                    "children": {
                        "Transformers": "Equipment/Electrical/Transformer",
                        "Switchgear/MV/LV": "Equipment/Electrical/Switchgear",
                        "MCCsVFDs": "Equipment/Electrical/MCC_VFD",
                        "UPS/Backup": "Equipment/Electrical/UPS",
                        "Substations": "Equipment/Electrical/Substation",
                        "Cables": "Equipment/Electrical/Cable",
                    },
                },
                "Piping": {
                    "code": "EQUIP/PIP",
                    "children": {
                        "SlurryPiping": "Equipment/Piping/Slurry",
                        "ProcessWaterPiping": "Equipment/Piping/Water",
                        "ReagentPiping": "Equipment/Piping/Reagent",
                        "CompressedAir": "Equipment/Piping/Air",
                        "FireWater": "Equipment/Piping/FireWater",
                    },
                },
                "Controls/Instrumentation": {
                    "code": "EQUIP/CTRL",
                    "children": {
                        "PLC/DCS": "Equipment/Control/PLC_DCS",
                        "FieldInstruments": "Equipment/Control/Instrument",
                        "SCADA/Historian": "Equipment/Control/SCADA",
                    },
                },
                "Civil/Structural/Architectural": {
                    "code": "EQUIP/CIV",
                    "children": {
                        "Concrete": "Equipment/Civil/Concrete",
                        "SteelStructures": "Equipment/Civil/Steel",
                        "Buildings": "Equipment/Civil/Building",
                    },
                },
            },
        },
        "CostBasis": {
            "code": "COST",
            "children": {
                "CAPEX": {
                    "code": "COST/CAPEX",
                    "children": {
                        "Direct": {
                            "EquipmentSupply": "COST/CAPEX/DIRECT/EquipSupply",
                            "FreightDuties": "COST/CAPEX/DIRECT/FreightDuties",
                            "PipingBulks": "COST/CAPEX/DIRECT/Piping",
                            "ElectricalBulks": "COST/CAPEX/DIRECT/Electrical",
                            "CivStructArch": "COST/CAPEX/DIRECT/Civil",
                            "Erection/Installation": "COST/CAPEX/DIRECT/Install",
                        },
                        "Indirect": {
                            "Engineering": "COST/CAPEX/INDIRECT/Engineering",
                            "ConstructionMgmt": "COST/CAPEX/INDIRECT/CM",
                            "TemporaryFacilities": "COST/CAPEX/INDIRECT/Temp",
                            "OwnerCosts": "COST/CAPEX/INDIRECT/Owner",
                            "Contingency": "COST/CAPEX/INDIRECT/Contingency",
                        },
                    },
                },
                "OPEX": {
                    "code": "COST/OPEX",
                    "children": {
                        "Power": "COST/OPEX/Power",
                        "ProcessWater": "COST/OPEX/Water",
                        "Reagents": "COST/OPEX/Reagents",
                        "Consumables": "COST/OPEX/Consumables",
                        "Labor": "COST/OPEX/Labor",
                        "Maintenance": "COST/OPEX/Maintenance",
                        "G&A": "COST/OPEX/GA",
                        "Tailings/Env": "COST/OPEX/Tailings",
                        "Permits/Royalties": "COST/OPEX/PermitsRoyalties",
                    },
                },
            },
        },
        "Inputs": {
            "code": "INPUT",
            "children": {
                "Materials": {
                    "Ore/Feed": "INPUT/MAT/Feed",
                    "Product/Concentrate": "INPUT/MAT/Product",
                    "Byproducts": "INPUT/MAT/Byproduct",
                    "GrindingMedia": "INPUT/MAT/Media",
                    "Liners/WearParts": "INPUT/MAT/Liners",
                    "Flocculant": "INPUT/MAT/Flocculant",
                    "Coagulant": "INPUT/MAT/Coagulant",
                    "Lime": "INPUT/MAT/Lime",
                    "Collectors/Frothers": "INPUT/MAT/FlotationReagents",
                    "pHModifiers": "INPUT/MAT/pHMod",
                    "FlotationAir": "INPUT/MAT/Air",
                },
                "Utilities": {
                    "Power": "INPUT/UTIL/Power",
                    "ProcessWater": "INPUT/UTIL/Water",
                    "FreshWater/Makeup": "INPUT/UTIL/FreshWater",
                    "CompressedAir": "INPUT/UTIL/Air",
                    "Fuel/Gas/Diesel": "INPUT/UTIL/Fuel",
                    "Steam/Heat": "INPUT/UTIL/Steam",
                },
                "Labor": {
                    "Operations": "INPUT/LAB/Operations",
                    "Maintenance": "INPUT/LAB/Maintenance",
                    "Technical/Process": "INPUT/LAB/Technical",
                    "Administration": "INPUT/LAB/Admin",
                },
            },
        },
    },
    # -------------------------------------------------------------------------
    # 2) ENTITY TEMPLATES (typed, prescriptive fields used during extraction)
    # -------------------------------------------------------------------------
    "TEMPLATES": {
        "System": {
            "required": {"id": "id", "name": "string"},
            "optional": {"description": "text", "areaCode": "string"},
        },
        "Subsystem": {
            "required": {"id": "id", "name": "string", "parentSystemId": "id"},
            "optional": {"description": "text"},
        },
        "Package": {
            "required": {"id": "id", "name": "string", "parentId": "id"},
            "optional": {
                "class_code": "string",  # taxonomy path like EQUIP/MECH/CRU
                "scope": "text",
            },
        },
        # Equipment item – use with taxonomy paths like "Equipment/Crusher/Gyratory"
        "EquipmentItem": {
            "required": {"id": "id", "name": "string"},
            "optional": {
                "equipment_class": "string",  # taxonomy path string
                "equipment_kind": "enum: Rotating|Fixed|Mobile|Electrical|Control",
                "manufacturer": "string",
                "model": "string",
                "duty": "text",
                "capacity_value": "float",
                "capacity_unit": "unit",
                "capacity_value_min": "float",
                "capacity_value_max": "float",
                "powerKw": "float",  # normalized preferred
                "powerKwRaw": "string",  # as-seen
                "throughput_value": "float",
                "throughput_unit": "unit",
                "dimensions": "text",
                "mass_kg": "float",
                "availabilityPct": "float",
                "location": "string",
                "tableRef": "TableCellRef?",
                "notes": "text",
            },
        },
        # Bulk item templates (piping/electrical/etc.)
        "BulkItem": {
            "required": {
                "id": "id",
                "name": "string",
                "bulk_type": "enum: Piping|Electrical|Civil|Structural|Instrumentation",
            },
            "optional": {
                # Piping specifics
                "pipe_material": "string",
                "pipe_size_NPS": "float",
                "schedule": "string",
                "pressure_class": "string",
                "length_m": "float",
                "corrosion_allow_mm": "float",
                # Electrical specifics
                "voltage_kV": "float",
                "feeder_type": "string",
                "cable_size_mm2": "float",
                "transformer_MVA": "float",
                "fault_level_kA": "float",
                # Instrumentation/controls
                "plc_count": "int",
                "instrument_points": "int",
                # Civil/structural
                "concrete_m3": "float",
                "steel_tonnes": "float",
                "location": "string",
                "notes": "text",
            },
        },
        "MaterialInput": {
            "required": {"id": "id", "name": "string"},
            "optional": {
                "material_class": "string",  # Ore, Product, Reagent, Consumable
                "grade_value": "float",
                "grade_unit": "unit",
                "bulk_density": "float",
                "bulk_density_unit": "unit",
                "moisture_pct": "float",
                "price_amount": "float",
                "price_currency": "string",
                "price_year": "int",
                "consumption_value": "float",
                "consumption_unit": "unit",  # e.g., g/t, kg/t, L/t
                "tableRef": "TableCellRef?",
                "notes": "text",
            },
        },
        "UtilityInput": {
            "required": {"id": "id", "name": "string"},
            "optional": {
                "utility_type": "enum: Power|Water|Air|Fuel|Steam",
                "rate_value": "float",
                "rate_unit": "unit",  # kWh/t, m3/h, L/s
                "cost_per_unit": "float",
                "currency": "string",
                "currencyYear": "int",
                "peak_demand_kW": "float",
                "voltage_kV": "float",
                "tableRef": "TableCellRef?",
                "notes": "text",
            },
        },
        "LaborCategory": {
            "required": {"id": "id", "name": "string"},
            "optional": {
                "headcount_FTE": "float",
                "shift_pattern": "string",
                "hourly_rate": "float",
                "currency": "string",
                "currencyYear": "int",
                "tableRef": "TableCellRef?",
                "notes": "text",
            },
        },
        "CostBasisItem": {
            "required": {
                "id": "id",
                "name": "string",
                "basis_code": "string",
            },  # e.g., COST/CAPEX/DIRECT/EquipSupply
            "optional": {
                "price_amount": "float",
                "currency": "string",
                "currencyYear": "int",
                "estimate_class": "enum: AACE_Class_5|AACE_Class_4|AACE_Class_3|AACE_Class_2|AACE_Class_1",
                "errorPlusPct": "float",
                "errorMinusPct": "float",
                "effectiveDate": "date",
                "costBasis": "string",  # FOB/EXW/Installed etc.
                "tableRef": "TableCellRef?",
                "notes": "text",
            },
        },
    },
    # -------------------------------------------------------------------------
    # 3) REQUIRED RELATIONS during extraction (authoring scaffolds)
    # -------------------------------------------------------------------------
    "PATTERNS": {
        "SystemBreakdown": {
            "nodes": ["System", "Subsystem", "Package"],
            "edges": [
                ["Subsystem", "PART_OF", "System"],
                ["Package", "PART_OF", "Subsystem"],
            ],
        },
        "PackageEquipment": {
            "nodes": ["Package", "EquipmentItem"],
            "edges": [["EquipmentItem", "PART_OF", "Package"]],
        },
        "EquipmentBulks": {
            "nodes": ["EquipmentItem", "BulkItem"],
            "edges": [["BulkItem", "PART_OF", "EquipmentItem"]],
        },
        "InputsToProcess": {
            "nodes": ["MaterialInput", "UtilityInput", "EquipmentItem"],
            "edges": [
                ["MaterialInput", "CONSUMES", "EquipmentItem"],
                ["EquipmentItem", "USES_UTILITY", "UtilityInput"],
            ],
        },
        "CostAttachment": {
            "nodes": ["CostBasisItem", "EquipmentItem|BulkItem|Package"],
            "edges": [["EquipmentItem|BulkItem|Package", "HAS_COST", "CostBasisItem"]],
        },
    },
    # -------------------------------------------------------------------------
    # 4) COST BASIS (prescriptive tags to classify costs consistently)
    # -------------------------------------------------------------------------
    "COST_BASIS_TAGS": {
        "capex_direct": [
            "EquipSupply",
            "FreightDuties",
            "Piping",
            "Electrical",
            "Civil",
            "Install",
        ],
        "capex_indirect": ["Engineering", "CM", "Temp", "Owner", "Contingency"],
        "opex": [
            "Power",
            "Water",
            "Reagents",
            "Consumables",
            "Labor",
            "Maintenance",
            "GA",
            "Tailings",
            "PermitsRoyalties",
        ],
    },
    "COST_RULES": [
        "If a price is clearly equipment supply only → basis_code=COST/CAPEX/DIRECT/EquipSupply.",
        "If text says 'installed' or includes erection labor → basis_code=COST/CAPEX/DIRECT/Install.",
        "If commodity tariffs or kWh price → basis_code=COST/OPEX/Power and cost_per_unit attached to UtilityInput.",
        "If reagent consumption (kg/t) × reagent price → create CostBasisItem (OPEX/Reagents).",
        "Use estimate_class mapped from AACE reference when accuracy or definition level stated.",
    ],
    # -------------------------------------------------------------------------
    # 5) NORMALIZATION (units & attributes — minimal, strict)
    # -------------------------------------------------------------------------
    "NORMALIZATION": {
        "preferred": {
            "power": "kW",
            "throughput": "tph",
            "flow_liquid": "m3/h",
            "pressure": "kPa",
            "density": "t/m3",
            "energy": "kWh/t",
            "price_currency": "ISO-4217",
        },
        "attribute_pairs": {
            "capacity": {
                "value": "capacity_value",
                "unit": "capacity_unit",
                "min": "capacity_value_min",
                "max": "capacity_value_max",
            },
            "throughput": {"value": "throughput_value", "unit": "throughput_unit"},
            "rate": {"value": "rate_value", "unit": "rate_unit"},
            "price": {
                "amount": "price_amount",
                "currency": "currency",
                "year": "currencyYear",
            },
        },
        "table_provenance_fields": [
            "tableId",
            "rowIndex",
            "colIndex",
            "headerPath",
            "originalText",
        ],
    },
    # -------------------------------------------------------------------------
    # 6) EXTRACTION HINTS (targeted cues for base-case documents)
    # -------------------------------------------------------------------------
    "HINTS": {
        "synonyms": {
            "EquipmentItem": [
                "machine",
                "unit",
                "package equipment",
                "major equipment",
            ],
            "BulkItem": [
                "bulks",
                "piping",
                "electrical",
                "cables",
                "conduit",
                "steelwork",
                "concrete",
                "C&S",
                "CSA",
            ],
            "MaterialInput": ["reagent", "consumable", "chemical", "media", "liner"],
            "UtilityInput": [
                "utility",
                "power",
                "electricity",
                "water",
                "compressed air",
                "steam",
                "fuel",
                "diesel",
                "gas",
            ],
            "CostBasisItem": [
                "cost",
                "price",
                "estimate",
                "budget",
                "allowance",
                "quote",
                "quotation",
            ],
            "Package": ["area", "battery limits", "scope package", "lot"],
            "Subsystem": ["section", "area", "island"],
        },
        "table_aliases": {
            "powerKw": ["power", "installed power", "motor kW", "drive power", "kW"],
            "throughput_value": ["capacity", "rate", "tph", "t/d", "t/h"],
            "price_amount": ["price", "cost", "$/t", "USD/t", "USD/kW", "USD/unit"],
            "consumption_value": ["dosage", "consumption", "kg/t", "g/t", "L/t"],
            "voltage_kV": ["voltage", "kV"],
            "length_m": ["length", "L (m)"],
        },
        "entity_patterns": [
            "Crusher/Mill: manufacturer+model near kW, capacity/throughput, dimensions.",
            "Pump: type (centrifugal/PD/slurry) + head/flow (m, m3/h) + efficiency + motor kW.",
            "Conveyor: length (m), lift (m), belt width (mm), speed (m/s), installed kW.",
            "Flotation: cell type + volume (m3) + air rate (m3/h) + residence time (min).",
            "Thickener: diameter (m) + torque (kNm) + area (m2) + underflow density (%).",
            "Piping: size (NPS) + schedule + material + service + total length (m).",
            "Electrical: transformer MVA, switchgear voltage, cable size, MCC tiers, VFD counts.",
            "Reagents: name + consumption (g/t or kg/t) + unit cost (USD/t or USD/kg).",
            "Utilities: power kWh/t tariffs; water m3/h supply; compressed air kW/kWh per t.",
        ],
    },
    # -------------------------------------------------------------------------
    # 7) CHECKS (quality & completeness recommendations)
    # -------------------------------------------------------------------------
    "QUALITY": {
        "required_patterns": [
            "SystemBreakdown",
            "PackageEquipment",
            "InputsToProcess",
            "CostAttachment",
        ],
        "provenance_required": True,
        "min_confidence": 0.40,
    },
    # -------------------------------------------------------------------------
    # 8) AUTHORING GUIDES (per-category required fields for exhaustiveness)
    # -------------------------------------------------------------------------
    "GUIDES": {
        "EquipmentItem": {
            "required_fields": ["name", "equipment_class"],
            "preferred_fields": [
                "powerKw",
                "capacity_value",
                "capacity_unit",
                "throughput_value",
                "throughput_unit",
                "manufacturer",
                "model",
                "availabilityPct",
                "location",
            ],
            "cost_link_required": False,  # True if cost appears in same table/snippet
            "bulks_expected": [
                "Piping",
                "Electrical",
                "Instrumentation",
                "Civil/Structural",
            ],
        },
        "BulkItem:Piping": {
            "required_fields": [
                "name",
                "bulk_type",
                "length_m",
                "pipe_size_NPS",
                "schedule",
                "pipe_material",
            ],
            "preferred_fields": ["pressure_class", "corrosion_allow_mm"],
        },
        "BulkItem:Electrical": {
            "required_fields": ["name", "bulk_type", "voltage_kV"],
            "preferred_fields": [
                "feeder_type",
                "cable_size_mm2",
                "transformer_MVA",
                "fault_level_kA",
            ],
        },
        "MaterialInput": {
            "required_fields": ["name", "material_class"],
            "preferred_fields": [
                "consumption_value",
                "consumption_unit",
                "price_amount",
                "currency",
                "currencyYear",
            ],
        },
        "UtilityInput": {
            "required_fields": ["name", "utility_type"],
            "preferred_fields": [
                "rate_value",
                "rate_unit",
                "cost_per_unit",
                "currency",
                "currencyYear",
                "peak_demand_kW",
            ],
        },
        "CostBasisItem": {
            "required_fields": [
                "name",
                "basis_code",
                "price_amount",
                "currency",
                "currencyYear",
            ],
            "preferred_fields": [
                "estimate_class",
                "errorPlusPct",
                "errorMinusPct",
                "effectiveDate",
                "costBasis",
            ],
        },
    },
    # -------------------------------------------------------------------------
    # 9) DEFAULTS
    # -------------------------------------------------------------------------
    "DEFAULTS": {
        "currency": "USD",
        "currency_year": 2025,
        "unit_system": "SI",
        "equipment_kind_default": "Fixed",
    },
}
