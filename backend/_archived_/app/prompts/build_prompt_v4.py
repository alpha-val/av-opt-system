from typing import Dict, Any, List, Optional
from ..ontology_v2 import AACE_ESTIMATE_CLASS_DEFINITION
import json

# Try to import from new app_v2 ontology first, fallback to old
try:
    from app_v2.domain.ontology.ontology import AV_MSIO_ONTOLOGY, ENTITY_ONTOLOGY
    from app_v2.domain.ontology.ontology import get_default_ontology
    default_ontology = get_default_ontology()
    ontology_nodes_and_relations = default_ontology.get("entity_ontology", ENTITY_ONTOLOGY)
except ImportError:
    # Fallback to old ontology if app_v2 not available
    from ..ontology import load_ontology, AV_MSIO_ONTOLOGY
    ontology_nodes_and_relations = load_ontology()

# Global objectives block
global_objectives_block = """
--------------------------------------------------------------------------------
GLOBAL OBJECTIVES EXTRACTION BLOCK — TARGETING KPIs, SPECIFICATIONS & CONSTRAINTS
--------------------------------------------------------------------------------
Purpose
Extract and structure all **global-level objectives** that govern or constrain
the project’s options, design flexibility, and cost estimation. This includes
performance targets, production KPIs, constraints, operating specifications,
policies, limitations, and high-level assumptions expressed in the base case
document. All findings populate meta.global_objectives and are linked to nodes
or edges that they influence.

--------------------------------------------------------------------------------
What to extract
--------------------------------------------------------------------------------
You must identify and capture the following categories:

1. **KPIs (Key Performance Indicators)**  
   - Examples: throughput (t/h), recovery (%), availability (%), OPEX/t, power efficiency.  
   - Extract name, formula, unit, direction (“maximize” / “minimize”), target value(s).
   - Signals: “target”, “KPI”, “goal”, “objective”, “performance indicator”, “design basis”.  
   - Example: “Maintain >90% plant availability” → {"name": "Plant availability", "value": 90, "unit": "%", "direction": "maximize"}

2. **Production & Operating Specifications**  
   - Technical baseline targets: ore grade, product purity, tonnage, throughput, utilization.
   - Signals: “production rate”, “feed grade”, “product quality”, “target output”, “operating hours”.
   - Example: “Nominal throughput 10,000 t/d, design 12,000 t/d” → throughput specs with min/max.

3. **Constraints & Limits**  
   - Technical or regulatory bounds: power limit, emission cap, throughput ceiling, footprint, pressure rating, etc.
   - Signals: “shall not exceed”, “limit”, “cap”, “maximum”, “must remain below”, “minimum requirement”.
   - Output fields: name, expression (normalized inequality form), severity, rationale.

4. **Policies & Governance Directives**  
   - Organizational, environmental, or design policies:  
     “Follow ISO 14001 standards”, “Safety factor ≥ 1.5”, “Use in-house design standards”.
   - Capture as Policy or Requirement objects; link via :GOVERNED_BY or :CONSTRAINED_BY.

5. **Design or Operating Assumptions**  
   - Explicit or implicit assumptions influencing cost/scope:  
     “Continuous operation, 330 days/year”, “Power cost = $0.08/kWh”.
   - Capture name and short_description; link to affected nodes via :REFERENCES or :BASED_ON.

6. **Limitations & Exclusions**  
   - Scope or boundary conditions: “Not including site preparation”, “Limited to dry crushing”.
   - Record as Limitation entities with description and affected domain.

7. **Decision Drivers / Optimization Variables**  
   - Parameters whose variation is mentioned (e.g., grind size, reagent dosage, hours/day).
   - Capture as DecisionVariable objects: name, domain, unit, defaultValue, feasible_range.

8. **Cost or Economic Targets**  
   - Any stated financial objective or threshold (CAPEX < X MUSD, payback period < Y years).
   - Capture as CostTarget objects; link to KPI or CostItem via :TARGETS or :OPTIMIZES_FOR.

9. **Risks or Uncertainties Affecting Objectives**  
   - If explicitly tied to objectives (“subject to weather risk”, “uncertainty ±10%”), record Risk references and connect via :HAS_RISK.

--------------------------------------------------------------------------------
Extraction methodology
--------------------------------------------------------------------------------
1. **Locate statements**  
   Search narrative sections and tables for mentions of performance, production, limits, assumptions,
   cost, or policy. These are usually found in:
   - Executive summary
   - Design criteria sections
   - Basis of estimate tables
   - Operating philosophy sections
   - Permit/Regulatory summary

2. **Extract attributes**  
   For each detected item, capture:
   - name (normalized concise title)
   - category (KPI, Constraint, Policy, Assumption, etc.)
   - key_value(s): numeric or textual (split into *_value and *_unit where possible)
   - direction (“maximize”, “minimize”, “maintain”)
   - rationale (if available)
   - source (provenance fields: sourceDoc, page, tableRef)

3. **Normalize & link**
   - Apply **UNITS NORMALIZATION** (capacity, throughput, energy, etc.)
   - Use ontology node types for mapping (e.g., KPI, Constraint, Policy, Assumption).
   - Create or link supporting nodes (Equipment, Process, CostItem) through edges:
     :AFFECTS, :GOVERNED_BY, :DRIVES, :LIMITS, :SATISFIES.

4. **Provenance & confidence**
   - For every item:
       "refs": node_ids or edge_ids related
       "provenance": {sourceDoc, sourcePage?, tableRef?, extractionMethod}
       "confidence": 0.9–1.0 if direct phrase or table value; 0.6–0.8 if inferred.
   - Include original sentence or cell text as provenance.contextSnippet.

--------------------------------------------------------------------------------
Output shape
--------------------------------------------------------------------------------
Insert results into meta.global_objectives with the following structure:

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
        "policies": [...],
        "assumptions": [...],
        "limitations": [...],
        "decision_variables": [...],
        "cost_targets": [...],
        "risks": [...],
        "uncertainties": [...],
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
    },
    "scenarios": {}
        "scenarios": [
            {"name": "Baseline", "description": "Standard operating conditions", "refs": ["scenario_1"]},
            {"name": "Capex Reduction", "description": "Reduced capital expenditure scenario", "refs": ["scenario_2"]}
        ]
    }
}


--------------------------------------------------------------------------------
Success criteria
--------------------------------------------------------------------------------
✓ Each extracted global item ties to a measurable or governing objective.
✓ Each has provenance and confidence.
✓ No speculative entries or invented data.
✓ Units, constraints, and targets follow normalization policies.
✓ All extracted items appear under meta.global_objectives by category.
✓ Follow the output format strictly
"""

# Units normalization block
units_normalization_block = """
--------------------------------------------------------------------------------
= = = UNITS NORMALIZATION & DEDUPLICATION POLICY = = =
--------------------------------------------------------------------------------
Purpose
* When extracting attributes with units (e.g., "flow_rate:500 gals/hr"):
  - Parse and store the numeric value in a property called "flow_rate_value".
  - Parse and store the unit in a property called "flow_rate_unit".
  - Normalize units to a consistent format (e.g., "gallons per hour" → "gals/hr").
* Attribute policy
** Create the attribute "capacity_value" for values representing capacity
** Create the attribute "capacity_unit" for the corresponding unit.
** Keep the original attribute (e.g., "flow_rate:500 gals/hr") in the node properties for provenance.
* Deduplicate entities with equivalent normalized values and units.
* Store original text in metadata for provenance.

* Normalization rules
** Prefer SI units where sensible, but retain original in auxiliary fields if helpful.
** Map the following 
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

* Specific examples:
** 18 m³ Concrete Volume -> concrete_volume_value: 18, concrete_volume_unit: m3
** Embedment Depth: 1 m -> embedment_depth_value: 1, embedment_depth_unit: m
** Flow Rate: 500 gals/hr -> flow_rate_value: 500, flow_rate_unit: gals/hr
** Throughput: 10,000 t/d -> throughput_value: 10000, throughput_unit: tons/day
** Power: 150 kW -> power_value: 150, power_unit: kW
** Capacity: 250 TPH -> capacity_value: 250, capacity_unit: tons/hr
** for primary units and capacity, ALSO map to "capacity_value" and "capacity_unit"
*** E.g., flow rate 500 gals/hr -> flow_rate_value: 500, flow_rate_unit: gals/hr, capacity_value: 500, capacity_unit: gals/hr

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

# Table extraction block
table_extraction_block = """
--------------------------------------------------------------------------------
= = = TABLE EXTRACTION = = =
--------------------------------------------------------------------------------
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

# Nodes and relations extraction block
nodes_and_relations_extraction_directives = """
    --------------------------------------------------------------------------------
    = = = NODES AND RELATIONS EXTRACTION = = =
    --------------------------------------------------------------------------------
    NODES AND RELATIONS EXTRACTION:
    Using ontology.NODE_TYPES and ontology.EDGE_TYPES, extract all nodes and their relationships
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
    Allowed node types (ontology.NODE_TYPES): See ontology contract for details.

    Allowed edge types (ontology.EDGE_TYPES): See ontology contract for details.

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
    - MSIO ontology metadata MUST include:
        • Discipline, Category, and Subcategory attributes and their values
        • See the example for an illustration of required properties
    - "name": human-readable name (string)

    Edge object (each item in extract_edges.edges) MUST have:
    - "source": node id
    - "target": node id
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
        • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
        • any domain attributes the ontology expects for that edge (if any)

    EXAMPLES:
    - Node example: {ontology.get("NODE_PROP_EXAMPLE", "{}")}
    - Edge example: {ontology.get("EDGE_PROP_EXAMPLE", "{}")}


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
    - For node properties include MSIO ontology metadata (Discipline, Category, Subcategory).
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

    --------------------------------------------------------------------------------
    OUTPUT (STRICT JSON SHAPE)
    --------------------------------------------------------------------------------
    Emit one JSON object with these top-level keys only: nodes, edges, meta.

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

    - meta: {{
        "ontology_version": "simple-json-v1",
        "policy": {{
        "element_split_on_slash": true
        }},
        "extraction_date": "YYYY-MM-DD",
    }}

    --------------------------------------------------------------------------------
    EXAMPLES (SCHEMATIC)
    --------------------------------------------------------------------------------
    Input snippet:
    “Two base pump units (centrifugal) sized for 500 gpm at 120 ft head with
    mechanical seals. Vendor datasheet attached.”

    Classification:
        Discipline: Mechanical Equipment
        Category: Pumps
        Subcategory: Centrifugal
        Entity: Base pump unit

    Node (sketch):[
        {{
        "id": "mech_pump_001",
        "type": "OntologyItem",
        "properties": {{
            "discipline": "Mechanical Equipment",
            "category": "Pumps",
            "subcategory": "Centrifugal",
            "entity": "Base pump unit",
            "design_flowrate_value": 500,
            "design_flowrate_unit": "gpm",
            "capacity": "120 ft head",
            "capacity_value": 120,
            "capacity_unit": "ft",
            "seal_type": "mechanical",
            "evidence_text": "...500 gpm at 120 ft head with mechanical seals..."
            "confidence": 0.92
        }}
    }}, ...]
    Edges:
    [
        {{
            "source":"mech_pump_001",
            "target":"subcat_centrifugal",
            "type":"PART_OF",
            "properties":
            {{
                "confidence":1.0,
                "evidence_text": "...500 gpm at 120 ft head with mechanical seals..."
            }}
        }},
        ...
    ]
"""

# Scenario extraction
scenario_extraction_block = """
--------------------------------------------------------------------------------
SCENARIO EXTRACTOR — GENERIC TEMPLATE FOR BASE CASE ➜ SCENARIO VARIANTS
--------------------------------------------------------------------------------

GOAL
You are an expert process engineer & cost estimator.
Extract, normalize, and templatize the following two classes of scenarios from
a given base case technical or cost report. These templates will later serve
as structured blueprints for generating scenario options and running cost or
production analyses.

--------------------------------------------------------------------------------
SCENARIO TYPES TO EXTRACT
--------------------------------------------------------------------------------
1. PRODUCTION CHANGE SCENARIO
   - Description: Any scenario that modifies production rate, throughput,
     output quantity, or system capacity (e.g., “increase production by 8%”).
   - Change direction: increase or decrease
   - Unit or percent-based: %, tpd, gpm, tons/hr, units/day, etc.
   - Expected outcome: new flow rate, capacity, or output level.

   Required extraction fields:
   - Affected systems/equipment (e.g., pumps, tanks, conveyors, circuits)
   - Process dependencies (bottlenecks, throughput-limiting steps)
   - Feasible engineering options (e.g., increase equipment size,
     debottleneck, reconfigure, add parallel train)
   - Associated constraints (e.g., power availability, structural limits)
   - Material or control implications (instrumentation, automation changes)
   - Cost and risk implications (estimated CAPEX/OPEX shifts, quality impact)
   - Applicable codes/standards, if modified (e.g., ASME, API, ISA)

2. CAPEX CHANGE SCENARIO
   - Description: Any scenario that modifies total installed cost or capital
     expenditure (e.g., “reduce Capex by 5%” or “increase Capex to enable
     future capacity expansion”).
   - Change direction: increase or decrease
   - Unit or percent-based: $, %, or absolute change.

   Required extraction fields:
   - Major cost drivers (equipment, materials, civil, electrical, labor)
   - Subsystems or components influencing CAPEX sensitivity
   - Possible cost-reduction levers (material downgrade, modularization,
     vendor selection, process simplification, deferred scope)
   - Quality, reliability, or safety trade-offs from cost reduction
   - Risk notes (e.g., supply chain volatility, performance uncertainty)
   - Policy or procurement constraints (codes, standards, local sourcing)
   - Recommended estimation methods or scaling rules (e.g., cost exponent)


--------------------------------------------------------------------------------
INPUTS
--------------------------------------------------------------------------------
1) BASE CASE TEXT: see below

2) SCENARIO REQUEST:
   {
     "goal": ["Increase production"] | ["Reduce Capex"],
     "change_type": ["Equipment","Material","Quality","Quantity"],
     "description": "Increase production by 8%" | "Reduce Capex by 5%"
   }

3) ONTOLOGY
Use ontology terms to classify and standardize all extracted
entities, parameters, relationships, and cost roles.

--------------------------------------------------------------------------------
QUALITY & STYLE
--------------------------------------------------------------------------------
- Be concise, specific, and quantitative.
- Keep terms consistent with ontology (if provided).
- Use SI/US units exactly as in the base case; include units on all numeric values.
- Use explicit references to section headers, tables, or page anchors (e.g., "§2 Major Equipment").
- Avoid narrative or commentary outside the JSON.
- Do not include emojis or special characters.

--------------------------------------------------------------------------------
OUTPUT — STRICT JSON FORMAT
--------------------------------------------------------------------------------
Return a single JSON object with the key `"scenarios"` containing one or more scenario templates.
Each scenario MUST conform to the following schema:

{
  "scenarios": [
    {
      "scenario_template": "Production Change | Capex Change",
      "scenario_header": {
        "scenario_uid": "",
        "target": "<e.g., Increase Production>",
        "change_type": ["Equipment","Material","Quality","Quantity"],
        "description": "<free text summary>",
        "confidence": 0.0,
        "related_sections": ["§2 Major Equipment", "§3 Design Criteria"],
        "scenario_summary": "<-- summary of the base case text relevant to this scenario; include as much detail as possible; limit the length to 3000 words; -->"
      },

      "relevant_entities": [
        {
          "entity_name": "<-- Pump, Tank, System -->",
          "entity_type": "Equipment | Process | Material | Control | Civil | Electrical | Other",
          "base_values": [{"key": "flow_rate", "value": "100", "units": "gpm", "discipline": "Piping", "category": "Hydraulic", "subcategory": "Flow Rate"}],
          "proposed_modifications": [
            {"parameter": "flow_rate", "change": "increase", "suggested_value": "108", "units": "gpm", "discipline": "Piping", "category": "Hydraulic", "subcategory": "Flow Rate"}
          ],
          "expected_impacts": {
            "capex": {"direction": "increase", "magnitude_note": "+5%"},
            "opex": {"direction": "increase", "magnitude_note": "+2%"}
          },
          "evidence": ["§2 Major Equipment <-- include relevant excerpts from the base case text that support this entity extraction -->"]
          "rationale": "<-- explain why this entity is relevant to the scenario; include as much detail as possible; limit the length to 1000 words; -->"
        }
      ],
    }
  ]
}

--------------------------------------------------------------------------------
STRICT REQUIREMENTS
--------------------------------------------------------------------------------
- Output MUST be valid JSON with a top-level key `"scenarios"`.
- Be as prescriptive and detailed as possible in the scenario_summary and rationale fields.
- The goal is to extract relevant entities that would be modified or impacted
  by the scenario request. After which, these entities will be used to generate
  detailed scenario and cost options in subsequent steps.
- Assess all possible changes and impacts from the scenario request. E.g., "Equipment", "Material", "Process", "Quality", "Quantity", etc.
- Important: FIND ALL POSSIBLE relevant entities in the base case text.
--------------------------------------------------------------------------------

""".strip()

# Provenance and Confidence block
prov_conf_block = """
    Provenance & Confidence extraction rules:
    - Include evidence: sourceDoc, sourcePage?, table_ref? (tableId,rowIndex,colIndex),
        evidence_text (≤200 chars).
    - Confidence scale:
        0.9–1.0 direct match + attributes present
        0.7–0.9 direct match w/ partial attributes or minor synonym use
        0.5–0.7 good subcategory match but Entity inferred
        <0.5 omit
"""

# Summary extraction block
# PROMPT_DISCIPLINE_STRUCTURED_SUMMARY = """
# --------------------------------------------------------------------------------
# ONTOLOGY-ALIGNED FAITHFUL SUMMARY GENERATION — ALPHA-VAL MINING CONTEXT
# --------------------------------------------------------------------------------
# Goal
# Create a **comprehensive, structured summary** of the supplied Base Case or project
# document, aligned with the AV_MSIO_ONTOLOGY disciplines.

# This summary must preserve every salient piece of information required to recreate the
# document’s content and context — including engineering workflows, systems,
# equipment specifications, materials, design parameters, operational constraints,
# policies, assumptions, and cost factors — **organized by discipline**.

# --------------------------------------------------------------------------------
# INSTRUCTIONS
# --------------------------------------------------------------------------------
# For each discipline listed below, extract and summarize **all** relevant content from the
# document. If a discipline is not mentioned, explicitly state “No information found.”

# Each discipline section should contain subsections for:
# - Overview / Role in Project
# - Key Workflows and Systems
# - Equipment and Entities (include specs, type, capacity, duty, vendor if available)
# - Materials and Consumables
# - Design Parameters and Constraints
# - Policies, Standards, and QA/QC
# - Objectives, KPIs, and Targets
# - Risks, Assumptions, and Data Gaps
# - Interdependencies with other disciplines

# --------------------------------------------------------------------------------
# DISCIPLINES (as defined in ALPHA-VAL-MINING-STRUCTURED-INDUSTRIAL-ONTOLOGY)
# --------------------------------------------------------------------------------
# 1. Mechanical Equipment
#    - Pumps (Centrifugal, Positive Displacement)
#    - Vessels (Reactors, Separators)
#    - Tanks (Fixed, Floating Roof)
#    - Heat Exchangers (Shell-and-tube)
#    - Compressors/Blowers (Centrifugal/Turbo)
#    - Material Handling (Belt, Screw)
#    - Utilities (Cooling Tower)
#    - Specialty (Agitators)
#    - Process Equipment (Grinding Mills)

# 2. Civil
#    - Site Works (Grading)
#    - Access (Roads, Paving)
#    - Stormwater (Retention, Channels)
#    - Utilities – Site (Duct banks)
#    - Hydrology (Culverts/Drainage)
#    - Survey (Topography)

# 3. Structural
#    - Steelwork (Platforms, Walkways)
#    - Pipe Supports (Racks)
#    - Buildings (Control Room, MCC)
#    - Foundations Interface (Embed Plates)

# 4. Concrete
#    - Foundations (Footings)
#    - Slabs (Slab on Grade)
#    - Retaining (Walls)
#    - Precast (Manholes)

# 5. Piping
#    - Process Lines (Large Bore, Small Bore)
#    - Materials (CS/SS/HDPE/FRP)
#    - Insulation (Heat Tracing)
#    - Testing (Hydrotest, Pneumatic)

# 6. Instrumentation
#    - Flow/Level (Flow Meters)
#    - Temperature & Pressure (Transmitters)
#    - Analyzers & Safety (Gas Detectors, pH)
#    - Cabling & Termination (Junction Boxes)

# 7. Control
#    - Control Systems (PLC/DCS/SCADA)
#    - Interfaces (HMI, Historian)
#    - Network & Cyber (Firewalls, Switches)
#    - I/O (Remote Panels)

# 8. Electrical
#    - Distribution (Transformers)
#    - Switchgear (MCC/SWGR)
#    - Cabling (Power & Control Cables)

# 9. Safety/Environment
#    - Fire Protection (Sprinklers, Hydrants)
#    - Containment (Bunds)
#    - Ventilation (Dust Extraction, Ducting)

# 10. Utilities
#     - Compressed Air (Network)
#     - Cooling Water (Pumps, Heat Exchangers)

# 11. Construction/Commissioning
#     - QA/QC (Inspections, Testing)
#     - Commissioning (Pre-startup Safety Reviews)

# 12. Costs & Economics
#     - Capex (Direct, Indirect)
#     - Opex
#     - Contingency

# 13. Process / Workflow / Operations
#     - Process Flow (Diagrams)
#     - Operational Steps
#     - Maintenance Procedures
    
# --------------------------------------------------------------------------------
# OUTPUT REQUIREMENTS
# --------------------------------------------------------------------------------
# Return your summary as a **single structured text block** formatted as
# Markdown-style headings. Example structure:

# # Project Overview
# ## Mechanical Equipment
# ### Pumps
# - Key equipment, capacity, vendor, duties
# - Constraints, operating ranges, materials
# ### Heat Exchangers
# - Type, duty, assumptions, interdependencies
# ...

# Ensure:
# - Explicit mention of missing data (e.g., “No mention of compressors”)
# - Inclusion of all numeric, parametric, or constraint details (e.g., “Flowrate: 300 m³/h”)
# - Capture of all assumptions, uncertainties, and cost linkages
# - Preservation of technical context (why, how, dependencies)
# - Capture details of processes, workflows, and operational procedures
# - Aim for detailed completeness over brevity

# --------------------------------------------------------------------------------
# FINAL OUTPUT
# --------------------------------------------------------------------------------
# Call the `extract_structured_report` tool with:
# - `structured_summary`: your full ontology-aligned summary text
# --------------------------------------------------------------------------------
# """

PROMPT_DISCIPLINE_STRUCTURED_SUMMARY = """
--------------------------------------------------------------------------------
SYSTEM PROMPT — EXHAUSTIVE BASE CASE EXTRACTION & STRUCTURED RECONSTRUCTION
--------------------------------------------------------------------------------
ROLE
You are an expert process engineer & cost estimator.
Extract, normalize, and structure all technical, cost, and policy information
from a base case engineering report into a compact but complete JSON
representation that serves as the digital “truth source” for the report.

OBJECTIVE
Faithfully reconstruct the base case report, including:
- All sections and subsections
- Process flows and control logic
- Equipment and materials with specifications
- Instrumentation and controls
- Environmental and site data
- Codes, standards, and governing policies
- Cost tables, assumptions, contingencies, exclusions
- Constraints, limitations, risks/uncertainties
- Provenance and coverage checks

In addition to structured fields, provide a **descriptive_text (250–500 words)**
for each top-level domain and for each item in `"sections"`, using only content
from the report. Descriptive text must be comprehensive and anchored, but must
not introduce new facts. It can quote short fragments (≤40 words each) where
helpful.

INPUTS
1) BASE_CASE_TEXT: <<FULL TEXT OF REPORT>>
2) ONTOLOGY (required):
   {
     "NODE_TYPES": [
       "Equipment","Material","Process","Control","Instrument",
       "Civil","Electrical","CostItem","CostRule","Policy","Assumption","Constraint"
     ],
     "EDGE_TYPES": ["HAS_PART","FEEDS","CONTROLS","CONSUMES","LOCATED_IN","GOVERNS"],
     "AV_MSIO_ONTOLOGY": "Mapping of Discipline, Category, Subcategory, Entity, Attributes, Notes"
   }

EXTRACTION POLICY
1) Exhaustiveness
   - Capture every measurable, referable, or categorical fact.
   - Include all numeric values and units exactly as written (no conversion/rounding).
   - Extract table rows, list items, design criteria, codes, assumptions, exclusions, etc.
   - Each object must carry at least one anchor (e.g., "§2", "p.4", "Table 1").

2) Descriptive Text (250–500 words per section/domain)
   - Provide `"descriptive_text"` for:
     • Each entry in `"sections"` (its own subsection narrative).
     • Each top-level domain: process_flows, design_criteria, equipment,
       materials, instrumentation_controls, site_data, codes_standards,
       policies_recommendations, constraints, costs, risks_uncertainties.
   - Use only information present in the report; do not invent.
   - You may include short quotes ≤40 words with anchors to capture exact phrasing.

3) Missing Data & Fidelity
   - If data are implied/missing → set value = null and add an item in
     `"risks_uncertainties"` with a remediation action.
   - Preserve original symbols and qualifiers (“~”, “@ 80%”, “±”, “nameplate”).

4) Output Discipline
   - Strict JSON only. No text outside JSON.
   - All arrays present (use [] if empty).

OUTPUT — STRICT JSON FORMAT
Return one object with top-level key `"base_case_extract"`:

{
  "base_case_extract": {
    "doc_header": { ... },

    "sections": [
      {
        "name": "<exact header>",
        "anchor": "<§ / page>",
        "subsections": [...],
        "descriptive_text": "<250–500 words drawn from this section only, with anchors>"
      }
    ],

    "process_flows": {
      "basis": {...},
      "streams": [...],
      "control_strategy": [...],
      "descriptive_text": "<250–500 words: overall flow/controls narrative with anchors>"
    },

    "design_criteria": {
      "process": [...],
      "mechanical": [...],
      "environmental_loads": [...],
      "assumptions": [...],
      "descriptive_text": "<250–500 words: criteria/basis narrative with anchors>"
    },

    "equipment": [
      {
        "items": [
          {
            "name": "Storage Tank",
            "type": "Equipment",
            "quantity": "1",
            "specs": [
              {"key": "capacity", "value": "1,000", "units": "gal @ 80%"},
              {"key": "gross_volume", "value": "1,250", "units": "gal"}
            ],
            "materials": [
              {"component": "shell", "material": "stainless steel", "grade": "304"}
            ],
            "notes": "Vertical atmospheric tank",
            "anchors": ["§2"]
          },
          {
            "name": "Pump + Motor",
            "type": "Equipment",
            "quantity": "1",
            "specs": [{"key": "power", "value": "10", "units": "hp"}],
            "materials": [],
            "notes": null,
            "anchors": ["§2"]
          }
        ],
        "descriptive_text": "<250–500 words: equipment/system narrative with anchors>"
      }
    ],

    "materials": [
      {
        "items": [
          {
            "name": "Water",
            "specs": [{"key": "quality", "value": "clean", "units": ""}],
            "compatibility_notes": "Suitable for stainless steel contact surfaces.",
            "anchors": ["§3"]
          }
        ],
        "descriptive_text": "<250–500 words: materials/compatibility narrative with anchors>"
      }
    ],

    "instrumentation_controls": [
      {
        "items": [
          {
            "tag": "LT-001",
            "type": "Level Transmitter",
            "service": "Tank Level Monitoring",
            "setpoints": [{"key": "SP", "value": "80", "units": "%"}],
            "interlocks": ["LL alarm → pump stop"],
            "io_notes": "4-20mA loop, panel display",
            "anchors": ["§3"]
          }
        ],
        "descriptive_text": "<250–500 words: instrumentation/control logic narrative>"
      }
    ],

    "site_data": [
      {
        "items": [
          {"key": "elevation", "value": "760", "units": "ft", "anchors": ["§4"]},
          {"key": "seismic_category", "value": "A", "units": "", "anchors": ["§4"]}
        ],
        "descriptive_text": "<250–500 words: site/geotechnical/environmental conditions narrative>"
      }
    ],

    "codes_standards": [
      {
        "items": [
          {"domain": "Structural", "standard": "ASCE 7-16", "anchors": ["§5"]},
          {"domain": "Process Piping", "standard": "ASME B31.3", "anchors": ["§5"]}
        ],
        "descriptive_text": "<250–500 words: codes and standards application narrative>"
      }
    ],

    "policies_recommendations": [
      {
        "items": [
          {
            "type": "Policy",
            "text": "Follow NCBC 2018 for structural design.",
            "anchors": ["§5"]
          },
          {
            "type": "Recommendation",
            "text": "Provide low-level interlock to protect pump.",
            "anchors": ["§3"]
          }
        ],
        "descriptive_text": "<250–500 words: policy/recommendation context and rationale>"
      }
    ],

    "constraints": [
      {
        "items": [
          {
            "type": "Physical",
            "constraint": "Tank must remain atmospheric.",
            "anchors": ["§3"]
          }
        ],
        "descriptive_text": "<250–500 words: constraints, limitations, and boundary conditions>"
      }
    ],

    "costs": [
      {
        "items": {
          "design_basis": [...],
          "line_items": [...],
          "subtotals": [...],
          "installed_total": {...},
          "assumptions": [...],
          "exclusions": [...],
          "sources_refs": [...],
          "sensitivities": [...],
          "planning_alternatives": [...]
        },
        "descriptive_text": "<250–500 words: cost estimate basis, assumptions, and sensitivity notes>"
      }
    ],

    "risks_uncertainties": [
      {
        "items": [
          {
            "gap": "TDH not provided",
            "impact": "High",
            "action": "Perform hydraulic calc",
            "anchors": ["§7"]
          }
        ],
        "descriptive_text": "<250–500 words: risks, uncertainties, and mitigation measures>"
      }
    ],

    "provenance": {
      "extraction_method": "LLM structured parse",
      "version": "v1",
      "notes": "All values anchored to report; units preserved.",
      "coverage_check": {
        "counts": {...},
        "missing": [...]
      }
    }
  }
}
--------------------------------------------------------------------------------

STRICTNESS
- Valid JSON; no text outside JSON.
- Every domain listed above must include a 250–500 word descriptive_text
  (or domain-specific *_descriptive_text) even if underlying arrays are empty.
- Quotes ≤40 words each; include anchors for quoted or pivotal statements.
- Do not introduce new facts; descriptive_text must be faithful to the report.
--------------------------------------------------------------------------------
END
--------------------------------------------------------------------------------
"""

# Load MSIO ontology
MSIO_ONTOLOGY_TEXT = json.dumps(AV_MSIO_ONTOLOGY, indent=1)


def build_prompt_v4(rules: Optional[List[str]] = None) -> str:
    """Builds a prompt for base-case extraction with a simple ontology mapper."""

    # Ontology mapping block
    ontology_mapping_block = f"""\
    --------------------------------------------------------------------------------
    ONTOLOGY REFERENCE (INLINE, SOURCE OF TRUTH)
    --------------------------------------------------------------------------------
    Map each entity (nodes) to this hierarchical ontology:
    - Discipline → Category → Subcategory → Entity

  Ontology:
  {MSIO_ONTOLOGY_TEXT}

    --------------------------------------------------------------------------------
    MATCHING & CLASSIFICATION RULES
    --------------------------------------------------------------------------------
    1) Match Scope
    - A mention in the report maps to exactly one ontology data above (Discipline,
        Category, Subcategory, Entity). Prefer the most specific match (Entity).
    - If the report uses synonyms (e.g., “float roof” vs “Float Roof”), normalize
        via case-insensitive matching and simple singular/plural folding.

    2) Exactness & Fallback
    - Try full 4-tuple match (Discipline, Category, Subcategory, Entity).
    - If Entity is ambiguous/missing, back off to Subcategory (keep searching
        for the best Entity within that Subcategory using nearby cues/attributes).
    - If still ambiguous, return the top-2 candidates with lower confidence.

    3) Attribute Extraction
    - For a matched ontology row, parse the listed Attributes from the local
        context (sentence/table row). Extract numbers and units where present.
    - Create normalized fields from attribute labels using snake_case and
        value/unit splitting where sensible (e.g., “Design flowrate” →
        design_flowrate_value, design_flowrate_unit).
    - Preserve the original text snippet as evidence_text.
        
    4) Matching is case-insensitive.
      
  Examples:
    - "Concrete" -> {{"Discipline": "Materials", "Category": "Concrete", "Subcategory": "Reinforced Concrete", "Entity": "Reinforced Concrete"}}
    - "Stainless steel tank" -> {{"Discipline": "Equipment", "Category": "Storage Tanks", "Subcategory": "Metal Tanks", "Entity": "Stainless Steel Tank"}}
    - Process:"Engineering & procurement" -> {{"Discipline": "Project Management", "Category": "Engineering", "Subcategory": "Engineering & Procurement", "Entity": "Engineering & Procurement"}}
    - Scenario:"Low-cost Budget" -> {{"Discipline": "Scenarios", "Category": "Budget Scenarios", "Subcategory": "Low-cost Budget", "Entity": "Low-cost Budget"}}

    """

    # Node and Relations extraction block (no edits)
    nodes_and_relations_extraction_block = f"""\
        --------------------------------------------------------------------------------
        NODES AND RELATIONS TYPES
        --------------------------------------------------------------------------------
        Emit one JSON object with these top-level keys only: nodes, edges, meta.
        {ontology_nodes_and_relations.get("NODE_TYPES", "")}
        {ontology_nodes_and_relations.get("EDGE_TYPES", "")}

        {nodes_and_relations_extraction_directives}
    """

    prompt = f"""\
    --------------------------------------------------------------------------------
    BASE-CASE EXTRACTION
    --------------------------------------------------------------------------------

    ROLE
    Produce a clean, deduplicated knowledge graph for mining/process-engineering content
    aligned exactly to the configured ontology. You read a base-case report (text/tables)
    and extract entities that match a simple hierarchical catalog (Discipline → Category → Subcategory → Entity). 
    You then emit a single JSON object with nodes and edges, plus evidence and confidence.

    Required output:
    --------------------------------------------------------------------------------
    # ONTOLOGY
    {ontology_mapping_block if "MSIO_ONTOLOGY" in (rules or []) else ""}
    
    # NODES & RELATIONS EXTRACTION RULES
    {nodes_and_relations_extraction_block if "NODES_AND_RELATIONS" in (rules or []) else ""}

    # PROVENANCE & CONFIDENCE
    {prov_conf_block if "PROVENANCE_AND_CONFIDENCE" in (rules or []) else ""}
   
    # UNIT NORMALIZATION & DEDUPLICATION
    {units_normalization_block if "UNITS_NORMALIZATION" in (rules or []) else ""}
    --------------------------------------------------------------------------------

    Optional:
    --------------------------------------------------------------------------------
    # TABLE EXTRACTION RULES
    {table_extraction_block if "TABLE_EXTRACTION" in (rules or []) else ""}

    # SCENARIO EXTRACTION RULES
    {scenario_extraction_block if "SCENARIO_EXTRACTION" in (rules or []) else ""}

    # GLOBAL OBJECTIVES
    {global_objectives_block if "GLOBAL_OBJECTIVES" in (rules or []) else ""}
    --------------------------------------------------------------------------------
    
    # SUMMARY EXTRACTION
    {PROMPT_DISCIPLINE_STRUCTURED_SUMMARY if "STRUCTURED_REPORT" in (rules or []) else ""}
    
    --------------------------------------------------------------------------------
    DO / DO NOT
    --------------------------------------------------------------------------------
    ✓ Do: map each mention to the most specific ontology Entity available.
    ✓ Do: split only the Entity field on “/” when classifying ontology rows.
    ✓ Do: extract attributes near the mention; split number/unit when clear.
    ✓ Do: explicitly map extracted nodes and edges to ontology types via their properties.
    ✓ Do: extract structured report if requested.
    
    ✗ Don’t: invent elements or attributes not evidenced in the text/table.
    ✗ Don’t: split on “/” in other fields (Subcategory, Category, Discipline).
    
    --------------------------------------------------------------------------------
    FINAL DELIVERABLE
    --------------------------------------------------------------------------------
    Return nodes with extract_nodes(nodes=[...]), edges with extract_edges(edges=[...]), 
    scenarios with extract_scenarios(scenarios=[...]), and extract structured report with extract_structured_report(base_case_report={...}) as per the output contract.
    """

    return prompt
