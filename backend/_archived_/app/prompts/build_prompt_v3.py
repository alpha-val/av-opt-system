"""
build_prompt_modular.py
Alpha-Val Optionality — Modular Prompt Builder (v2)
---------------------------------------------------
Goal: Assemble a clean, consistent, and extensible prompt from discrete sections
without altering section text. You control inclusion order via `assemble_prompt`.

Usage:
    from ontology_v2 import ONTOLOGY
    from build_prompt_modular import assemble_prompt

    prompt = assemble_prompt(
        ontology=ONTOLOGY,
        rules=[
            "BASE_CASE",          # include Base Case contract
            "TABLE_EXTRACTION",   # include Table Extraction Policy block
            "UNITS_NORMALIZATION",
            "GLOBAL_OBJECTS",
            "AACE_REFERENCE"      # include AACE class reference block if provided
        ],
        extra_blocks={
            "TABLE_EXTRACTION_BLOCK": TABLE_EXTRACTION_BLOCK,  # paste your exact text
            "UNITS_NORMALIZATION_BLOCK": UNITS_NORMALIZATION_BLOCK,  # paste exact text
            "AACE_CLASS_REFERENCE_BLOCK": AACE_CLASS_REFERENCE_BLOCK  # optional
        }
    )
"""

from typing import Dict, Any, List, Optional
from .ontology_v2 import AACE_ESTIMATE_CLASS_DEFINITION
import json
from .ontology_msio_v1 import MSIO

# -----------------------------------------------------------------------------
# Paste your exact canonical text blocks below (no edits to content).
# -----------------------------------------------------------------------------

# 1) Required: Role / Heading
ROLE_BLOCK = """
# ALPHA-VAL – POLICY-BOUND EXTRACTION PROMPT
ROLE: You are an expert extraction system that reads reports and tables to produce a
typed knowledge graph consistent with the Alpha-Val ontology. Apply all included
policies and prove compliance in the output.
"""

# 2) Optional: Base Case Contract (include with "BASE_CASE")
BASE_CASE_BLOCK = """
--------------------------------------------------------------------------------
BASE CASE CONTRACT (MANDATORY WHEN PRESENT)
1) Create exactly one node of type "Baseline" named "Base Case" (or report-native name).
2) All extracted facts MUST be attachable to this Baseline via the declared edges.
3) Do NOT invent scenarios/options here; the goal is the baseline configuration as stated.
"""

# 3) Ontology Contract intro (static shell; details are populated from ontology)
ONTOLOGY_CONTRACT_SHELL = """
--------------------------------------------------------------------------------
ONTOLOGY CONTRACT (CANONICAL VOCAB)
Use only declared labels from ontology. Each node must satisfy typed fields in TEMPLATES.
"""

# --------------------------------------------------------------------------
# HIERARCHICAL SYSTEMS & INPUTS EXTRACTION POLICY (BOUND TO MSIO)
# --------------------------------------------------------------------------
HIERARCHICAL_EXTRACTION_BLOCK = """
    --------------------------------------------------------------------------------
    HIERARCHICAL SYSTEMS & INPUTS EXTRACTION POLICY
    --------------------------------------------------------------------------------
    Goal:
    Identify, extract, and classify all systems, subsystems, packages, equipment, bulks,
    and operating inputs (materials, utilities, labor, and cost basis) described in the
    document, using the hierarchical taxonomy defined in the Mining Systems & Inputs
    Ontology (MSIO).  Preserve normal Alpha-Val JSON structure (`nodes`, `edges`),
    but include explicit ontology mappings for hierarchy and class resolution.

    --------------------------------------------------------------------------------
    1. Hierarchy Recognition
    --------------------------------------------------------------------------------
    Recognize hierarchical patterns in text and tables:
        - System → Subsystem → Package → EquipmentItem → BulkItem
        - Inputs (MaterialInput, UtilityInput, LaborCategory)
        - CostBasisItem (CAPEX/OPEX, Direct/Indirect classification)

    Typical cues:
        • Section headings (e.g., “3. Crushing and Conveying System”)
        • Table titles (“Mechanical Equipment List – Grinding Area”)
        • Column headers containing scope (e.g., “Package No.”, “Area”)
        • Indentation, numbering, or “within” language (“within Grinding Area”)

    Every extracted node must carry:
        "ontology_path": <MSIO taxonomy path string>,
        e.g., "Equipment/Mechanical/Crushing/PrimaryGyratory"
    --------------------------------------------------------------------------------
    2. Node Construction & Ontology Mapping
    --------------------------------------------------------------------------------
    For each extracted entity:
        1. Determine its **entity category** using MSIO.TAXONOMY and SYNONYMS.
        Examples:
            "Primary Crusher" → EquipmentItem (Equipment/Mechanical/Crushing/PrimaryGyratory)
            "Plant MCC"        → EquipmentItem (Equipment/Electrical/MCCsVFDs)
            "Process Water Line"→ BulkItem (Equipment/Piping/Water)
            "Flotation Reagent"→ MaterialInput (INPUT/MAT/FlotationReagents)
            "Power Tariff"     → UtilityInput (INPUT/UTIL/Power)
            "Installation Labor"→ LaborCategory (INPUT/LAB/Maintenance)
            "Freight & Duties" → CostBasisItem (COST/CAPEX/DIRECT/FreightDuties)

        2. Create node under top-level key `"nodes"` with:
            {
                "id": "<uuid>",
                "type": "<mapped Alpha-Val node_type>",
                "ontology_path": "<MSIO taxonomy path>",
                "category": "<MSIO category, e.g., EquipmentItem>",
                "properties": { … filled per MSIO.TEMPLATES[...] … },
                "provenance": {sourceDoc, sourcePage?, extractionMethod?},
                "confidence": 0.0–1.0
            }

        3. Add hierarchy linkage edges:
            Subsystem  —PART_OF→ System
            Package    —PART_OF→ Subsystem
            Equipment  —PART_OF→ Package
            BulkItem   —PART_OF→ Equipment
            Material/Utility —CONSUMES→ Equipment
            Equipment —HAS_COST→ CostBasisItem

    --------------------------------------------------------------------------------
    3. Property Population
    --------------------------------------------------------------------------------
    Populate all relevant template fields from MSIO.TEMPLATES for the given category:
        • EquipmentItem → powerKw, capacity_value, throughput_value, manufacturer, model, duty.
        • BulkItem → bulk_type (Piping/Electrical/etc.) + category-specific attributes.
        • MaterialInput → material_class, consumption_value/unit, price_amount/currency/year.
        • UtilityInput → utility_type, rate_value/unit, cost_per_unit, voltage_kV, peak_demand_kW.
        • CostBasisItem → basis_code, price_amount, currency, estimate_class, costBasis.
        • LaborCategory → headcount_FTE, hourly_rate, shift_pattern.

    Normalize numeric and unit fields per UNITS NORMALIZATION POLICY.

    --------------------------------------------------------------------------------
    4. Cost Basis Classification
    --------------------------------------------------------------------------------
    Map each CostBasisItem to its canonical cost path per MSIO.COST_BASIS_TAGS:
        • Direct CAPEX → COST/CAPEX/DIRECT/*
        • Indirect CAPEX → COST/CAPEX/INDIRECT/*
        • OPEX → COST/OPEX/*

    Attach cost basis to equipment, bulks, or inputs with :HAS_COST edges.

    --------------------------------------------------------------------------------
    5. Provenance, Normalization, and Confidence
    --------------------------------------------------------------------------------
    Every node and edge must include:
        - provenance: {sourceDoc, sourcePage?, tableRef?, extractionMethod: "LLM"|"tabular"}
        - ontology_path: the canonical MSIO taxonomy string
        - confidence: numeric score (0.0–1.0)

    Normalize:
        • Units per UNITS NORMALIZATION & DEDUPLICATION POLICY
        • Currency to ISO-4217
        • Estimate classes per AACE reference

    --------------------------------------------------------------------------------
    6. Output Requirements
    --------------------------------------------------------------------------------
    All hierarchical extractions must be serialized under the standard Alpha-Val schema:
    {
    "nodes": [ {…System…}, {…Subsystem…}, {…EquipmentItem…}, {…MaterialInput…}, … ],
    "edges": [
        {"source": "equip_12", "target": "pkg_5", "type": "PART_OF"},
        {"source": "equip_12", "target": "cost_7", "type": "HAS_COST"},
        {"source": "reagent_3", "target": "equip_12", "type": "CONSUMES"}
    ],
    "meta": {
        "ontology_mapping": "MSIO_v0.9.0",
        "policyCompliance": {…},
        "normalization": {…}
    }
    }

    --------------------------------------------------------------------------------
    7. Validation & Completeness
    --------------------------------------------------------------------------------
    ✓ Each EquipmentItem must have an ontology_path and category.
    ✓ Each node must resolve to one MSIO.TAXONOMY path (no orphan nodes).
    ✓ Each Package and Subsystem must have PART_OF edges upwards.
    ✓ Each EquipmentItem should have at least one cost, input, or bulk relationship.
    ✓ Use MSIO.PATTERNS (SystemBreakdown, PackageEquipment, InputsToProcess, CostAttachment)
    to verify graph completeness.

    ✗ Do not invent hierarchy beyond evidence.
    ✗ Do not merge distinct physical items into one node.
    ✗ Do not assign arbitrary ontology paths—use the closest defined code.

    --------------------------------------------------------------------------------
    8. Examples
    --------------------------------------------------------------------------------
    Example 1 — Table snippet: "Primary Crusher, 600 kW, 2500 tph"
    → Node type: EquipmentItem
    ontology_path: "Equipment/Mechanical/Crushing/PrimaryGyratory"
    type: "Equipment"
    properties: {"powerKw":600, "throughput_value":2500, "throughput_unit":"tph"}
    → Connect to parent Package "Crushing & Conveying" via PART_OF.

    Example 2 — Row: "Flocculant, 0.1 kg/t, USD 2500/t"
    → Node type: MaterialInput
    ontology_path: "INPUT/MAT/Flocculant"
    properties: {"consumption_value":0.1,"consumption_unit":"kg/t","price_amount":2500,"currency":"USD"}
    → Connect via CONSUMES edge to Thickener Package.

    --------------------------------------------------------------------------------
    Compliance
    --------------------------------------------------------------------------------
    All extracted entities must reference a valid MSIO taxonomy path and be mappable
    to Alpha-Val ontology node/edge types through MSIO.MAPPINGS. Include ontology_path
    and category fields in every node for cross-ontology reasoning.
    """


# 4) Output schema (keep content; this is the single JSON object contract)
OUTPUT_FORMAT_BLOCK = """
--------------------------------------------------------------------------------
STRICT OUTPUT FORMAT (single JSON object)
{
  "nodes": [
    {
      "id": "stable_id-or-uuid",
      "type": "<NodeType>",
      "name": "string",
      "properties": {
        // Typed per ontology.TEMPLATES[NodeType]
        "provenance": {
          "sourceDoc": "string",
          "sourcePage": "int?",
          "extractionMethod": "LLM",
          "createdBy": "AlphaVal"
        }
      }
    }
  ],
  "edges": [
    {
      "source": "<node_id>",
      "target": "<node_id>",
      "type": "<EdgeType>",
      "properties": {
        "confidence": 0.0-1.0,
        "rationale": "short reason",
        "provenance": {
          "sourceDoc": "string",
          "sourcePage": "int?",
          "extractionMethod": "LLM",
          "createdBy": "AlphaVal"
        }
      }
    }
  ],
  "meta": {
    "policyCompliance": {
      "appliedPatterns": [],
      "synonymMappings": [],
      "tableAliasMappings": [],
      "normalizations": [],
      "defaultsUsed": [],
      "dedupe": {"rulesApplied": [], "mergedPairs": []},
      "qualityGate": {
        "declaredEdgeTypesOnly": true/false,
        "singletonNodesAllowed": true/false,
        "provenanceFieldsPresent": true/false,
        "templatesSatisfied": true/false
      }
    }
  }
}
"""

# 5) Required: Quality Gate (no edits)
QUALITY_GATE_BLOCK_SHELL = """
POLICY — QUALITY GATE (BOUND)
- edges_must_use_declared_types = {edges_declared} ⇒ Only ontology EDGE_TYPES allowed.
- allow_singleton_nodes = {singletons} ⇒ Singleton nodes {singletons_text}.
- require_provenance_fields = {prov_fields} ⇒ Present on EVERY node/edge.
- reject_if_missing_required_template_fields = {reject_templates} ⇒ If required missing, omit node.
- Confidence: omit facts with confidence < 0.40.
"""

# 6) Required: Synonyms and Hints shells (data injected from ontology)
SYNONYMS_BLOCK_SHELL = """
POLICY — SYNONYMS (BOUND; CANONICAL TYPE RESOLUTION)
Map source synonyms to canonical types before emission and log mapping.
{synonym_lines}
"""

HINTS_BLOCK_SHELL = """
POLICY — EXTRACTION HINTS (BOUND)
Entity patterns (prioritize):
{entity_pattern_lines}

Table header aliasing (apply BEFORE assigning field names):
{alias_lines}
"""

# 7) Required: Patterns shell (data injected)
PATTERNS_BLOCK_SHELL = """
POLICY — PATTERNS (BOUND; SATISFY WHEN EVIDENCE EXISTS)
Try to assemble nodes/edges to satisfy at least one relevant pattern:
{pattern_lines}
"""

# 8) Required: Defaults shell (data injected)
DEFAULTS_BLOCK_SHELL = """
POLICY — DEFAULTS & FALLBACKS (BOUND)
Apply defaults only if the value is truly absent after aliasing & normalization.

Defaults:
{defaults_lines}

Log any default used: meta.policyCompliance.defaultsUsed = [{{"field":"currency","value":"{default_currency}"}}]
"""

# 9) Optional: Units Normalization Policy (include with "UNITS_NORMALIZATION")
# Paste your **exact** units normalization block content here:
UNITS_NORMALIZATION_BLOCK = """
    UNITS NORMALIZATION & DEDUPLICATION POLICY:
    * Unit metric and cost extraction policy
    ** Create the attribute "capacity_value" for values representing capacity
    ** Create the attribute "capacity_unit" for the corresponding unit.
    ** Keep the original attribute (e.g., "flow_rate:500 gals/hr") in the node properties for provenance.
    * When extracting attributes with units (e.g., "flow_rate:500 gals/hr"):
    - Parse and store the numeric value in a property called "flow_rate_value".
    - Parse and store the unit in a property called "flow_rate_unit".
    - Normalize units to a consistent format (e.g., "gallons per hour" → "gals/hr").
    * Deduplicate entities with equivalent normalized values and units.
    * Store original text in metadata for provenance.

    * Normalization Directives
    ** Prefer SI units where sensible, but retain original in auxiliary fields if helpful.
    ** Mapping directives:
    ** gals, gallons, gal -> gallons
    ** ft3, cubic feet -> cubic feet
    *** gallons/hour, gallons per hour, gal/hr, gph → gals/hr
    *** gallons/min, gals/min, gpm → gals/min
    *** cubic meters/hour, cubic meters per hour, m3/hr, m3h → m3/hr
    *** barrels/day, barrels per day, bbl/day, bpd → bbl/day
    *** liters/minute, liters per minute, L/min, Lpm → L/min
    *** tons/day, tons per day, tpd → tons/day
    *** pounds/hour, pounds per hour, lb/hr, lbs/hr, pph → lb/hr
    *** kilograms/hour, kilograms per hour, kg/hr, kph → kg/hr
    ** If units are not provided then use appropriate placeholders or null values.
    *** E.g., "capacity_value": "1000", "capacity_unit": null
    ** Map common abbreviations to standard forms.
    *** E.g., "TPH" → "tons/hr", "gals" → "gallons"
    *** pounds → lbs, kilograms → kg, liters → L, cubic meters → m3
    * When both imperial and metric units are provided, store both as separate properties.
    * For ranges or dual units (e.g., "10-20 TPH" or "500 gals/hr (metric: 1892 L/hr)"):
    - Extract min/max values into separate properties (e.g., "capacity_value_min", "capacity_value_max").
    - Store each unit variant in its own property (e.g., "capacity_unit_imperial", "capacity_unit_metric").
    * For compound values (e.g., "5 @ 80% efficiency"), separate the main value from conditions.
    * Always retain the original text attribute for provenance.

    # Evidence for variations in capacity:
    * Extracting factors or variations of entities due increase or decrease in capacity:
    ** You must do the following if entity name consists of a base capacity plus an adjustment (e.g., "250 (base)", "125 (-50%)", "500 (2x)"), e.g., 250 (base) -> baseline value, 125 (-50%) -> lowered by 50%, 375 (+50%) -> increased by 50%, 500 (2x) -> doubled
    ** Handle the variations:
    *** Percentages: "-50%", "+25%"
    *** Multipliers: "2x", "0.5x"
    *** Absolute changes: "-100", "+200"
    ** Store the adjusted value in "capacity_value" and the adjustment method in a separate property (e.g., "capacity_adjustment": "-50%").
    ** * Example:
    Fruit Washer Cost Estimates table:
    Capacity (lbs/hr),	Spec / Notes,	Base Domestic, Cost Estimate,	Freight & Delivery Buffer,	"All-in to Charlotte" Estimate
    125 (−50%),	Compact drum,	$5,000,	+10%,	$5,500
    250 (base),	Standard auto rotating drum,	$9,000,	+10%,	$9,900
    500 (2×),	Larger drum, motorized feed,	$15,000,	+12%,	$16,800
    1,000 (4×),	Dual-drum continuous,	$25,000,	+15%,	$28,750
    2,500 (10×),	Industrial flume / continuous,	$45,000,	+15%,	$51,750    
    """

# 10) Optional: Table Extraction Policy (include with "TABLE_EXTRACTION")
TABLE_EXTRACTION_BLOCK = """
    TABLE EXTRACTION POLICY:
    When encountering tabular data in any format, apply these principles:

    TABLE STRUCTURE RECOGNITION:
    * **Lattice tables**: Regular grid with clear row/column boundaries
    - Extract using cell coordinates (row, col)
    - Preserve header hierarchy if multi-level

    * **Stream tables**: Tabular data without visible grid lines
    - Infer structure from whitespace and alignment
    - Use consistent column positions to group values

    * **Inverted tables**: Attributes as rows, instances as columns
    - Transpose mentally: each column becomes an entity
    - Row labels become property names

    * **Nested headers**: Column headers with sub-columns
    - Parse as "parent_subcolumn" or structured dict
    - Example: "Type / Incl." → type_incl or {type: {incl: value}}

    EXTRACTION APPROACH:
    1. **Parse headers**: 
    - Top row(s) define property names
    - Detect multi-level headers
    2. **Normalize headers**:
    - Handle merged cells and sub-headers
    - Normalize to ontology property names (NODE_PROPERTIES)
    3. **Process rows**:
    - Each row = one potential entity (lattice/stream)
    - Each column = one potential entity (inverted)
    - Maintain row/column index for provenance
    4. **Handle missing data**:
    - Empty cells → null/absent property
    - "N/A", "-", "..." → explicit null
    - Never infer or fill missing values

    COLUMN INTERPRETATION:
    * Detect units in headers: "Capacity (TPH)" → capacity_tph
    * Handle dual units: both imperial and metric as separate properties
    * Parse compound cells: "10-20" → min/max, "5 @ 80%" → value + condition
    * Separate numeric values from qualifiers: "100 kg" → value=100, unit=kg

    ENTITY CONSTRUCTION FROM TABLES:
    * **Type inference**:
    - Column names suggest type: "Model" + "Capacity" → Equipment
    - Use ontology NODE_TYPES as targets
    - Default to most specific applicable type
    - If no obvious or explicit name column, use context or table title for naming; create descriptive names; else use enumerated generic names
    - IMPORTANT: For each column in the table, create an attribute in the node properties; for example, if the first column is not name or equipment information, then create a property in the node properties with the column name and value from that cell

    * **Property mapping**:
    - Map column names to NODE_PROPERTIES
    - Keep original column name in metadata
    - Add table_id, row_index, col_index for lineage

    * **Naming convention**:
    - Names should be explicit, not generic (e.g., avoid "Item")
    - Names should include distinguishing attributes (e.g., "Pump 10 TPH")
    - Synthesize from key attributes: "{Type} {Dimension}"
    - Ensure uniqueness within table scope

    * **Confidence scoring**:
    - Direct extraction: confidence=1.0
    - Inferred type/property: confidence=0.7–0.9
    - Ambiguous mappings: confidence=0.5–0.7
    - Missing/empty cells: confidence=0.0
    - Document reasoning in 'extracted_from' metadata

    * **Evidence tracking**:
    - Include table_id, row_index, col_index in node properties
    - Include "evidence" snippet from table context
    - Use "extracted_from": "table" with method "tabular"


    EDGE CREATION FROM TABLES:
    * **Implicit relationships**:
    - Sequential rows may have PRECEDES/NEXT relationships
    - Grouped sections indicate hierarchical PART_OF
    - Cross-references in cells create typed edges

    * **Aggregation edges**:
    - Subtotals/totals create AGGREGATES edges
    - Source: detail rows → Target: summary row

    * **Provenance edges**:
    - Every entity → EXTRACTED_FROM → table/row reference
    - Include extraction_method: "tabular"

    QUALITY REQUIREMENTS FOR TABLE EXTRACTION:
    ✓ Preserve all non-empty cells as properties
    ✓ Maintain row/column provenance in metadata
    ✓ Normalize property names to ontology
    ✓ Parse units and separate from values
    ✓ Detect and handle merged cells
    ✓ Respect table boundaries (no bleeding across tables)
    ✓ Set confidence=1.0 for direct table values
    ✓ Create meaningful entity names
    ✓ Add table name in properties for context
    ✗ Never merge distinct rows into one entity
    ✗ Never split one row into multiple entities (unless clearly composite)
    ✗ No hallucinated values for empty cells
    ✗ No assumptions about missing units
"""

# 11) Optional: Global Objects Summary (include with "GLOBAL_OBJECTS")
GLOBAL_OBJECTS_BLOCK = """
    --------------------------------------------------------------------------------
    GLOBAL OBJECTS SUMMARY (FOR OPTIONALITY & COST ALTERNATIVES) — ACTIONABLE
    --------------------------------------------------------------------------------
    Goal
    Summarize all globally relevant options, alternatives, KPIs, constraints, costs, risks,
    decision variables, cost drivers, uncertainties, assumptions, schedules, permits,
    and data gaps that influence optionality and cost estimation in THIS document.

    What to produce
    1) A populated summary at:  meta.global_objectives
    - Use the category keys and field sets from ontology.GLOBAL_OBJECTIVES_SPEC.categories.
    - For each category item, populate the listed fields using values EXTRACTED from this
        report/tables (not from the spec), and include:
        - "refs": array of node_ids/edge_ids supporting the item
        - "provenance": {sourceDoc, sourcePage?, extractionMethod?}
        - "confidence": 0.0–1.0

    2) Nodes & Edges (if missing)
    - If a relevant item is NOT yet represented by a node/edge, create a minimal node that
        satisfies its ontology template (required fields only) and add appropriate edges.
    - Reuse existing node_ids/edge_ids whenever present.

    How to extract (category-wise cues)
    Use the ontology categories/fields as your contract AND mine the text/tables accordingly:

    • KPIs - key performance indicators (node_types: KPI; fields: name, formula, unit, direction)
    Signals: “KPI”, “target”, “objective”, “% recovery”, “OPEX/ton”, “availability %”.
    Actions: Parse formulae, units, target/min/max. Link with :SATISFIES or :OPTIMIZES_FOR if present.

    • Constraints (Constraint; fields: name, expression, severity, rationale)
    Signals: “shall/must”, “limit”, “cap”, inequalities (<=, >=), “maximum demand”.
    Actions: Normalize expressions (e.g., powerKw <= 2500). Capture rationale if stated.

    • Cost (CostItem; fields: name, price, estimateClass, effectiveDate, costBasis)
    Signals: currency + value + unit (USD, M$, USD/kW, USD/t). Map estimate class via AACE ref.
    Actions: Emit Money with currencyYear; if rebased, create derived CostItem via :DERIVED_FROM
            and :INDEXED_BY (EscalationIndex) as evidence.

    • Risk (Risk; fields: name, risk_severity, risk_probability)
    Signals: “risk”, “uncertainty”, “variability”, “likelihood/probability”, “impact/severity”.
    Actions: Capture mitigation if implied; relate with :HAS_RISK (owner entity) and record refs.

    • Options (Option; fields: name, category, description)
    Signals: tunable choices (vendor selection, technology choice, layout, energy source, maintenance regime).
    Actions: Connect options to effects with :AFFECTS_COST, :IMPACTS_KPI, :ENABLES.

    • Alternatives (Alternative; fields: name, optionRef, assumptions)
    Signals: “Option A/B”, “Vendor A/B”, “Case 1/2/3”, “variant”.
    Actions: Relate peers via :ALTERNATIVE_TO and associate to their Option via optionRef.

    • Decision Variables (DecisionVariable; fields: name, domain, unit, defaultValue)
    Signals: throughput setpoints, grind size, reagent dosage, plant hours.
    Actions: Encode feasible ranges (e.g., “[500,1500] tph”).

    • Cost Drivers (CostDriver; fields: name, driverType, unit)
    Signals: power, reagents, labor, freight, maintenance, spares, water, tails.
    Actions: Link drivers with :DRIVES to CostItem/KPI where stated.

    • Uncertainties (Uncertainty; fields: distribution, low, mode, high)
    Signals: “normal/triangular/lognormal”, P10/P50/P90, ranges ±%.
    Actions: Convert stated ranges into numeric fields; preserve text in provenance.contextSnippet.

    • Assumptions (Assumption; fields: name, short_description)
    Signals: explicit “assumption(s)”, basis-of-estimate sections.
    Actions: Capture succinctly; link important ones via :GOVERNED_BY or :REFERENCES.

    • Schedule (Schedule/Milestone/Event; fields: name, time, short_description)
    Signals: commissioning/start-up dates, lead times, critical path.
    Actions: Use :PRECEDES/:FOLLOWS/:NEXT for ordering; attach TimeWindow if known.

    • Permits (Permit; fields: issuingAuthority, validFrom, validTo, permitNumber)
    Signals: permit IDs, approvals, license numbers, regulators.
    Actions: Connect with :PERMITTED_BY / :REGULATED_BY to Facility/Process.

    • Data Gaps (DataGap; fields: missingField, context)
    Signals: “TBD”, “N/A”, missing columns, redacted values.
    Actions: Describe the gap and where it occurs (table cell/page).

    Dedupe & merge
    - Merge items that are semantically the same (case-insensitive name + same key fields).
    - Record merged node_id pairs in meta.policyCompliance.dedupe.mergedPairs.

    Provenance & refs (mandatory)
    - For EVERY item in meta.global_objectives:
    - refs: node_ids and/or edge_ids used as evidence (e.g., ["kpi_1","edge_17"]).
    - provenance: include sourceDoc and sourcePage; include tableRef (tableId,rowIndex,colIndex)
        when from tables; set extractionMethod to "LLM" or "tabular".

    Confidence policy
    - Direct numeric/textual evidence: 0.9–1.0
    - Mapped from soft language or inferred from context: 0.6–0.8
    - Ambiguous/weak: 0.4–0.6 (omit if < 0.40)

    Normalization requirements
    - Apply UNITS NORMALIZATION & DEDUPLICATION policy for capacities/flows/throughputs.
    - Apply METRIC_NORMALIZATION shape for quantities/money (raw+normalized where applicable).
    - Preserve original text in provenance.contextSnippet and/or Evidence.originalAttribute.

    Output shape (strict)
    - Conform to ontology.GLOBAL_OBJECTIVES_SPEC.output_shape category keys exactly.
    - Omit a category only if the spec does NOT include it; otherwise include it as an empty list.

    Example (schematic)
    "meta": {
        "global_objectives": {
            "kpis": [
                {"name":"OPEX Intensity","formula":"opex/throughput","unit":"USD/t","direction":"minimize",
                "refs":["kpi_1","edge_12"], "provenance":{"sourceDoc":"docA","sourcePage":12}, "confidence":0.92}
            ],
            "constraints": [
                {"name":"Power cap","expression":"powerKw <= 2500","severity":"high",
                "refs":["constraint_3"], "provenance":{"sourceDoc":"docA","sourcePage":18}, "confidence":0.9}
            ],
            "cost": [
            {"name":"Primary crusher CAPEX","price":{"amount":2100000,"currency":"USD","currencyYear":2015},
                "estimateClass":"AACE_Class_4","costBasis":"FOB","refs":["cost_12","edge_33"],
                "provenance":{"sourceDoc":"docA","sourcePage":31}, "confidence":0.95}
            ],
            "... other categories per spec ..."
        },
        "policy_compliance": {
            "... as per COMPLIANCE FOOTER ..."
        },
        "provenance": {
            "sourceDoc": "docA",
            "sourcePage": 12,
            "tableRef": {
                "tableId": "table_1",
                "rowIndex": 5,
                "colIndex": 3
            }
        },
        "references": {
            "references": [
                {"title":"Mining Cost Estimation Handbook","authors":["John Doe"],"year":2020,"publisher":"Mining Press","url":"http://..."}
            ],
            "figures": [
                {"title":"Process Flow Diagram","caption":"Main process flow with key equipment","source":"fig_1"}
            ],
            "tables": [
                {"title":"Cost Estimates by Equipment Type","caption":"Summary of estimated costs for major equipment items","source":"table_1"}
            ],
            "footnotes":[
                {"text":"Cost estimates are based on 2020 USD values.","source":"footnote_1"}
            ]
        }
    }

    Do NOT
    - Do not echo or restate ontology.GLOBAL_OBJECTIVES_SPEC itself in the output.
    - Do not add categories/fields that are not in the spec.
    - Do not invent items without evidence.

    Success criteria
    - Every populated item is traceable via refs + provenance.
    - Categories reflect actual content of THIS report/tables.
    - Units, currencies, and estimate classes follow the normalization and AACE policies.
    """

# 12) Optional: AACE Class Reference appendix (include with "AACE_REFERENCE")
AACE_CLASS_REFERENCE_BLOCK = AACE_ESTIMATE_CLASS_DEFINITION

# 13) Required: Compliance Footer (no edits)
COMPLIANCE_FOOTER_BLOCK = """
POLICY COMPLIANCE FOOTER (REQUIRED in meta.policyCompliance):
- Log synonym mappings, alias mappings, normalizations performed, defaults used,
  dedupe rules applied, and quality gate booleans.
"""

# 14) Required: Node and Relations extraction block (no edits)
NODES_AND_RELATIONS_EXTRACTION_BLOCK = """
    NODES AND RELATIONS EXTRACTION:
    Using ontology.NODES_AND_RELATIONS_SPEC, extract all nodes and their relationships
    from the document. Include all relevant metadata and provenance information.

    Mission: Produce a clean, deduplicated knowledge graph for mining/process-engineering content
    aligned exactly to the configured ontology.

    You MUST:
    - Extract only what is explicitly or strongly implied by the text.
    - Do not infer or assume information not present.
    - Emit only node/edge types that appear in the ontology.
    - Each node must have a type or property["label"] that maps to NODE_TYPES.
    - Use only node/edge property names that appear in the ontology metadata lists.
    - Attach evidence and a confidence score to every node and edge using the
      allowed property names from NODE_PROPERTIES / EDGE_PROPERTIES.
    - Normalize entity names and deduplicate obvious variants.

    You MUST NOT:
    - Hallucinate entities, methods, or relationships.
    - Invent node/edge types or property keys not present in the ontology lists.
    - Emit empty labels or unnamed nodes.
    - Create cycles unless clearly supported by the text.
    - Add the string (table_entity) at the end of entity names.

    ONTOLOGY (from config.py):
    Allowed node types (NODE_TYPES): See ontology contract for details.

    Allowed edge types (EDGE_TYPES): See ontology contract for details.

    OUTPUT CONTRACT (strict):
    Node object (each item in extract_nodes.nodes) MUST have:
    - "id": stable unique string identifier (uuid)
    - "type": one of NODE_TYPES; a Node object must have a type
    - "properties": object/dict containing:
        • follow the properties mentioned in NODE_PROPERTIES in the ontology
        • prioritize finding cost associated with an entity (e.g., 'cost_value', 'price_value', 'currency', 'basis_year', 'expenditure')
        • always keep cost value and currency as separate properties (never as a combined string)
        • if a cost or price is present, extract the numeric value to 'cost_value' and the currency to 'currency'
        • if a basis year is present, extract it to 'basis_year'
        • if currency is not present, set 'currency' to null
        • if basis year is not present, omit 'basis_year'
        • include evidence/confidence meta-properties from NODE_PROPERTIES
        • include any other domain-specific properties from NODE_PROPERTIES that appear in the text
    - "name": human-readable name (string)

    Edge object (each item in extract_edges.edges) MUST have:
    - "source": node id
    - "target": node id
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
        • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
        • any domain attributes the ontology expects for that edge (if any)

    EXAMPLES:
    "NODE_PROP_EXAMPLES": {
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
    }
    

    NORMALIZATION & DEDUPLICATION RULES:
    - Canonicalize names for comparison: lowercase; strip punctuation/underscores/dashes/spaces.
    - Merge if (same type) AND (canonical names match). Otherwise keep separate but
      you may create a low-confidence equivalence edge (if your ontology defines one).
    - Maintain 'aliases' inside the node 'properties' if variants appear in text.

    Units & values:
    - Normalize units (prefer SI where sensible) but preserve the original in an
      auxiliary field (e.g., 'display_value' or 'orig_unit') if helpful.
    - For monetary values, always extract and store the numeric value and currency as separate properties.
    - For monetary values, carry currency (ISO code) and basis_year whenever stated.

    Confidence scoring (guideline):
    - 0.90–1.00: explicit statement, exact figure/name, direct quote.
    - 0.70–0.89: implied by nearby text or table; light inference (e.g., unit conversion).
    - 0.50–0.69: cross-paragraph inference consistent with evidence.
    - <0.50: prefer to omit unless essential for connectivity.

    Evidence:
    - Keep excerpts short (≤250 chars). Populate the appropriate meta fields strictly
      from NODE_PROPERTIES / EDGE_PROPERTIES (e.g., 'source_doc', 'extracted_from', etc.).

    NORMALIZATION & DEDUPLICATION POLICY:
    Refer to the UNIT_NORMALIZATION_BLOCK for detailed rules.

    QUALITY GATE (pre-return):
    - Every node: non-empty, unique 'id' (uuid), valid 'type', and a 'properties' dict.
    - Every node has a 'name' property; populate it with the proper entity name.
    - Every node has a 'type' property that matches NODE_TYPES.
    - Every node property key matches NODE_PROPERTIES.
    - For nodes of type 'Equipment', 'Process', 'Material', 'Product', 'Waste', etc., acquire cost details if they appear in text.
    - For nodes of type 'CostRule', ensure compliance with COST & METHOD POLICY block.
    - For nodes of type 'CostEstimate' or similar, ensure costing details are present.
    - For node properties that are costs/prices, always extract and store the numeric value and currency as separate properties.
    - For node properties that are costs/prices, include currency and basis_year when available.
    - Every edge: valid 'source', 'target', 'type', and a 'properties' dict.
    - Every edge property key matches EDGE_PROPERTIES.
    - For node and edge, include evidence; evidence must be present and derived from the text.
    - For node and edge, include confidence; confidence must be present and justified.
    - All nodes must be linked with type that matches EDGE_TYPES.
    - Normalize units and values as per the rules above.
    - Only ontology-approved types and meta property keys are used.
    - Do not hallucinate entities, relationships, or properties.

    Return:
    - nodes with extract_nodes(nodes=[...])
    - edges with extract_edges(edges=[...])
    - meta with extract_meta(meta=[...])
    """

# 15) Cost & Method Policy
COST_AND_METHOD_POLICY_BLOCK = """
    COST & METHOD POLICY:
    * Reserve the 'CostRule' node type only for reusable cost-estimation methods.
    Examples: factors, parametric curves, scale exponents, lookup tables,
    regressions, escalation/deflation formulas, or vendor price lists used as a
    method (not just a one-off price).
    * Do not create a 'CostRule' node just because a dollar amount appears.
    - If the text states a specific price/cost for an entity, attach it to that
        entity as a property in its node 'properties' (e.g., 'cost_value' plus
        currency and basis year).
    * Link rules to governed targets with an appropriate edge type from EDGE_TYPES
    (e.g., :GOVERNED_BY if available in your ontology).
    * When costs/prices appear in text, attach them directly as properties on the
    relevant node (e.g., Equipment/Process) or use dedicated costing nodes
    defined in your ontology (e.g., 'CostEstimate') and edges from EDGE_TYPES
    (e.g., :COSTED_BY / :AGGREGATES, if present).
    * For every cost or price, always extract and store the numeric value in a property
    called 'cost_value' (or 'price_value' if appropriate), and store the currency
    in a separate property called 'currency' (e.g., 'USD', 'EUR', etc.).
    * If a basis year is mentioned, store it in a property called 'basis_year'.
    * Do not merge cost value and currency into a single string; keep them as separate fields.
    * If a cost or price is mentioned without a currency, set 'currency' to null.
    * If a cost or price is mentioned without a basis year, omit 'basis_year'.
    """

# -----------------------------------------------------------------------------
# Internal helpers (no text changes; just formatting & ordering)
# -----------------------------------------------------------------------------


def _join_lines(items: List[str]) -> str:
    return "\n".join(x for x in items if x and x.strip())


def _fmt_list(lst: List[str], limit: Optional[int] = None) -> str:
    if not lst:
        return "(none)"
    lst = lst if limit is None else lst[:limit]
    return ", ".join(lst)


def _bulleted(lst: List[str]) -> str:
    return "\n".join(f"- {x}" for x in lst) if lst else "- (none)"


def _json_to_str(data: Any) -> str:
    return json.dumps(data, indent=2)


# -----------------------------------------------------------------------------
# Section builders that *inject ontology data* in fixed shells (no text edits)
# -----------------------------------------------------------------------------


def section_ontology_contract(ontology: Dict[str, Any]) -> str:
    core = ontology.get("CORE", {})
    ext = ontology.get("EXTENSIONS", {}).get("mining_process", {})
    node_types = core.get("NODE_TYPES", [])
    edge_types = core.get("EDGE_TYPES", [])
    node_types_ext = ext.get("NODE_TYPES_ADD", [])
    edge_types_ext = ext.get("EDGE_TYPES_ADD", [])

    taxonomy = MSIO.get("TAXONOMY", {})

    lines = [
        ONTOLOGY_CONTRACT_SHELL,
        f"NODE_TYPES (Core excerpt): {_fmt_list(node_types, 18)} …",
        f"NODE_TYPES (Extension add): {_fmt_list(node_types_ext, 18)} …",
        f"EDGE_TYPES (Core excerpt): {_fmt_list(edge_types, 18)} …",
        f"EDGE_TYPES (Extension add): {_fmt_list(edge_types_ext, 18)} …",
        f"TAXONOMY excerpt: {_fmt_list(list(taxonomy.keys()), 18)} …",
        f"TAXONOMY MAPPINGS: {_fmt_list(list(MSIO.get('TAXONOMY_MAPPINGS', {}).keys()), 18)} …",
        f"TAXONOMY EDGE_MAP excerpt: {_fmt_list(list(MSIO.get('TAXONOMY_EDGE_MAP', {}).keys()), 18)} …",
    ]
    return _join_lines(lines)


def section_quality_gate(ontology: Dict[str, Any]) -> str:
    qg = ontology.get("QUALITY_GATE", {})
    edges_declared = qg.get("edges_must_use_declared_types", True)
    singletons = qg.get("allow_singleton_nodes", True)
    prov_fields = qg.get(
        "require_provenance_fields", ["sourceDoc", "extractionMethod", "createdBy"]
    )
    reject_templates = qg.get("reject_if_missing_required_template_fields", True)

    return QUALITY_GATE_BLOCK_SHELL.format(
        edges_declared=edges_declared,
        singletons=singletons,
        singletons_text=("allowed" if singletons else "not allowed"),
        prov_fields=prov_fields,
        reject_templates=reject_templates,
    )


def section_synonyms(ontology: Dict[str, Any]) -> str:
    syn = ontology.get("SYNONYMS", {})
    lines = (
        [f"{k}: {', '.join(v)}" for k, v in syn.items()] if syn else ["(no synonyms)"]
    )
    return SYNONYMS_BLOCK_SHELL.format(synonym_lines=_bulleted(lines))


def section_hints(ontology: Dict[str, Any]) -> str:
    hints = ontology.get("EXTRACTION_HINTS", {})
    entity_patterns = hints.get("entity_patterns", [])
    aliases = hints.get("table_column_aliases", {})
    alias_lines = [f"{k}: {', '.join(v)}" for k, v in (aliases or {}).items()] or [
        "(no alias map)"
    ]

    return HINTS_BLOCK_SHELL.format(
        entity_pattern_lines=_bulleted(entity_patterns or ["(no entity patterns)"]),
        alias_lines=_bulleted(alias_lines),
    )


def section_patterns(ontology: Dict[str, Any]) -> str:
    patterns = ontology.get("PATTERNS", {})
    patt_lines = []
    for name, spec in (patterns or {}).items():
        nodes = spec.get("nodes", [])
        edges = spec.get("edges", [])
        patt_lines.append(f"{name} → nodes:{nodes} | edges:{edges}")
    return PATTERNS_BLOCK_SHELL.format(
        pattern_lines=_bulleted(patt_lines or ["(no patterns)"])
    )


def section_defaults(ontology: Dict[str, Any]) -> str:
    defaults = ontology.get("DEFAULTS", {})
    defaults_lines = [f"{k}: {v}" for k, v in (defaults or {}).items()]
    default_currency = defaults.get("currency", "USD")
    return DEFAULTS_BLOCK_SHELL.format(
        defaults_lines=_bulleted(defaults_lines or ["(no defaults)"]),
        default_currency=default_currency,
    )


def section_extraction_note() -> str:
    return """
    --------------------------------------------------------------------------------
    STRICT POLICIES FOR EXTRACTION
    --------------------------------------------------------------------------------: 
    Return nodes with extract_nodes(nodes=[...]), edges with extract_edges(edges=[...]), and meta with extract_meta(meta=[...]).
    """


# -----------------------------------------------------------------------------
# Assembly
# -----------------------------------------------------------------------------


def assemble_prompt(
    ontology: Dict[str, Any],
    rules: Optional[List[str]] = None,
    extra_blocks: Optional[Dict[str, str]] = None,
) -> str:
    """
    Assemble the final prompt by concatenating modular sections.
    - `rules` controls optional inclusions (e.g., "BASE_CASE", "TABLE_EXTRACTION",
      "UNITS_NORMALIZATION", "GLOBAL_OBJECTS", "AACE_REFERENCE")
    - `extra_blocks` can override/paste exact text for optional blocks keys:
      TABLE_EXTRACTION_BLOCK, UNITS_NORMALIZATION_BLOCK, AACE_CLASS_REFERENCE_BLOCK
    """
    rules = [r.upper() for r in (rules or [])]
    extra_blocks = extra_blocks or {}

    # Resolve optional blocks (do not alter content)
    table_block = extra_blocks.get("TABLE_EXTRACTION_BLOCK", TABLE_EXTRACTION_BLOCK)
    units_block = extra_blocks.get(
        "UNITS_NORMALIZATION_BLOCK", UNITS_NORMALIZATION_BLOCK
    )
    aace_block = extra_blocks.get(
        "AACE_CLASS_REFERENCE_BLOCK", _json_to_str(AACE_CLASS_REFERENCE_BLOCK)
    )

    sections: List[str] = []

    # 1) Heading / Role
    sections.append(ROLE_BLOCK)

    # 2) Ontology contract (always early)
    sections.append(section_ontology_contract(ontology))

    # 3) Base Case (optional)
    if "BASE_CASE" in rules:
        sections.append(BASE_CASE_BLOCK)

    # 4) Output schema (contract)
    sections.append(OUTPUT_FORMAT_BLOCK)

    # 5) Quality Gate (hard policy)
    sections.append(section_quality_gate(ontology))

    # 6) Units normalization (optional)
    if "UNITS_NORMALIZATION" in rules:
        sections.append(units_block)

    if "COST_AND_METHOD_POLICY" in rules:
        sections.append(COST_AND_METHOD_POLICY_BLOCK)

    # 7) Synonyms and Hints (policy-bound)
    sections.append(section_synonyms(ontology))
    sections.append(section_hints(ontology))

    # 8) Patterns (policy-bound)
    sections.append(section_patterns(ontology))

    # 9) Defaults & Fallbacks (policy-bound)
    sections.append(section_defaults(ontology))

    # 10) Table Extraction (optional, after defaults to avoid clashes)
    if "TABLE_EXTRACTION" in rules:
        sections.append(table_block)

    # 11) Global Objects Summary (optional)
    if "GLOBAL_OBJECTS" in rules:
        global_objectives_block = (
            GLOBAL_OBJECTS_BLOCK
            + "\n"
            + _json_to_str(ontology.get("GLOBAL_OBJECTIVES_SPEC", {}))
        )
        sections.append(global_objectives_block)

    # 12) AACE Class Reference (optional appendix)
    if "AACE_REFERENCE" in rules:
        sections.append(aace_block)

    # 13) Compliance footer (always last policy)
    sections.append(COMPLIANCE_FOOTER_BLOCK)

    # 14) Node and Relations extraction
    sections.append(
        NODES_AND_RELATIONS_EXTRACTION_BLOCK + "\n" + HIERARCHICAL_EXTRACTION_BLOCK,
    )

    # 15) Final extraction note
    sections.append(section_extraction_note())

    # Final assembly without redundant blank lines
    text = _join_lines([s.strip("\n") for s in sections])
    # Normalize consecutive blank lines to a single blank line
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text
