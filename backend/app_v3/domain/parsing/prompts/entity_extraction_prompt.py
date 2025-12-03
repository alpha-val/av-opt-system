from typing import Dict, Any, List, Optional
import json

# Import from app_v3 ontology
from ...ontology.ontology import AV_MSIO_ONTOLOGY, ENTITY_ONTOLOGY, get_default_ontology
from ...ontology.loader import get_ontology as get_ontology_instance

# Get ontology instance and convert to dict format for compatibility
default_ontology = get_default_ontology()
ontology_instance = get_ontology_instance()
entity_ont = ontology_instance.entity_ontology

# Convert EntityOntology to dict format expected by prompts
ontology_nodes_and_relations = {
    "NODE_TYPES": entity_ont.node_types,
    "EDGE_TYPES": entity_ont.edge_types,
    "NODE_PROPERTIES": entity_ont.node_properties,
    "EDGE_PROPERTIES": entity_ont.edge_properties,
    "NODE_DESCRIPTIONS": entity_ont.node_descriptions,
    "EDGE_DESCRIPTIONS": entity_ont.edge_descriptions,
    "NODE_PROP_EXAMPLES": entity_ont.node_prop_examples,
    "EDGE_PROP_EXAMPLES": entity_ont.edge_prop_examples,
}

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
  UNITS NORMALIZATION BLOCK
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

  * Parsing
  ** Deconstruct numbers and units into separate properties
  E.g., "100 kg" -> "value": 100, "unit": "kg"
  ** Handle ranges by splitting into min and max values
  E.g., "10-20 kg" -> "value_min": 10, "value_max": 20, "unit": "kg"
  E.g., "$160-$200" -> "value_min": 160, "value_max": 200, "unit": "$"
  ** Interpret currency values appropriately
  E.g., "$230k" -> "value": 230000, "unit": "$"
  E.g., "£120k" -> "value": 120000, "unit": "£"
  E.g., "€120k" -> "value": 120000, "unit": "€"
  E.g., "¥120k" -> "value": 120000, "unit": "¥"
  E.g., "₹120k" -> "value": 120000, "unit": "₹"
  ** Interpret currency amounts appropriately
  E.g., "$100k" -> "value": 100000, "unit": "$"
  E.g., "$2.1M" -> "value": 2100000, "unit": "$"
  ** Handle compound values by splitting into value and condition
  E.g., "100 kg @ 80%" -> "value": 100, "unit": "kg", "condition": "80%"
  E.g., "100 kg @ 80% - $100k" -> "value": 100, "unit": "kg", "condition": "80%", "cost": 100000, "unit": "$"
  ** Handle percentage values appropriately
  E.g., "80%" -> "value": 80, "unit": "%"
  E.g., "80% - $100k" -> "value": 80, "unit": "%", "cost": 100000, "unit": "$"

  """

# Table extraction block
table_extraction_block = """
  --------------------------------------------------------------------------------
  TABLE EXTRACTION BLOCK
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

# Deduplication block
entity_deduplication_block = """
    --------------------------------------------------------------------------------
    ENTITY DEDUPLICATION AND MERGING BLOCK
    --------------------------------------------------------------------------------
    PURPOSE:
    Prevent duplicate nodes by merging entities that represent the same physical/logical
    entity across multiple text chunks or mentions with alternative units.

    DEDUPLICATION CRITERIA:
    Two entities are considered DUPLICATES if ALL of the following match:
    1. **MSIO Classification Match** (MANDATORY):
       - Same discipline (case-insensitive)
       - Same category (case-insensitive)
       - Same subcategory (case-insensitive)
       - Same entity (case-insensitive)
    
    2. **Entity Name Similarity** (MANDATORY):
       - Exact match (case-insensitive), OR
       - High semantic similarity (e.g., "Salt Slurry System" vs "Salt Slurry Process")
       - Ignore minor variations in wording
    
    3. **Attribute Overlap** (at least 60% of attributes match):
       - Compare attribute names and values
       - If same attribute has different values, check if they are unit conversions
       - If values differ but units are convertible (e.g., GPM vs gal/hr), treat as same entity

    MERGING STRATEGY:
    When duplicates are detected, merge them into a SINGLE node using this strategy:

    1. **Preserve All Information**:
       - Keep the most specific/complete name
       - Retain the highest confidence score
       - Merge all evidence_text snippets (concatenate or pick best)
    
    2. **Handle Alternative Units**:
       - When the same attribute appears with different units (e.g., flow_rate: 3733 GPM and 223975 gal/hr):
         * Store BOTH as separate attribute objects in the attributes array
         * Use descriptive names: "flow_rate_gpm" and "flow_rate_gal_per_hr"
         * OR keep both in the attributes array with their respective units
       - Example:
         ```json
         "attributes": [
           {
             "name": "flow_rate",
             "value": 3733,
             "unit": "GPM",
             "evidence_text": "3,733 GPM",
             "confidence": 0.95
           },
           {
             "name": "flow_rate",
             "value": 223975,
             "unit": "gal/hr",
             "evidence_text": "≈223,975 gal/hr",
             "confidence": 0.95
           }
         ]
         ```
    
    3. **Consolidate Attributes**:
       - Merge attributes from all duplicate mentions
       - For same attribute with same units: keep the most confident/complete value
       - For different attributes: add all to the merged node
       - Preserve all evidence_text for provenance
    
    4. **Merge Properties**:
       - Combine all properties from duplicate nodes
       - For conflicting values: prefer more specific/confident source
       - Keep all non-null values
    
    5. **Update Edges**:
       - Redirect all edges pointing to duplicate nodes to point to the merged node
       - Remove duplicate edges (same source, target, type)

    DEDUPLICATION WORKFLOW:
    1. Extract all entities first following normal extraction rules
    2. Group entities by MSIO classification (discipline/category/subcategory/entity)
    3. Within each group, identify entities with similar names and overlapping attributes
    4. Apply merging strategy to consolidate duplicates
    5. Update all edge references to merged nodes
    6. Return deduplicated node list

    EXAMPLES:

    Example 1: Alternative Units (Same Entity, Different Units)
    Input mentions:
    - "Throughput: 100 short tons/hr"
    - "200,000 lb/hr dry table salt"
    - "Volumetric flow: ≈223,975 gal/hr ≈ 3,733 GPM"
    
    Detected duplicates:
    - All refer to "Salt Slurry Process" (same MSIO classification)
    - Same entity, different attribute representations
    
    Merged output (SINGLE NODE):
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",  // MUST be a valid UUID
      "type": "Process",
      "properties": {
        "name": "Salt Slurry Process",
        "discipline": "Process Engineering",
        "category": "Slurry Processing",
        "subcategory": "Mixing",
        "entity": "Salt Slurry System",
        "attributes": [
          {
            "name": "slurry_concentration",
            "value": 10,
            "unit": "% mass",
            "evidence_text": "10% (w/w) salt slurry",
            "confidence": 0.95
          },
          {
            "name": "feed_rate",
            "value": 100,
            "unit": "st/hr",
            "evidence_text": "100 short tons/hr",
            "confidence": 0.95
          },
          {
            "name": "feed_rate",
            "value": 200000,
            "unit": "lb/hr",
            "evidence_text": "200,000 lb/hr dry table salt",
            "confidence": 0.95
          },
          {
            "name": "flow_rate",
            "value": 223975,
            "unit": "gal/hr",
            "evidence_text": "≈223,975 gal/hr",
            "confidence": 0.93
          },
          {
            "name": "flow_rate",
            "value": 3733,
            "unit": "GPM",
            "evidence_text": "≈ 3,733 GPM",
            "confidence": 0.93
          }
        ],
        "evidence_text": "Salt + Water Suspension System — 10% (w/w) salt slurry. Throughput: 100 short tons/hr (200,000 lb/hr). Volumetric flow: ≈223,975 gal/hr ≈ 3,733 GPM.",
        "confidence": 0.94
      }
    }
    ```

    Example 2: Cross-Chunk Consolidation
    Chunk 1: "Centrifugal pump rated for 500 GPM"
    Chunk 2: "The pump has a 10 HP motor and mechanical seal"
    
    Detected duplicates:
    - Both refer to same pump (same MSIO: Mechanical Equipment/Pumps/Centrifugal)
    
    Merged output (SINGLE NODE):
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",  // MUST be a valid UUID
      "type": "Equipment",
      "properties": {
        "name": "Centrifugal Pump",
        "discipline": "Mechanical Equipment",
        "category": "Pumps",
        "subcategory": "Centrifugal",
        "entity": "Base pump unit",
        "attributes": [
          {
            "name": "Design flowrate",
            "value": 500,
            "unit": "GPM",
            "evidence_text": "rated for 500 GPM",
            "confidence": 0.95
          },
          {
            "name": "Power",
            "value": 10,
            "unit": "HP",
            "evidence_text": "10 HP motor",
            "confidence": 0.95
          }
        ],
        "seal_type": "mechanical",
        "evidence_text": "Centrifugal pump rated for 500 GPM. The pump has a 10 HP motor and mechanical seal",
        "confidence": 0.94
      }
    }
    ```

    QUALITY REQUIREMENTS:
    ✓ Merge all duplicate entities into single nodes
    ✓ Preserve all information from all mentions
    ✓ Store alternative units as separate attribute entries
    ✓ Consolidate evidence from multiple chunks
    ✓ Update all edge references to merged nodes
    ✓ Maintain highest confidence scores
    ✗ Do NOT create multiple nodes for the same entity
    ✗ Do NOT lose information when merging
    ✗ Do NOT convert units (store both original units)
    ✗ Do NOT merge entities with different MSIO classifications
"""

# Nodes and relations extraction block
nodes_and_relations_extraction_directives_v0 = """
    --------------------------------------------------------------------------------
    = = = NODES AND RELATIONS EXTRACTION = = =
    --------------------------------------------------------------------------------
    NODES AND RELATIONS EXTRACTION:
    Using ontology.NODE_TYPES and ontology.EDGE_TYPES, extract all nodes and their relationships
    from the document. Include all relevant metadata and provenance information.

    --------------------------------------------------------------------------------
    Extract What's Specified in the Ontology Contract
    --------------------------------------------------------------------------------

    You MUST:
    - Extract only what is explicitly or strongly implied by the input text.
    - Do not infer or assume information not present.
    - Emit only node/edge types that appear in the ontology.
    - Each node must have a type or property["label"] that maps to NODE_TYPES.
    - Use only node/edge property names that appear in the ontology metadata lists.
    - Attach evidence and a confidence score to every node and edge using the
    allowed property names from NODE_PROPERTIES / EDGE_PROPERTIES.
    - **CRITICAL: Every node MUST have an "id" field that is a valid UUID in RFC 4122 format (e.g., "550e8400-e29b-41d4-a716-446655440000"). Edge "source" and "target" fields MUST also be valid UUIDs referencing node IDs.**
    - Normalize entity names and deduplicate obvious variants.
    - EVERY node MUST have MSIO (Mining System Integration Ontology) ontology classification (discipline, category, subcategory, entity)
    - EVERY node MUST match the MSIO ontology hierarchy as closely as possible
    - Use ONLY Discipline/Category/Subcategory/Entity names from the provided MSIO ontology
    - If an entity cannot be matched to MSIO ontology, create a new node with the closest MSIO hierarchy match and set "outside_msio": true attribute
    - Find entities with total costs e.g., Total Installed Cost (TIC) or Total Capital Cost (TCC) and extract the cost value and currency as separate properties
    - Use the MSIO matching workflow above for every entity extraction
    - DEDUPLICATE entities following the Entity Deduplication and Merging Policy (see above)


    ONTOLOGY (from config.py):
    Allowed node types (ontology.NODE_TYPES): See ontology contract for details.

    Allowed edge types (ontology.EDGE_TYPES): See ontology contract for details.

    --------------------------------------------------------------------------------
    Additional Specifications for Entity Extraction
    --------------------------------------------------------------------------------

    Extract the following decision-related entities as nodes in addition to
    physical assets, materials, and costs. These define the "global objective" layer
    used for optimization and optionality.

  1. **KPIs (Key Performance Indicators)**  
    - Examples: throughput (t/h), recovery (%), availability (%), OPEX/t, power efficiency.  
    - Extract name, formula, unit, direction (“maximize” / “minimize”), target value(s).
    - Signals: “target”, “KPI”, “goal”, “objective”, “performance indicator”, “design basis”.  

  2. **Production & Operating Specifications**  
    - Technical baseline targets: ore grade, product purity, tonnage, throughput, utilization.
    - Signals: “production rate”, “feed grade”, “product quality”, “target output”, “operating hours”.

  3. **Materials, Reagents, Fuels, and Streams**  
    - Any named physical substance or flow referenced with quantities, composition, or cost:
      ore types, concentrates, tailings, reagents, acids/bases, solvents, fuels (diesel, gas),
      process water, slurry or gas streams.
    - For each distinct substance, create a `Material` node:
      - Set properties.name to the domain term (e.g., “sodium cyanide”, “high-grade ore”).
      - In `properties.attributes`, capture:
        • "material_class": one of ["ore","concentrate","tailings","process_reagent",
          "bulk_chemical","solvent","gas","fuel","water","structural_material","consumable",
          "grinding_media","liner","explosive","product","waste","other"].
        • "phase": "solid" | "liquid" | "gas" | "slurry" | "solution".
        • Any composition (grade, species, purity), density, viscosity, heating_value,
          carbon_intensity, and unit_cost (value + unit) where present in the text.
    - For each flow with a quantity over time or per-tonne basis, create a `Stream` node:
      - In `properties.attributes`, capture:
        • "stream_type": "material" or "energy".
        • "basis": e.g. "per_hour", "per_day", "per_year", "per_tonne_ore".
        • "flow_rate" and "flow_unit" (e.g., 500 and "t/h"; 20 and "Nm3/h"; 15 and "kWh/t").
        • optional solids_fraction, temperature, pressure if stated.
      - If supported by EDGE_TYPES, link streams to substances using a :USES_MATERIAL edge
        (Stream → Material); otherwise embed the material reference in attributes.

    4. Constraints  (node type: "Constraint")
      - Definition: Bounds or requirement expressions (technical, economic,
        regulatory, environmental).
      - When to create:
        • Text specifies hard limits or mandatory requirements.
        • Phrases like "must not exceed", "at least", "no more than", "cannot be
          less than", "limited to".
      - Capture:
        • quantity_name (e.g., "power demand", "tailings capacity").
        • operator: "<=", ">=", "=".
        • value and unit (e.g., 30 MW, 92 % availability).
        • scope/condition (e.g., "during Phase 1", "for 20-year horizon").

    5. KPIs  (node type: "KPI")
      - Definition: Key performance indicators with formulas or definitions.
      - When to create:
        • Text defines a metric used to measure success or performance.
        • Phrases like "KPI", "key metric", "indicator", or explicit definitions of
          metrics such as "cash cost per tonne", "recovery", "availability".
      - Capture:
        • name and unit.
        • formula/definition if provided.
        • direction: "higher is better" / "lower is better" if implied.
        • link later to Objectives via satisfaction or contribution (SATISFIES).

    6. Scenarios  (node type: "Scenario")
      - Definition: What-if overlays referencing a baseline configuration.
      - When to create:
        • Text describes specific cases like "Base Case", "High power price
          scenario", "25% throughput increase case".
        • Mentions of sensitivities or discrete cases ("low / medium / high").
      - Capture:
        • name (scenario label).
        • description: what changes relative to the baseline.
        • any key parameters changed if explicitly stated.

    7. Options and Alternatives  (node types: "Option", "Alternative")
      - Option:
        • Definition: Change proposal applied over a Baseline.
        • When to create:
          – Text proposes a design or operating change: new equipment, flowsheet
            variant, different energy source, etc.
        • Capture:
          – name (e.g., "Add secondary crusher", "Switch to HPGR").
          – description and rationale if provided.
      - Alternative:
        • Definition: Concrete alternative within an Option (e.g., specific vendor
          or configuration choices).
        • When to create:
          – Text lists multiple concrete choices under the same conceptual option,
            like "Crusher A vs Crusher B", "Reagent package X vs Y".
        • Capture:
          – name and description for each alternative.

    8. Decision Variables  (node type: "DecisionVariable")
      - Definition: Variables that can vary across scenarios or optimization
        runs (tunable levers).
      - When to create:
        • Text identifies adjustable parameters: grind size, reagent dosage,
          operating hours, number of lines, cut-off grade, etc.
        • Often specified with ranges ("between", "from X to Y") or as things that
          "can be adjusted", "tuned", or "optimized".
      - Capture:
        • name and unit.
        • default_value if stated.
        • lower_bound and upper_bound when a range is given.
        • description of its role (e.g., "controls throughput", "affects recovery").

    9. Cost Rules and Cost Drivers  (node types: "CostRule", "CostDriver")
      - CostRule:
        • Definition: Reusable estimation methods, parametric formulas, or rules
          that map drivers to costs.
        • When to create:
          – Text specifies cost relationships such as "maintenance cost is 3% of
            installed cost per year" or "cost scales with capacity^0.6".
        • Capture:
          – description and formula (as text or pseudo-math).
          – applicable scope (equipment type, capacity range, region).
      - CostDriver:
        • Definition: Drivers of cost (throughput, power, distance, hardness, etc.).
        • When to create:
          – Text identifies variables that influence cost levels, even if the
            exact formula is not given.
        • Capture:
          – name of the driver.
          – description of how it affects cost when stated.

    10. Risks and Assumptions  (node types: "Risk", "Assumption")
      - Risk:
        • Definition: Potential adverse events or uncertainties that may affect
          objectives, costs, or schedule.
        • When to create:
          – Text describes risks such as power price volatility, supply chain
            issues, geotechnical failures, regulatory delays.
        • Capture:
          – description.
          – likelihood and impact if quantified (or qualitative high/medium/low).
      - Assumption:
        • Definition: Explicit assumptions supporting decisions or scenarios.
        • When to create:
          – Text uses "assumes", "assuming", "on the basis that", or otherwise
            clearly marks underlying assumptions.
        • Capture:
          – assumption text.
          – any numeric values embedded in the assumption (prices, rates, etc.).

    11. Project  (node type: "Project")
      - Definition: Coherent endeavor with scope and timeline (overall mining or
        processing project, phase, or study).
      - When to create:
        • Text names the project, phase, or study ("XYZ Copper Project", "Phase 1
          Expansion", "Feasibility Study 2025").
      - Capture:
        • name.
        • phase/stage if given (concept, PFS, FS, etc.).
        • any dates or time horizons mentioned.


    OUTPUT CONTRACT (strict):
    Node object (each item in extract_nodes.nodes) MUST have:
    - "id": MUST be a valid UUID (RFC 4122 format, e.g., "550e8400-e29b-41d4-a716-446655440000")
    - "type": one of NODE_TYPES; a Node object must have a type
    - "properties": object/dict containing:
        • MANDATORY MSIO fields (all must be present and match ontology):
          - "discipline": string (MUST match an MSIO Discipline name exactly)
          - "category": string (MUST match an MSIO Category name within that Discipline)
          - "subcategory": string (MUST match an MSIO Subcategory name within that Category)
          - "entity": string (MUST match an MSIO Entity name within that Subcategory, or closest match)
        • MANDATORY Attributes:
          - "attributes": array of attribute objects (see STEP 6 under 'MANDATORY MSIO ONTOLOGY MATCHING WORKFLOW')
            - "name": string (attribute name from ontology)
            - "value": number|null (attribute value)
            - "unit": string|null (attribute unit)
            - "evidence_text": string|null (text snippet used to extract attribute)
            - "confidence": 0.0-1.0 (confidence score for this attribute)
        • if an entity outside the MSIO ontology is extracted, create a new node with the entity name and the MSIO hierarchy that is closest to the entity name (e.g., "Concrete Spread Footings" -> "Concrete" -> "Foundations" -> "Footings" -> "Spread footings")
          •• for the outside entity, set an attribute "outside_msio" to true
        • follow the properties mentioned in NODE_PROPERTIES in the ontology
        • prioritize finding cost associated with an entity (e.g., 'cost_value', 'price_value', 'currency', 'basis_year', 'expenditure')
        • always keep cost value and currency as separate properties (never as a combined string)
        • always keep cost value and currency as top-level within the properties dictionary
        • if a cost or price is present, extract the numeric value to 'cost_value' and the currency to 'currency'
        • if a basis year is present, extract it to 'basis_year'
        • if currency is not present, set 'currency' to null
        • if basis year is not present, omit 'basis_year'
        • include evidence/confidence meta-properties from NODE_PROPERTIES
        • include any other domain-specific properties from NODE_PROPERTIES that appear in the text
    - "name": human-readable name (string)

    Node object (each item in extract_nodes.tabular_entities) MUST follow the same guidelines as for entities from text, and with the following additional requirements:
    - "attributes": array of attribute objects (combining NODE_PROPERTIES and MSIO_ONTOLOGY entity ontology attributes)
      - "name": string (attribute name from ontology)
      - "value": number|null (attribute value)
      - "unit": string|null (attribute unit)
      - "evidence_text": string|null (text snippet used to extract attribute)
      - "confidence": 0.0-1.0 (confidence score for this attribute)

    Edge object (each item in extract_edges.edges) MUST have:
    - "source": node id (MUST be a valid UUID referencing a node)
    - "target": node id (MUST be a valid UUID referencing a node)
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
        • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
        • any domain attributes the ontology expects for that edge (if any)
        • include evidence/confidence meta-properties from EDGE_PROPERTIES

    EXAMPLES:
    - Node example: {ontology.get("NODE_PROP_EXAMPLE", "{}")}
    - Edge example: {ontology.get("EDGE_PROP_EXAMPLE", "{}")}


    QUALITY GATE (pre-return):
    - Every node: non-empty, unique 'id' (MUST be a valid UUID in RFC 4122 format), valid 'type', and a 'properties' dict.
    - Every node has a 'name' property; populate it with the proper entity name.
    - Every node has a 'type' property that matches NODE_TYPES.
    - Every node property key matches NODE_PROPERTIES.
    - For nodes of type 'Equipment', 'Process', 'Material', 'Product', 'Waste', etc., acquire cost details if they appear in text.
    - For nodes of type 'CostRule', ensure compliance with COST & METHOD POLICY block.
    - For nodes of type 'CostEstimate' or similar, ensure costing details are present.
    - For node properties that are costs/prices, always extract and store the numeric value and currency as separate properties.
    - For node properties that are costs/prices, include currency and basis_year when available.
    - MSIO ONTOLOGY VALIDATION (MANDATORY):
      ✓ Every node.properties.discipline exists in MSIO ontology disciplines list
      ✓ Every node.properties.category exists within the matched Discipline
      ✓ Every node.properties.subcategory exists within the matched Category
      ✓ Every node.properties.entity exists within the matched Subcategory (or is closest match)
      ✓ All MSIO fields are non-empty strings
      ✓ No nodes have MSIO fields that don't exist in the ontology
      ✓ If MSIO match is partial/inferred, confidence < 0.7 and rationale provided
      ✓ Reject any nodes that cannot be matched to at least Discipline+Category+Subcategory
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
        "id": "550e8400-e29b-41d4-a716-446655440000",  // MUST be a valid UUID (RFC 4122 format)
        "type": "<EntityType>",                 // One of NODE_TYPES from the ontology
        "properties": {{
            "name": "string",                   // Human-readable name
            "created_at": "ISO-8601-timestamp", // e.g., "2024-01-01T12:00:00Z"
            "updated_at": "ISO-8601-timestamp", // e.g., "2024-01-01T12:00:00Z"
            "discipline": "string",             // Required; Discipline from the MSIO ontology
            "category": "string",               // Required; Category from the MSIO ontology
            "subcategory": "string",            // Required; Subcategory from the MSIO ontology
            "entity": "string",                // Required; Entity from the MSIO ontology
            "attributes": [                     // Array of attribute objects (see STEP 6)
                {{
                    "name": "string",           // Attribute name from ontology (e.g., "Design flowrate")
                    "value": "number|null",     // Attribute value (e.g., 500) or null if not present
                    "unit": "string|null",      // Attribute unit (e.g., "gpm") or null if not present
                    "evidence_text": "string|null", // Text snippet used to extract attribute
                    "confidence": 0.0-1.0        // Confidence score for this attribute
                }}
            ],
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
        "id": "550e8400-e29b-41d4-a716-446655440001",  // MUST be a valid UUID (RFC 4122 format)
        "source": "550e8400-e29b-41d4-a716-446655440000",  // MUST be a valid UUID referencing a node
        "target": "550e8400-e29b-41d4-a716-446655440002",  // MUST be a valid UUID referencing a node
        "type": "PART_OF",
        "properties": {{
            "created_at": "ISO-8601-timestamp",
            "updated_at": "ISO-8601-timestamp",
            "evidence_text": "short supporting snippet",
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
    "Two base pump units (centrifugal) sized for 500 gpm at 120 ft head with
    mechanical seals. Vendor datasheet attached."

    Classification:
        Discipline: Mechanical Equipment (matches MSIO)
        Category: Pumps (matches MSIO within Mechanical Equipment)
        Subcategory: Centrifugal (matches MSIO within Pumps)
        Entity: Base pump unit (matches MSIO within Centrifugal)

    Nodes: [
        {{
        "id": "550e8400-e29b-41d4-a716-446655440000",  // MUST be a valid UUID
        "type": "Equipment",
        "properties": {{
            "name": "Centrifugal Pump 500 gpm",
            "discipline": "Mechanical Equipment",
            "category": "Pumps",
            "subcategory": "Centrifugal",
            "entity": "Base pump unit",
            "attributes": [
                {{
                    "name": "Design flowrate",
                    "value": 500,
                    "unit": "gpm",
                    "evidence_text": "sized for 500 gpm",
                    "confidence": 0.95
                }},
                {{
                    "name": "Head",
                    "value": 120,
                    "unit": "ft",
                    "evidence_text": "at 120 ft head",
                    "confidence": 0.95
                }},
                {{
                    "name": "NPSH",
                    "value": null,
                    "unit": null,
                    "evidence_text": null,
                    "confidence": 0.0
                }}
            ],
            "seal_type": "mechanical",
            "evidence_text": "...500 gpm at 120 ft head with mechanical seals...",
            "confidence": 0.92,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
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

nodes_and_relations_extraction_directives = """
  --------------------------------------------------------------------------------
  = = = NODES AND RELATIONS EXTRACTION = = =
  --------------------------------------------------------------------------------
  Using ontology.NODE_TYPES and ontology.EDGE_TYPES, extract all nodes and edges
  from the document, with full MSIO classification, metadata, and provenance.

  --------------------------------------------------------------------------------
  Ontology Contract (Hard Constraints)
  --------------------------------------------------------------------------------
  You MUST:
  - Extract only what is explicitly or strongly implied by the text.
  - Do NOT invent entities, properties, or relations.
  - Emit only node/edge types in NODE_TYPES / EDGE_TYPES.
  - Each node MUST have:
    • "id": valid RFC 4122 UUID (e.g., "550e8400-e29b-41d4-a716-446655440000").
    • "type": one of NODE_TYPES.
    • "properties": dict with only keys from NODE_PROPERTIES.
    • "name": human-readable label.
  - Each edge MUST have:
    • "id": valid RFC 4122 UUID.
    • "source": UUID of existing node.
    • "target": UUID of existing node.
    • "type": one of EDGE_TYPES.
    • "properties": dict with only keys from EDGE_PROPERTIES.
  - Attach evidence_text and confidence to every node and edge (from allowed meta keys).
  - Normalize entity names; deduplicate variants (per Entity Deduplication policy).
  - Every node MUST have MSIO classification:
    • discipline, category, subcategory, entity
    • Each MUST match the MSIO ontology (closest valid match).
  - If no exact MSIO match:
    • choose the closest hierarchy,
    • set properties["outside_msio"] = true.
  - Use ONLY Discipline/Category/Subcategory/Entity names from AV_MSIO_ONTOLOGY.
  - For every entity with a total cost (e.g., TIC, TCC, installed cost, opex):
    • extract cost_value (numeric), currency (string), and basis_year (if present),
    • NEVER store combined "USD 5M" strings as a single field.
  - Apply the MSIO matching workflow and dedup policy to every entity.

  ONTOLOGY (from config.py):
  - Allowed node types: ontology.NODE_TYPES
  - Allowed edge types: ontology.EDGE_TYPES

  --------------------------------------------------------------------------------
  Additional Specifications for Entity Extraction
  --------------------------------------------------------------------------------
  Extract the following decision-related entities as nodes in addition to physical
  assets, materials, and costs. These define the global objective / optimization layer.

  1. KPIs (node type: "KPI")
    - Any named metric used to track performance or success: throughput, recovery,
      availability, opex/t, power efficiency, etc.
    - Signals: "KPI", "indicator", "metric", "target", "goal", "design basis".
    - Capture: name, unit, formula/definition if given, direction ("maximize" /
      "minimize" / "higher is better" / "lower is better"), target values if stated.

  2. Production & Operating Specifications
    - Baseline technical targets: ore grade, product purity, tonnage, throughput,
      utilization, operating hours.
    - Capture as attributes on relevant nodes (Equipment, Process, Project, Scenario)
      using NODE_PROPERTIES; do NOT create custom ad-hoc node types.

  3. Materials, Reagents, Fuels, and Streams
    - Any physical substance or flow with quantity, composition, or cost:
      ore types, concentrates, tailings, reagents, acids/bases, solvents, fuels,
      process water, slurry streams, gas streams.
    - For each distinct substance, create a Material node:
      • properties["name"]: domain term (e.g., "sodium cyanide", "high-grade ore").
      • attributes:
        - "material_class": one of [
          "ore","concentrate","tailings","process_reagent","bulk_chemical","solvent",
          "gas","fuel","water","structural_material","consumable","grinding_media",
          "liner","explosive","product","waste","other"
        ]
        - "phase": "solid" | "liquid" | "gas" | "slurry" | "solution"
        - composition/grade/purity, density, viscosity, heating_value,
          carbon_intensity, unit_cost and unit_cost_basis when present.
    - For each flow with a rate over time or per-tonne basis, create a Stream node:
      • attributes:
        - "stream_type": "material" or "energy"
        - "basis": e.g., "per_hour", "per_day", "per_year", "per_tonne_ore"
        - "flow_rate" (numeric) and "flow_unit" ("t/h", "Nm3/h", "kWh/t", etc.)
        - solids_fraction, temperature, pressure when present.
      • If EDGE_TYPES contains USES_MATERIAL:
        - create Stream —USES_MATERIAL→ Material edges.

  4. Constraints (node type: "Constraint")
    - Bounds or requirements (technical, economic, regulatory, environmental).
    - Signals: "must not exceed", "at least", "not less than", "no more than",
      "limited to".
    - Capture: quantity_name, operator ("<=", ">=", "="), value, unit, and any
      scope/condition ("Phase 1", "20-year life").

  5. Scenarios (node type: "Scenario")
    - What-if overlays relative to a baseline: "Base Case", "High power price
      scenario", "25% throughput increase case", "low/medium/high cases".
    - Capture: name, description (how it differs from baseline), and explicit
      parameter changes if stated.

  6. Options and Alternatives (node types: "Option", "Alternative")
    - Option:
      • Change proposal applied over a baseline:
        new equipment, flowsheet variant, different energy source, reagent system.
      • Capture: name (e.g., "Add secondary crusher"), description, rationale.
    - Alternative:
      • Concrete choice inside an Option: "Crusher A vs Crusher B", "Reagent X vs Y".
      • Capture: name, description.
    - Structure: multiple Alternatives may exist under one Option; later edges
      (e.g., ALTERNATIVE_TO, MODIFIES) are allowed only if in EDGE_TYPES.

  7. Decision Variables (node type: "DecisionVariable")
    - Variables that can vary across scenarios or optimization runs:
      grind size, reagent dosage, operating hours, number of lines, cut-off grade.
    - Signals: "can be adjusted", "tuned", "optimized", ranges ("from X to Y",
      "between X and Y").
    - Capture: name, unit, default_value (if given), lower_bound, upper_bound,
      and a short description of its role.

  8. Cost Rules and Cost Drivers (node types: "CostRule", "CostDriver")
    - CostRule:
      • Parametric cost formulas or rules:
        "maintenance cost is 3% of installed cost per year",
        "cost scales with capacity^0.6".
      • Capture: description, formula (text/pseudo-math), applicable scope
        (equipment type, capacity range, region).
    - CostDriver:
      • Variables that drive cost: throughput, installed power, distance to port,
        ore hardness, reagent dosage.
      • Capture: name, qualitative/quantitative description of impact on cost.

  9. Risks and Assumptions (node types: "Risk", "Assumption")
    - Risk:
      • Adverse events or uncertainties impacting objectives, cost, or schedule:
        power price volatility, geotechnical failure, supply disruption,
        permitting delays.
      • Capture: description, likelihood and impact if given (or qualitative
        high/medium/low).
    - Assumption:
      • Explicit assumptions underpinning analysis:
        "assumes constant power price", "assumes 93% recovery", "assumes no
        significant permitting delay".
      • Capture: assumption text, any numeric values (prices, rates, recoveries).

  10. Project (node type: "Project")
      - Overall project or study: "XYZ Copper Project", "Phase 1 Expansion",
        "Feasibility Study 2025".
      - Capture: name, phase/stage (concept, PFS, FS, etc.) if given, and
        key dates or horizons.

  --------------------------------------------------------------------------------
  OUTPUT CONTRACT (STRICT)
  --------------------------------------------------------------------------------
  Top-level JSON keys ONLY: "nodes", "edges", "meta".

  nodes: array of node objects. Each node:
  {
    "id": "<RFC-4122-UUID>",             // REQUIRED
    "type": "<NodeTypeFromNODE_TYPES>",  // REQUIRED
    "properties": {
      "name": "string",                  // REQUIRED
      "discipline": "string",            // REQUIRED MSIO discipline
      "category": "string",              // REQUIRED MSIO category
      "subcategory": "string",           // REQUIRED MSIO subcategory
      "entity": "string",                // REQUIRED MSIO entity (or closest match)
      "attributes": [                    // attribute objects
        {
          "name": "string",
          "value": number|null,
          "unit": "string|null",
          "evidence_text": "string|null",
          "confidence": 0.0-1.0
        }
      ],
      "cost_value": number|null,         // if any cost present
      "currency": "string|null",         // e.g., "USD"; null if not present
      "basis_year": number|null,         // omit if not present
      "outside_msio": true|false,        // include only when outside MSIO
      "evidence_text": "string|null",
      "confidence": 0.0-1.0,
      ...                                // any other fields from NODE_PROPERTIES only
    }
  }

  edges: array of edge objects. Each edge:
  {
    "id": "<RFC-4122-UUID>",             // REQUIRED
    "source": "<RFC-4122-UUID>",         // REQUIRED, must reference a node.id
    "target": "<RFC-4122-UUID>",         // REQUIRED, must reference a node.id
    "type": "<EdgeTypeFromEDGE_TYPES>",  // REQUIRED
    "properties": {
      "evidence_text": "string|null",
      "confidence": 0.0-1.0,
      ...                                // only keys from EDGE_PROPERTIES
    }
  }

  meta:
  {
    "ontology_version": "simple-json-v1",
    "policy": {
      "element_split_on_slash": true
    },
    "extraction_date": "YYYY-MM-DD"
  }

  --------------------------------------------------------------------------------
  QUALITY GATE (MANDATORY BEFORE RETURN)
  --------------------------------------------------------------------------------
  - Every node:
    • id is a valid UUID, unique.
    • type in NODE_TYPES.
    • properties is non-empty dict.
    • has name, discipline, category, subcategory, entity.
    • MSIO fields exist in AV_MSIO_ONTOLOGY hierarchy; otherwise outside_msio=true.
    • attributes is an array; all attribute objects follow the contract.
    • cost_value and currency split if cost present.
  - Every edge:
    • id, source, target are valid UUIDs.
    • type in EDGE_TYPES.
    • properties contains evidence_text and confidence.
  - MSIO validation:
    ✓ discipline/category/subcategory/entity all non-empty and valid.
    ✓ no invalid MSIO labels.
    ✓ partial/inferred MSIO match ⇒ confidence < 0.7 and rationale in evidence_text.
  - No property keys outside NODE_PROPERTIES / EDGE_PROPERTIES.
  - No hallucinated entities, relations, or values.

  Return a single JSON object:
  { "nodes": [...], "edges": [...], "meta": {...} }
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

# Cost extraction prompt
cost_extraction_block = """
  --------------------------------------------------------------------------------
  COST EXTRACTION
  --------------------------------------------------------------------------------
  
  Extract cost information from the text when available and store it in properties.cost object. If not available, 
  still create the entity but keep cost properties as null.

  COST PROPERTIES:
  - cost_value (number): Numeric cost value
  - cost_currency (string): Currency code in ISO format (e.g., 'USD', 'EUR')
  - cost_min (number): Minimum cost value, default to cost_value if not present
  - cost_max (number): Maximum cost value
  - cost_unit (string): Unit of the cost value
  - cost_basis (string): Basis of the cost value (e.g., “installed”, “silt fence”)
  - cost_alternates (array of additional ranges when text contains “or / OR”)
  - Attach cost objects to `CostItem` nodes and, when appropriate, to `Material` or `Stream`
    nodes (e.g., reagent price per tonne, fuel price per MWh, water price per m3), using the
    standard cost_value, cost_currency, cost_basis, cost_min, cost_max, cost_unit, cost_alternates properties.

  • If a cost string contains multiple ranges (e.g., “$5 - $25 / SY or $1,000 - $8,000 LS”), parse the FIRST as the primary range and each additional range as a separate `alternate` entry.

  • Examples of cost range formats:
    - "$1200" -> cost_value: 1200, cost_currency: "USD", cost_min: null, cost_max: null
    - "$12 - $25 / yd3" -> cost_min: 12, cost_max: 25, cost_unit: "yd3"
    - "$3 - $8 / LF (silt fence)" -> cost_min: 3, cost_max: 8, cost_unit: "LF", cost_basis: "silt fence"
    - "$800 - $3,000 / inlet" -> cost_min: 800, cost_max: 3000, cost_unit: "inlet"
    - "$5 - $25 / SY or $1,000 - $8,000 LS" -> cost_min: 5, cost_max: 25, cost_unit: "SY", cost_alternates: [{"cost_min": 1000, "cost_max": 8000, "cost_unit": "LS"}]
    - "$80 - $250 / ft3 (liner & basin) OR $8,000 - $25,000 / EA" -> cost_min: 80, cost_max: 250, cost_unit: "ft3", cost_basis: "liner & basin", cost_alternates: [{"cost_min": 8000, "cost_max": 25000, "cost_unit": "EA"}]
  • If the column is blank, return cost_value: null, cost_currency: null, cost_basis_year: null, cost_type: null, annual_op_cost: null, reclamation_cost: null
  
  TOTAL COST EXTRACTION:
  When Total Installed Cost (TIC), Total Capital Cost (TCC), or similar totals are mentioned:
  - Extract as separate CostItem entities with type='CostItem'
  - Include total_cost_value and total_cost_currency as direct properties
  - Create HAS_COST or AFFECTS_COST relationships linking entities to total cost
  - This enables validation by comparing extracted vs calculated totals  
"""

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

  2) EXTRACTION POLICY
  2.1) Exhaustiveness
    - Capture every measurable, referable, or categorical fact.
    - Include all numeric values and units exactly as written (no conversion/rounding).
    - Extract table rows, list items, design criteria, codes, assumptions, exclusions, etc.
    - Each object must carry at least one anchor (e.g., "§2", "p.4", "Table 1").

  2.2) Descriptive Text (250–500 words per section/domain)
    - Provide `"descriptive_text"` for:
      • Each entry in `"sections"` (its own subsection narrative).
      • Each top-level domain: process_flows, design_criteria, equipment,
        materials, instrumentation_controls, site_data, codes_standards,
        policies_recommendations, constraints, costs, risks_uncertainties.
    - Use only information present in the report; do not invent.
    - You may include short quotes ≤40 words with anchors to capture exact phrasing.

  2.3) Missing Data & Fidelity
    - If data are implied/missing → set value = null and add an item in
      `"risks_uncertainties"` with a remediation action.
    - Preserve original symbols and qualifiers (“~”, “@ 80%”, “±”, “nameplate”).

  2.4) Output Discipline
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

NODE_TYPES = json.dumps(ENTITY_ONTOLOGY.get("node_types", []), indent=1)
EDGE_TYPES = json.dumps(ENTITY_ONTOLOGY.get("edge_types", []), indent=1)
NODE_PROPERTIES = json.dumps(ENTITY_ONTOLOGY.get("node_properties", []), indent=1)
EDGE_PROPERTIES = json.dumps(ENTITY_ONTOLOGY.get("edge_properties", []), indent=1)

# Load MSIO ontology
MSIO_ONTOLOGY_TEXT = json.dumps(AV_MSIO_ONTOLOGY, indent=1)

# Extract discipline names for quick reference
MSIO_DISCIPLINE_NAMES = [d["name"] for d in AV_MSIO_ONTOLOGY.get("disciplines", [])]
MSIO_DISCIPLINE_NAMES_STRING = ", ".join(MSIO_DISCIPLINE_NAMES)

# MSIO Classification Workflow
msio_classification_workflow = f"""\

  --------------------------------------------------------------------------------
  MSIO ONTOLOGY QUICK REFERENCE
  --------------------------------------------------------------------------------
  Valid Disciplines (case-insensitive match):
  {MSIO_DISCIPLINE_NAMES_STRING}

  For each Discipline, valid Categories can be found in the full ontology JSON below.
  For each Category, valid Subcategories can be found in the full ontology JSON below.
  For each Subcategory, valid Entities can be found in the full ontology JSON below.

  MATCHING STRATEGY:
  1. Use case-insensitive string matching
  2. Normalize whitespace (collapse multiple spaces)
  3. Handle common synonyms (e.g., "pump" → match to "Pumps" category)
  4. If exact match fails, look for partial matches (e.g., "centrifugal pump" → "Centrifugal" subcategory)

  --------------------------------------------------------------------------------
  FULL MSIO ONTOLOGY JSON (SOURCE OF TRUTH)
  --------------------------------------------------------------------------------
  {MSIO_ONTOLOGY_TEXT}

  --------------------------------------------------------------------------------
  MSIO ONTOLOGY MAPPING WORKFLOW
  --------------------------------------------------------------------------------
  Map MSIO classification to entities found using the top-level "NODE_TYPE" type and their properties in "NODE_PROPERTIES"

  STEP 1: Identify the entity
  - Extract the entity name/description from text
  - Note surrounding context (e.g., "pump", "tank", "conveyor belt")
  - Assign a type from the top-level "NODE_TYPE" to the entity

  STEP 2: Match to Discipline (top-down search)
  - Start with Discipline names in the MSIO ontology
  - Match case-insensitively (e.g., "mechanical equipment" = "Mechanical Equipment")
  - If no match, assign the entity to the "Miscellaneous" category

  STEP 3: Match to Category (within matched Discipline)
  - Search Categories within the matched Discipline
  - Match case-insensitively
  - If no match, assign the entity to the "Miscellaneous" category

  STEP 4: Match to Subcategory (within matched Category)
  - Search Subcategories within the matched Category
  - Match case-insensitively
  - If no match, assign the entity to the "Miscellaneous" category

  STEP 5: Match to Entity (within matched Subcategory)
  - Search Entity names within the matched Subcategory
  - Match case-insensitively (e.g., "base pump unit" = "Base pump unit")
  - If no match, assign the entity to the "Miscellaneous" category

  STEP 6: Extract Attributes and Cost Information
  - For each NODE_TYPE entity, extract the attributes from the text based on the properties in NODE_PROPERTIES
  - [Required] Extract all possible technical and operational attributes from the text, including but not limited to:
    * Flow-related: Flow To Pump Box, Design flowrate, flow_rate, throughput, etc.
    * Efficiency: Motor Efficiency, Pump Efficiency, efficiency, etc.
    * Power: Required Motor HP, power, horsepower, etc.
    * Head/Pressure: Total Dynamic Head, Head, pressure, etc.
    * Capacity: Capacity Value, Capacity Unit, capacity, etc.
    * Other: Description, Materials, Seal type, Speed, NPSH, Dimensions, Mass, Weight, Temperature, etc.
  - Create an object for each attribute with the following properties:
    * "name": the attribute name (use descriptive names like "Flow To Pump Box", "Motor Efficiency", etc.)
    * "value": the attribute value (number or string)
    * "unit": the attribute unit (e.g., "GPM", "%", "HP", "ft")
    * "evidence_text": the text that was used to extract the attribute
    * "confidence": the confidence score for the attribute
  - Additionally, check the "attributes" list in the MSIO_ONTOLOGY entity ontology
    - Normalize attribute fields per the Attribute Extraction rules
      * [Required] If the attribute is not present in the text, set the attribute value to null and the attribute unit to null
      ** For example, if the attribute is "Design flowrate", and the text says "500 gpm", then the attribute value should be 500 and the attribute unit should be "gpm"
      ** if the attribute "Design flowrate" is not present in the text, then the attribute value should be null and the attribute unit should be null
  - IMPORTANT: Cost information (cost_value, cost_currency, cost_basis_year, cost_type, annual_op_cost, reclamation_cost) should be stored as DIRECT PROPERTIES on the node, NOT in the attributes array


  --------------------------------------------------------------------------------
  MATCHING & CLASSIFICATION RULES
  --------------------------------------------------------------------------------
  1) Match Scope
  - A mention in the report maps to one ontology data above (Discipline,
      Category, Subcategory, Entity). Prefer the most specific match (Entity).
  - If the report uses synonyms (e.g., "float roof" vs "Float Roof"), normalize
      via case-insensitive matching and simple singular/plural folding.

  2) Exactness & Fallback
  - Try full 4-tuple match (Discipline, Category, Subcategory, Entity).
  - If Entity is ambiguous/missing, back off to Subcategory (keep searching
      for the best Entity within that Subcategory using nearby cues/attributes).
  - If still ambiguous, return the top-2 candidates with lower confidence.

  3) Attribute Extraction
  - For a matched ontology row, parse the listed Attributes from the local
      context (sentence/table row). Extract numbers and units where present.
  - Create attribute objects as specified in STEP 6 with the following structure:
      * Each attribute must be an object with: name, value, unit, evidence_text, confidence
      * Store attributes in an "attributes" array in the node properties
      * Use attribute names as listed in the ontology (e.g., "Design flowrate", "Head")
      * For attributes not present in text, set value and unit to null
      * Preserve the original text snippet as evidence_text for each attribute
      
  4) Matching is case-insensitive.
    
    Examples (using actual MSIO_ONTOLOGY):
    - Input: "Two centrifugal pumps sized for 500 gpm at 120 ft head"
      Classification:
        Discipline: "Mechanical Equipment" (matches MSIO)
        Category: "Pumps" (matches MSIO within Mechanical Equipment)
        Subcategory: "Centrifugal" (matches MSIO within Pumps)
        Entity: "Base pump unit" (matches MSIO within Centrifugal)
        Attributes: "Design flowrate" (500 gpm), "Head" (120 ft)

    - Input: "Storage tank with fixed roof"
      Classification:
        Discipline: "Mechanical Equipment"
        Category: "Tanks"
        Subcategory: "Storage Tank"
        Entity: "Fixed Roof"

    - Input: "Concrete spread footings"
      Classification:
        Discipline: "Concrete"
        Category: "Foundations"
        Subcategory: "Footings"
        Entity: "Spread footings"


  VALIDATION CHECKLIST (before returning):
  ✓ Map to top-level NODE_TYPES and NODE_PROPERTIES for attributes
  ✓ Every node has properties.discipline matching an MSIO_ONTOLOGY Discipline name, else set to "Miscellaneous"
  ✓ Every node has properties.category matching an MSIO_ONTOLOGY Category name within that Discipline, else set to "Miscellaneous"
  ✓ Every node has properties.subcategory matching an MSIO_ONTOLOGY Subcategory name within that Category, else set to "Miscellaneous"  
  ✓ Every node has properties.entity matching an MSIO_ONTOLOGY Entity name within that Subcategory (or closest match), else set to "Miscellaneous"
  ✓ Every node has properties.attributes matching the attributes in NODE_PROPERTIES and MSIO_ONTOLOGY entity ontology attributes
  """

# Node and Relations extraction block (no edits)
nodes_and_relations_extraction_block = f"""\
  --------------------------------------------------------------------------------
  NODES AND RELATIONS TYPES
  --------------------------------------------------------------------------------
  Emit one JSON object with these top-level keys only: nodes, edges, meta.
  NODE_TYPES: {ontology_nodes_and_relations.get("NODE_TYPES", "")}
  EDGE_TYPES: {ontology_nodes_and_relations.get("EDGE_TYPES", "")}

  --------------------------------------------------------------------------------
  NODES AND RELATIONS PROPERTIES
  --------------------------------------------------------------------------------
  {ontology_nodes_and_relations.get("NODE_PROPERTIES", "")}
  {ontology_nodes_and_relations.get("EDGE_PROPERTIES", "")}

  {nodes_and_relations_extraction_directives}
  """

##### Recommendation-based entity extraction prompt #####

# Objective-driven extraction additions (only what's different from base extraction)
objective_driven_extraction_additions = """
    --------------------------------------------------------------------------------
    OBJECTIVE-DRIVEN EXTRACTION REQUIREMENTS
    --------------------------------------------------------------------------------

    **CRITICAL DIFFERENCES FOR OBJECTIVE-DRIVEN EXTRACTION:**

    1. **Focus on Objective Relevance:**
       - Extract all nodes and relationships relevant to achieving the objective goal and target
       - Prioritize entities that directly or indirectly support the objective
       - Consider both current state and potential modifications

    2. **Recommendations Integration:**
       - **CRITICAL: NEVER create nodes with type='Recommendation'. Embed recommendations 
         in entity.properties.recommendations arrays only.**
       - Each node MUST have a "recommendations" array in properties (can be empty)
       - Recommendations should be embedded within relevant entity nodes

    3. **Enhanced Cost Information:**
       - Extract cost data when available (store in properties.cost)
       - Include cost impact direction and magnitude for recommendations

    4. **All other extraction rules from the base extraction prompt apply:**
       - Use NODE_TYPES and EDGE_TYPES from ontology (already provided above)
       - Follow MSIO classification requirements
       - Apply deduplication policies
       - Include evidence_text and confidence for all nodes and edges
       - Use UUID format for all IDs

    --------------------------------------------------------------------------------
    QUALITY VALIDATION (Additional Checks)
    --------------------------------------------------------------------------------
    ✓ Every node has recommendations array (can be empty)
    ✓ NO nodes with type='Recommendation' (recommendations only in properties.recommendations)
    ✓ Cost information stored in properties.cost (not in attributes)
    ✓ All entities are relevant to achieving the stated objective
"""

# Comments
"""
  - Process: Flow improvements, efficiency gains, throughput enhancements
  - Operations: Shift patterns, staffing, procedures, scheduling
  - Infrastructure: Utilities, buildings, site work, foundations, structures
  - Controls: Automation, instrumentation, SCADA, control logic
  - Energy: Power consumption, heat recovery, waste minimization
  - Maintenance: Reliability improvements, preventive maintenance, spare parts
  - Safety: Safety systems, procedures, equipment, training
  - Environmental: Emissions reduction, waste treatment, compliance
  
  Categorize as:
  - PRIMARY (5-10): High-impact, direct solutions
  - SECONDARY (5-10): Supporting changes
  - OTHER (5-10): Alternative approaches
"""


def generate_prompt_v1(
    artifact_type: str = "base_case",
    objective_type: Optional[str] = None,
    objective_target: Optional[str] = None,
    objective_unit: Optional[str] = None,
    objective_description: Optional[str] = None,
    add_edges: bool = False,
    rules: Optional[List[str]] = [
        "NODES_AND_RELATIONS",
        "PROVENANCE_AND_CONFIDENCE",
        "UNITS_NORMALIZATION",
    ],
) -> str:
    """
    Generate a single, compact, aggregated prompt for entity extraction.

    This is a unified prompt that combines all extraction capabilities into one text,
    with conditional sections for recommendations (if artifact_type is base_case).
    Recommendations section comes before entity extraction.

    Args:
        artifact_type: Type of artifact being processed (e.g., "base_case")
        objective_type: Objective type/goal (e.g., "increase production", "reduce capex")
        objective_target: Objective target value (e.g., "10%", "5%")
        objective_unit: Objective unit (e.g., "%", "USD")
        add_edges: Whether to extract edges/relationships (default: False)
        rules: Optional list of extraction rules to enable

    Returns:
        Single aggregated prompt string
    """

    # Build conditional recommendation section
    recommendation_section = ""
    if artifact_type == "base_case" and objective_type:
        recommendation_section = f"""
        -------------------------------------------------------------------------------
        RECOMMENDATION GENERATION (STEP 1 - DO THIS FIRST)
        -------------------------------------------------------------------------------
        CONTEXT
        Engineers in the [mining] industry use system design reports (here referred to as base case documents) to design and optimize systems to plan capital-intensive installations and operations. The reports consist of details on technical requirements, equipment and material, process, operations, capital (CAPEX) and operating (OPEX) costs, constraints, assumptions, exclusions, and policy information on project requirements. Our system (Alpha-Val) is designed to read the reports and extract all the relevant information and factors (hereon referred to as extracted entities), which is then used for cost estimation and analysis. Entities are structured data about factors such as equipment, material, process, constraints, cost items, and other relevant factors. Our system employs an ontology to map the extracted entities to a standard classification system (hereon referred to as MSIO ontology) and to extract the relevant information and factors.

        OBJECTIVE: {objective_type} by {objective_target} {objective_unit or "%"} {objective_description or ""}

        Before extracting entities, identify comprehensive recommendations to achieve this objective.

        Generate 3-5 most relevant recommendations across:
        - Equipment: Upgrades, replacements, additions, technology improvements
        - Materials: Raw materials, consumables, feedstocks, product specifications (e.g., concrete, metals, chemicals, liquids, gases, etc.)
        
        Recommendations must
        - Directly relate to the {objective_type} {objective_target} {objective_unit or "%"} {objective_description or ""}
        - Be relevant to the system and the objective
        - Be specific and detailed in the rationale field
        - Aim for 3-5 recommendations
        - Be categorized as PRIMARY or SECONDARY
          - PRIMARY: High-impact, direct solutions
          - SECONDARY: Supporting changes
        - Have the following fields: id, type, name, rationale, relevance, change_direction, change_magnitude, evidence_text, confidence, cost information (if available).
        - Be embedded in entity.properties.recommendations arrays.
        - NEVER create separate nodes with type='Recommendation'.
        """

    # Build edges section conditionally
    edges_section = ""
    if add_edges:
        edge_types_str = json.dumps(
            ontology_nodes_and_relations.get("EDGE_TYPES", []), indent=1
        )
        edges_section = f"""
          -------------------------------------------------------------------------------
          EDGES/RELATIONSHIPS EXTRACTION
          -------------------------------------------------------------------------------
          Extract relationships between entities using EDGE_TYPES: {edge_types_str}

          Each edge MUST have:
          - "id": valid UUID (RFC 4122 format)
          - "source": source node UUID
          - "target": target node UUID  
          - "type": one of EDGE_TYPES
          - "properties": object with evidence_text, confidence, and domain attributes

          """

    # Build rules sections conditionally
    rules_sections = ""
    if rules:
        if "UNITS_NORMALIZATION" in rules:
            rules_sections += f"{units_normalization_block}\n\n"
        if "TABLE_EXTRACTION" in rules:
            rules_sections += f"{table_extraction_block}\n\n"
        if "GLOBAL_OBJECTIVES" in rules:
            rules_sections += f"{global_objectives_block}\n\n"
        if "PROVENANCE_AND_CONFIDENCE" in rules:
            rules_sections += f"{prov_conf_block}\n\n"

    # Always include cost extraction block
    rules_sections += f"{cost_extraction_block}\n\n"

    # Main prompt
    prompt = f"""\
      -------------------------------------------------------------------------------
      ENTITY EXTRACTION PROMPT
      -------------------------------------------------------------------------------

      ROLE
      Extract clean, deduplicated entities from mining/process-engineering content aligned 
      to Mining System Integration Ontology (MSIO). Map entities to MSIO hierarchy 
      (Discipline → Category → Subcategory → Entity). If no MSIO match, use closest 
      hierarchy match and set "outside_msio": true.

      {recommendation_section}
      -------------------------------------------------------------------------------
      ONTOLOGY REFERENCE
      -------------------------------------------------------------------------------
      NODE_TYPES: {json.dumps(ontology_nodes_and_relations.get("NODE_TYPES", []), indent=1)}
      EDGE_TYPES: {json.dumps(ontology_nodes_and_relations.get("EDGE_TYPES", []), indent=1)}
      NODE_PROPERTIES: {json.dumps(ontology_nodes_and_relations.get("NODE_PROPERTIES", []), indent=1)}
      EDGE_PROPERTIES: {json.dumps(ontology_nodes_and_relations.get("EDGE_PROPERTIES", []), indent=1)}

      MSIO Disciplines: {MSIO_DISCIPLINE_NAMES_STRING}
      Full MSIO Ontology: {MSIO_ONTOLOGY_TEXT}

      -------------------------------------------------------------------------------
      EXTRACTION REQUIREMENTS
      -------------------------------------------------------------------------------

      MANDATORY:
      - Extract only what is explicitly or strongly implied by input text
      - Every node MUST have "id" as valid UUID (RFC 4122 format, e.g., "550e8400-e29b-41d4-a716-446655440000")
      - Every node MUST have MSIO classification: discipline, category, subcategory, entity
      - Use case-insensitive matching for MSIO hierarchy
      - If no match, set to "Miscellaneous" at that level
      - Extract all attributes from text (flow_rate, efficiency, power, capacity, head, pressure, etc.)
      - Store attributes in properties.attributes array: name, value, unit, evidence_text, confidence
      - Cost information stored in properties.cost (NOT in attributes): cost_value, 
        cost_currency, cost_basis_year, cost_type, annual_op_cost, reclamation_cost
      - Normalize units per units normalization rules
      - Deduplicate entities: merge duplicates with same MSIO classification and similar names
      - Include evidence_text and confidence (0.0-1.0) for all nodes
      - Map to most specific MSIO Entity available
      - Split only Entity/Element field on "/" in MSIO hierarchy

      OUTPUT CONTRACT:
      Each node MUST have:
      - "id": valid UUID
      - "type": one of NODE_TYPES
      - "properties": object containing:
        • discipline, category, subcategory, entity (MSIO classification)
        • "name": human-readable name
        • "attributes": array of {{
            "name": string,
            "value": number|null,
            "unit": string|null,
            "evidence_text": string|null,
            "confidence": 0.0-1.0
          }}
        • "cost": {{cost_value, cost_currency, cost_basis_year, cost_type, ...}} (if available)
        • "recommendations": array (if artifact_type is base_case, can be empty)
        • "outside_msio": boolean (true if no MSIO match)
        • evidence_text, confidence (MANDATORY)

      {rules_sections}
      {edges_section}
      -------------------------------------------------------------------------------
      MSIO CLASSIFICATION WORKFLOW
      -------------------------------------------------------------------------------

      STEP 1: Identify entity name/description from text
      STEP 2: Match to Discipline (case-insensitive, fallback to "Miscellaneous")
      STEP 3: Match to Category within Discipline (fallback to "Miscellaneous")
      STEP 4: Match to Subcategory within Category (fallback to "Miscellaneous")
      STEP 5: Match to Entity within Subcategory (fallback to "Miscellaneous")
      STEP 6: Extract attributes from NODE_PROPERTIES and MSIO ontology
        - Create attribute objects: name, value, unit, evidence_text, confidence
        - If attribute not present, set value and unit to null
        - Store cost info in properties.cost (not attributes array)

      Examples:
      - "Two centrifugal pumps 500 gpm at 120 ft head"
        → Discipline: "Mechanical Equipment", Category: "Pumps", Subcategory: "Centrifugal", 
          Entity: "Base pump unit", Attributes: Design flowrate (500 gpm), Head (120 ft)

      - "Storage tank with fixed roof"
        → Discipline: "Mechanical Equipment", Category: "Tanks", Subcategory: "Storage Tank", 
          Entity: "Fixed Roof"

      -------------------------------------------------------------------------------
      VALIDATION
      -------------------------------------------------------------------------------
      ✓ Every node has: unique UUID id, valid type, properties object with name, MSIO classification, attributes array
      ✓ All MSIO fields match ontology or set to "Miscellaneous"
      ✓ Extract only equipment, material, process, and product entities
      ✓ Attributes array contains all relevant attributes (null values allowed)
      ✓ Cost information in properties.cost (not attributes)
      ✓ Evidence and confidence for all nodes
      ✓ No hallucinated entities or properties
      {"✓ Recommendations array in properties (can be empty)" if artifact_type == "base_case" else ""}
      {"✓ Edges extracted with valid UUIDs and types" if add_edges else ""}
      - REJECT any nodes with empty recommendations array (properties.recommendations.length = 0) if artifact_type is base_case

      -------------------------------------------------------------------------------
      OUTPUT
      -------------------------------------------------------------------------------
      Return nodes with extract_nodes(nodes=[...]){" and edges with extract_edges(edges=[...])" if add_edges else ""}.

      Each node example:
      {{
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "Equipment",
        "properties": {{
          "name": "Centrifugal Pump 500 gpm",
          "discipline": "Mechanical Equipment",
          "category": "Pumps",
          "subcategory": "Centrifugal",
          "entity": "Base pump unit",
          "attributes": [
            {{"name": "Design flowrate", "value": 500, "unit": "gpm", "evidence_text": "500 gpm", "confidence": 0.95}}
          ],
          "cost": {{"cost_value": 400000, "cost_min":40000, "cost_max": 80000, "cost_unit": "USD", "cost_basis": "installed", "cost_alternates": []}},{f'\n    "recommendations": [],' if artifact_type == "base_case" else ""}
          "evidence_text": "...",
          "confidence": 0.92
        }}
      }}
      """

    return prompt


def generate_prompt(
    artifact_type: str,
    rules: List[str],
    add_edges: bool = False,
    objective_type: Optional[str] = None,
    objective_target: Optional[str] = None,
    objective_unit: Optional[str] = None,
    objective_description: Optional[str] = None,
) -> str:

    recommendation_section = f"""

    RECOMMENDATION-BASED ENTITY EXTRACTION: 

    Before extracting entities, identify comprehensive recommendations to achieve the objective: {objective_type} {objective_target} {objective_unit or "%"} {objective_description or ""}.

    Generate relevant recommendations for the objective across:
    - Equipment: Upgrades, replacements, additions, technology improvements
    - Materials: Raw materials, consumables, feedstocks, product specifications (e.g., concrete, metals, chemicals, liquids, gases, etc.)
    
    **THE RECOMMENDATIONS MUST:**
    - Directly relate to the objective
    - Be specific and detailed in the rationale field
    - Be categorized as PRIMARY or SECONDARY
      - PRIMARY: High-impact, direct solutions
      - SECONDARY: Supporting changes
    - Have the following fields: id, type, name, rationale, relevance, change_direction, change_magnitude, evidence_text, confidence, cost information (if available).
    - Be embedded in entity.properties.recommendations arrays.
    """

    msio_ontology_section = f"""
    MANDATORY MSIO CLASSIFICATION WORKFLOW:
    
    Map entities to the below Mining System Integration Ontology (MSIO).
    {MSIO_ONTOLOGY_TEXT}
    
    Classification workflow;
    STEP 1: Identify entity name/description from text
    STEP 2: Match to Discipline (case-insensitive, fallback to "Miscellaneous")
    STEP 3: Match to Category within Discipline (fallback to "Miscellaneous")
    STEP 4: Match to Subcategory within Category (fallback to "Miscellaneous")
    STEP 5: Match to Entity within Subcategory (fallback to "Miscellaneous")
    STEP 6: Extract attributes from NODE_PROPERTIES and MSIO ontology
      - Create attribute objects: name, value, unit, evidence_text, confidence
      - If attribute not present, set value and unit to null
      - Store cost info in properties.cost (not attributes array)

    Examples:
      - "Two centrifugal pumps 500 gpm at 120 ft head" → Discipline: "Mechanical Equipment", Category: "Pumps", Subcategory: "Centrifugal", Entity: "Base pump unit", Attributes: Design flowrate (500 gpm), Head (120 ft)

      - "Storage tank with fixed roof" → Discipline: "Mechanical Equipment", Category: "Tanks", Subcategory: "Storage Tank", Entity: "Fixed Roof"
    """
    nodes_section = f"""
    - MANDATORY NODE OBJECT:
      - Generate all types of nodes: Equipment, Material, Process, Product, and others (if applicable)
      - Match each node to the text
      - If an entity cannot be matched to MSIO ontology, create a new node with the closest MSIO hierarchy match and set "outside_msio": true attribute
      - If Total Installed Cost (TIC) or Total Capital Cost (TCC) are mentioned, extract the cost value and currency as separate properties
      - Use the MSIO matching workflow above for every entity extraction
      - DEDUPLICATE entities following the Entity Deduplication and Merging Policy (see above)
    - NODE OBJECT: Node object (each item in extract_nodes.nodes) MUST have:
      - "id": MUST be a valid UUID (RFC 4122 format, e.g., "550e8400-e29b-41d4-a716-446655440000")
      - "type": one of NODE_TYPES; a Node object must have a type
      - "properties": object/dict containing:
        • MANDATORY MSIO fields (all must be present and match ontology):
          - "discipline": string (MUST match an MSIO Discipline name exactly)
          - "category": string (MUST match an MSIO Category name within that Discipline)
          - "subcategory": string (MUST match an MSIO Subcategory name within that Category)
          - "entity": string (MUST match an MSIO Entity name within that Subcategory, or closest match)
        • MANDATORY Attributes:
          - "attributes": array of attribute objects 
            - "name": string (attribute name, e.g., Design flowrate, Head, NPSH, Spec, Reagent, Attributes, etc.)
            - "value": number|null (attribute value)
            - "unit": string|null (attribute unit)
            - "evidence_text": string|null (text snippet used to extract attribute)
            - "confidence": 0.0-1.0 (confidence score for this attribute)
        • For `Material` nodes, use attributes with names such as "material_class", "phase",
          "composition", "density", "heating_value", "unit_cost", "unit_cost_basis",
          "carbon_intensity", whenever the text provides them.
        • For `Stream` and `WasteStream` nodes, use attributes with names such as "stream_type",
          "basis", "flow_rate", "flow_unit", "solids_fraction", "temperature", "pressure".

    """

    edges_section = f"""
    Edge object (each item in extract_edges.edges) MUST have:
    - "source": node id
    - "target": node id
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
      • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
      • any domain attributes the ontology expects for that edge (if any)
    """
    output_section = f"""
      OUTPUT: Return nodes with extract_nodes(nodes=[...]){" and edges with extract_edges(edges=[...])" if add_edges else ""}.

      Each node example:
      {{
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "Equipment",
        "properties": {{
          "name": "Centrifugal Pump 500 gpm",
          "discipline": "Mechanical Equipment",
          "category": "Pumps",
          "subcategory": "Centrifugal",
          "entity": "Base pump unit",
          "attributes": [
            {{"name": "Design flowrate", "value": 500, "unit": "gpm", "evidence_text": "500 gpm", "confidence": 0.95}}
          ],
          "cost": {{"cost_value": 400000, "cost_min":40000, "cost_max": 80000, "cost_unit": "USD", "cost_basis": "installed", "cost_alternates": []}},
          {f'\n    "recommendations": [],' if artifact_type == "base_case" else ""}
          "evidence_text": "...",
          "confidence": 0.92
        }}
      }}
    """

    # Build rules sections conditionally
    rules_sections = ""
    if rules:
        if "UNITS_NORMALIZATION" in rules:
            rules_sections += f"{units_normalization_block}\n\n"
        if "TABLE_EXTRACTION" in rules:
            rules_sections += f"{table_extraction_block}\n\n"
        if "GLOBAL_OBJECTIVES" in rules:
            rules_sections += f"{global_objectives_block}\n\n"
        if "PROVENANCE_AND_CONFIDENCE" in rules:
            rules_sections += f"{prov_conf_block}\n\n"

    # Always include cost extraction block
    rules_sections += f"{cost_extraction_block}\n\n"

    base_prompt = f"""
      -------------------------------------------------------------------------------
      CONTEXT: Engineers and Cost Estimators use system design reports (referred to as base case documents) to design and optimize systems to plan capital-intensive installations and operations. The reports consist of details on technical requirements, equipment and material, process, operations, capital expenditure(CAPEX) and operating expenditure(OPEX) costs, constraints, assumptions, exclusions, and policy information on project requirements. Our system ingests the reports and extracts all the relevant information and factors (referred to as extracted entities), which is then used for cost estimation and analysis. Entities are structured data about factors such as equipment, material, process, constraints, cost items, and so on. Our system employs an ontology to map the extracted entities to a standard classification system (referred to as Mining System Integration Ontology (MSIO)).

      ROLE: Extract clean, deduplicated entities from mining/process-engineering content aligned to the provided Mining System Integration Ontology (MSIO). Map entities to MSIO hierarchy (Discipline → Category → Subcategory → Entity).

      {recommendation_section if artifact_type == "base_case" else ""}

      {msio_ontology_section}

      {nodes_section}

      {edges_section if add_edges else ""}

      {rules_sections}

      {output_section}
      """
    return base_prompt
