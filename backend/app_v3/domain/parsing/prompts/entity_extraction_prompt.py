from typing import Dict, Any, List, Optional
import json

# Import from app_v2 ontology
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

# Deduplication block
entity_deduplication_block = """
    --------------------------------------------------------------------------------
    = = = ENTITY DEDUPLICATION AND MERGING POLICY = = =
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
      "id": "salt_slurry_process_001",
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
      "id": "pump_001",
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
nodes_and_relations_extraction_directives = """
    --------------------------------------------------------------------------------
    = = = NODES AND RELATIONS EXTRACTION = = =
    --------------------------------------------------------------------------------
    NODES AND RELATIONS EXTRACTION:
    Using ontology.NODE_TYPES and ontology.EDGE_TYPES, extract all nodes and their relationships
    from the document. Include all relevant metadata and provenance information.

    You MUST:
    - Extract only what is explicitly or strongly implied by the input text.
    - Do not infer or assume information not present.
    - Emit only node/edge types that appear in the ontology.
    - Each node must have a type or property["label"] that maps to NODE_TYPES.
    - Use only node/edge property names that appear in the ontology metadata lists.
    - Attach evidence and a confidence score to every node and edge using the
    allowed property names from NODE_PROPERTIES / EDGE_PROPERTIES.
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

    OUTPUT CONTRACT (strict):
    Node object (each item in extract_nodes.nodes) MUST have:
    - "id": stable unique string identifier (uuid)
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
    - "source": node id
    - "target": node id
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
        • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
        • any domain attributes the ontology expects for that edge (if any)
        • include evidence/confidence meta-properties from EDGE_PROPERTIES

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
        "id": "uuid-or-stable",
        "source": "<node_id_element>",
        "target": "<node_id_subcategory>",
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
        "id": "mech_pump_001",
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

  STEP 6: Extract Attributes
  - For each NOD_TYPE entity, extract the attributes from the text based on the properties in NODE_PROPERTIES
  - [Required] Extract all possible attributes from the text
  - Create an object for each attribute with the following properties:
    * "name": the attribute name
    * "value": the attribute value
    * "unit": the attribute unit
    * "evidence_text": the text that was used to extract the attribute
    * "confidence": the confidence score for the attribute
  - Additionally, check the "attributes" list in the MSIO_ONTOLOGY entity ontology
    - Normalize attribute fields per the Attribute Extraction rules
      * [Required] If the attribute is not present in the text, set the attribute value to null and the attribute unit to null
      ** For example, if the attribute is "Design flowrate", and the text says "500 gpm", then the attribute value should be 500 and the attribute unit should be "gpm"
      ** if the attribute "Design flowrate" is not present in the text, then the attribute value should be null and the attribute unit should be null


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

  {nodes_and_relations_extraction_directives}
  """


def get_entity_extraction_prompt(rules: Optional[List[str]] = None) -> str:
    """Builds a prompt for base-case extraction with a simple ontology mapper."""

    prompt = f"""\
      --------------------------------------------------------------------------------
      BASE-CASE EXTRACTION
      --------------------------------------------------------------------------------

      ROLE
      Produce a clean, deduplicated entities and relationships for mining/process-engineering content aligned to the configured Mining System Integration Ontology (MSIO/msio). You read a base-case report (text/tables) and extract entities that match the MSIO hierarchy (Discipline → Category → Subcategory → Entity). If an entity cannot be matched to MSIO ontology, create a new node with the entity name and the MSIO hierarchy that is closest to the entity name (e.g., "Concrete Spread Footings" -> "Concrete" -> "Foundations" -> "Footings" -> "Spread footings") and set the attribute "outside_msio" to true. You then emit a single JSON object with nodes and edges, plus evidence and confidence.

      --------------------------------------------------------------------------------
      INPUTS AND OUTPUTS
      --------------------------------------------------------------------------------
      # NODES & RELATIONS EXTRACTION RULES
      {nodes_and_relations_extraction_block}

      # ONTOLOGY MAPPING
      {msio_classification_workflow}


      # ENTITY DEDUPLICATION (MANDATORY - MERGE DUPLICATE NODES)
      {entity_deduplication_block}
      
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
      ✓ Do: in the MSIO hierarchy,split only the Entity/Element field on “/” when classifying ontology rows.
      ✓ Do: extract attributes near the mention; split number/unit when clear.

      
      ✗ Don’t: invent elements or attributes not evidenced in the text/table.
      ✗ Don’t: split on “/” in other MSIO hierarchy fields (Subcategory, Category, Discipline).


      --------------------------------------------------------------------------------
      FINAL VALIDATION REMINDER
      --------------------------------------------------------------------------------
      Before calling extract_nodes(), verify:
      1. Every possible entities are found
      2. Map entities to MSIO Ontology: discipline/category/subcategory/entity values exist, else set to "Miscellaneous"
      3. Confidence scores reflect MSIO matching quality (exact match = 0.9-1.0, partial = 0.7-0.8, inferred = <0.7)


      --------------------------------------------------------------------------------
      FINAL DELIVERABLE
      --------------------------------------------------------------------------------
      Return nodes with extract_nodes(nodes=[...]), edges with extract_edges(edges=[...]), 
      scenarios with extract_scenarios(scenarios=[...]), recommendations with extract_recommendations(recommendations=[...]), and extract structured report with extract_structured_report(base_case_report={{...}}) as per the output contract.
      """

    return prompt


def get_targeted_entity_extraction_prompt(
    relevant_entities: Optional[List[Dict[str, Any]]] = None,
    extraction_scope: str = "exact",
    rules: Optional[List[str]] = None,
) -> str:
    """
    Build a prompt for targeted entity extraction based on relevant entities.

    Args:
        relevant_entities: List of entity specifications from recommendations
        extraction_scope: "exact" (only specified entities), "with_relationships"
        (entities + direct relationships), or "with_context"
        (entities + related entities in same context)
        rules: Optional list of extraction rules to enable

    Returns:
        Prompt string for targeted entity extraction
    """
    # Get base prompt
    base_prompt = get_entity_extraction_prompt(rules=rules)

    if not relevant_entities:
        # If no relevant entities provided, return base prompt
        return base_prompt

    # Build targeted extraction section
    entities_spec = []
    for idx, entity in enumerate(relevant_entities, 1):
        # Handle full node structure
        entity_id = entity.get("id", f"entity_{idx}")
        entity_type = entity.get("type", "Unknown")
        props = entity.get("properties", {})

        # Extract fields from properties
        entity_name = props.get("name", "Unknown")
        discipline = props.get("discipline", "N/A")
        category = props.get("category", "N/A")
        subcategory = props.get("subcategory", "N/A")
        msio_entity = props.get("entity", "N/A")
        expected_attrs = props.get("expected_attributes", [])
        evidence_locs = props.get("evidence_locations", [])
        rationale = props.get("extraction_rationale", "")
        priority = props.get("extraction_priority", "medium")

        spec = f"""
    Entity {idx} (ID: {entity_id}):
    - Type: {entity_type}
    - Name: {entity_name}
    - MSIO Classification:
      * Discipline: {discipline}
      * Category: {category}
      * Subcategory: {subcategory}
      * Entity: {msio_entity}
    - Priority: {priority}
    - Expected Attributes: {', '.join(expected_attrs) if expected_attrs else 'All relevant attributes from ontology'}
    - Evidence Locations: {', '.join(evidence_locs[:5]) if evidence_locs else 'Search entire document'}
    - Rationale: {rationale[:200] if rationale else 'N/A'}...
    - Additional Properties: Extract all applicable properties from NODE_PROPERTIES as found in the text
"""
        entities_spec.append(spec)

    entities_list = "\n".join(entities_spec)

    # Determine extraction scope instructions
    if extraction_scope == "exact":
        scope_instruction = """
    EXTRACTION SCOPE: EXACT ENTITIES ONLY
    - Extract ONLY the entities listed above
    - Do NOT extract other entities, even if mentioned in the text
    - Focus on extracting comprehensive information for the specified entities
    - Extract all attributes, relationships, and properties for these entities
    - Penalize extracting fewer entities or sparse information
"""
    elif extraction_scope == "with_relationships":
        scope_instruction = """
    EXTRACTION SCOPE: SPECIFIED ENTITIES + DIRECT RELATIONSHIPS
    - Extract the entities listed above
    - Also extract entities that have direct relationships (edges) with the specified entities
    - Extract relationships between specified entities and related entities
    - Focus on comprehensive extraction for all entities in scope
"""
    else:  # with_context
        scope_instruction = """
    EXTRACTION SCOPE: SPECIFIED ENTITIES + RELATED CONTEXT ENTITIES
    - Extract the entities listed above
    - Also extract entities mentioned in the same context/sections as the specified entities
    - Extract entities that are part of the same system or process as specified entities
    - Extract comprehensive information for all entities in scope
"""

    targeted_section = f"""
    --------------------------------------------------------------------------------
    TARGETED ENTITY EXTRACTION MODE
    --------------------------------------------------------------------------------
    You are extracting entities in TARGETED MODE. This means you should focus on
    extracting specific entities that have been identified as relevant to the
    analysis objectives.
    
    {scope_instruction}
    
    RELEVANT ENTITIES TO EXTRACT:
    {entities_list}
    
    EXTRACTION REQUIREMENTS:
    - Extract ONLY entities that match the specifications above (or related entities if scope allows)
    - For each specified entity, extract as a COMPLETE NODE following the extract_nodes structure:
      * REQUIRED: id (unique identifier), type (from NODE_TYPES), properties (object)
      * REQUIRED: properties.name (entity name)
      * REQUIRED: properties.discipline, properties.category, properties.subcategory, properties.entity (MSIO classification)
      * REQUIRED: properties.attributes (array of attribute objects with name, value, unit, evidence_text, confidence)
      * Extract ALL applicable properties from NODE_PROPERTIES as found in the text
      * All attributes mentioned in expected_attributes list
      * All additional attributes found in the text
      * All relationships (edges) to other entities
      * Evidence text and confidence scores for all extracted information
    - Be comprehensive: extract as much detail as possible for each entity
    - Do NOT skip entities or extract sparse information
    - If an entity is mentioned multiple times, merge information from all mentions
    - Prioritize high-priority entities but extract all specified entities
    - ALL extracted nodes MUST follow the exact structure from extract_nodes tool:
      * id: string (unique identifier)
      * type: string (from NODE_TYPES enum)
      * properties: object containing all applicable NODE_PROPERTIES
      * properties must include MSIO classification (discipline, category, subcategory, entity)
      * properties must include attributes array with full attribute objects
    - Map ALL nodes to MSIO ontology following the matching workflow in nodes_and_relations_extraction_directives
    
    DEDUPLICATION (MANDATORY):
    - Apply Entity Deduplication and Merging Policy (see above)
    - Merge duplicate entities with same MSIO classification and similar names
    - Consolidate information from multiple chunks/mentions into single nodes
    - Store alternative units as separate attribute entries (e.g., GPM and gal/hr)
    - Preserve all evidence and information when merging
    - Return only deduplicated nodes (no duplicates)
    
    QUALITY REQUIREMENTS:
    ✓ Extract comprehensive information for each specified entity as COMPLETE NODES
    ✓ Include all attributes, relationships, and properties following extract_nodes structure
    ✓ Provide evidence text for all extracted information
    ✓ Set appropriate confidence scores based on MSIO match quality
    ✓ All nodes must have complete MSIO classification (discipline, category, subcategory, entity)
    ✓ All nodes must follow the exact extract_nodes structure with id, type, and properties
    ✓ DEDUPLICATE entities - merge duplicates following the deduplication policy
    ✓ Store alternative units as separate attributes (e.g., 3733 GPM and 223975 gal/hr as two attribute objects)
    ✓ Consolidate cross-chunk mentions into single nodes
    ✗ Do NOT extract entities not in the relevant_entities list (unless scope allows)
    ✗ Do NOT extract sparse or incomplete entity information
    ✗ Do NOT skip expected attributes if they are mentioned in the text
    ✗ Do NOT extract nodes without complete structure (id, type, properties)
    ✗ Do NOT create duplicate nodes for the same entity (same MSIO + similar name)
    ✗ Do NOT lose information when merging duplicates
    
    --------------------------------------------------------------------------------
"""

    # Insert targeted section after base prompt's role section but before ontology section
    # Find a good insertion point - after the role/objective section
    insertion_marker = "Required output:"
    if insertion_marker in base_prompt:
        parts = base_prompt.split(insertion_marker, 1)
        return parts[0] + targeted_section + insertion_marker + parts[1]
    else:
        # Fallback: prepend to base prompt
        return targeted_section + "\n" + base_prompt


##### Recommendation-based entity extraction prompt #####

# Nodes and relations extraction block
objective_driven_nodes_and_relations_extraction_directives = f"""
    --------------------------------------------------------------------------------
    = = = OBJECTIVE-DRIVEN NODES AND RELATIONS EXTRACTION = = =
    --------------------------------------------------------------------------------

    Using NODE_TYPES and ontology.EDGE_TYPES, extract all nodes and their relationships
    from the document that are relevant to the objective goal and target. Include all relevant metadata and provenance information.

    You MUST:
    - Extract only what is explicitly or strongly implied by the input text.
    - Do not infer or assume information not present.
    - Emit only node/edge types that appear in the ontology.
    - Each node must have a type or property["label"] that maps to NODE_TYPES.
    - **CRITICAL: NEVER create nodes with type='Recommendation' or type='Recommendations'. Recommendations MUST be embedded within entity properties.recommendations array, NOT as separate nodes.**
    - Use only node/edge property names that appear in the ontology metadata lists.
    - Attach evidence and a confidence score to every node and edge using the
    allowed property names from NODE_PROPERTIES / EDGE_PROPERTIES.
    - Normalize entity names and deduplicate obvious variants.
    - EVERY node MUST have MSIO (Mining System Integration Ontology) ontology classification (discipline, category, subcategory, entity)
    - EVERY node MUST match the MSIO ontology hierarchy as closely as possible
    - Use ONLY Discipline/Category/Subcategory/Entity names from the provided MSIO ontology
    - If an entity cannot be matched to MSIO ontology, create a new node with the closest MSIO hierarchy match and set "outside_msio": true attribute
    - Find entities with total costs e.g., Total Installed Cost (TIC) or Total Capital Cost (TCC) and extract the cost value and currency as separate properties
    - Use the MSIO matching workflow above for every entity extraction
    - DEDUPLICATE entities following the Entity Deduplication and Merging Policy (see above)
    - **For each recommendation found in the text, identify the relevant entity (Equipment, Process, Material, etc.) and add the recommendation to that entity's properties.recommendations array. DO NOT create a separate Recommendation node.**


    ONTOLOGY:
    Allowed node types and node properties:
    {NODE_TYPES}
    
    {NODE_PROPERTIES}

    Allowed edge types and edge properties:
    {EDGE_TYPES}
    
    {EDGE_PROPERTIES}

    OUTPUT CONTRACT (strict):
    Node object (each item in extract_nodes.nodes) MUST have:
    - "id": stable unique string identifier (uuid)
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
          - "recommendations": array of recommendation objects (see STEP 6 under 'RECOMMENDATION-BASED ENTITY EXTRACTION')
            - "id": string (unique identifier for the recommendation)
            - "type": string (one of RECOMMENDATION_TYPES)
            - "name": string (recommendation name)
            - "rationale": string (recommendation rationale)
            - "relevance": string (one of RELEVANCE_TYPES)
            - "change_direction": string (one of CHANGE_DIRECTION_TYPES)
            - "change_unit": string (one of CHANGE_UNIT_TYPES)
            - "change_magnitude": string (one of CHANGE_MAGNITUDE_TYPES)
            - "change_magnitude_unit": string (one of CHANGE_MAGNITUDE_UNIT_TYPES)
            - "change_magnitude_direction": string (one of CHANGE_MAGNITUDE_DIRECTION_TYPES)
            - "evidence_text": string|null (text snippet used to extract recommendation)
            - "confidence": 0.0-1.0 (confidence score for this recommendation)
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


    Edge object (each item in extract_edges.edges) MUST have:
    - "source": node id
    - "target": node id
    - "type": one of EDGE_TYPES
    - "properties": object/dict containing ONLY:
        • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
        • any domain attributes the ontology expects for that edge (if any)
        • include evidence/confidence meta-properties from EDGE_PROPERTIES

    EXAMPLES:
    - Node example: {{ontology.get("NODE_PROP_EXAMPLE", "{{}}")}}
    - Edge example: {{ontology.get("EDGE_PROP_EXAMPLE", "{{}}")}}


    QUALITY GATE (pre-return):
    - Every node: non-empty, unique 'id' (uuid), valid 'type', and a 'properties' dict.
    - Every node has a 'name' property; populate it with the proper entity name.
    - Every node has a 'type' property that matches NODE_TYPES.
    - **CRITICAL VALIDATION: NO nodes with type='Recommendation' or type='Recommendations' are allowed. All recommendations must be in properties.recommendations arrays of entity nodes.**
    - Every node property key matches NODE_PROPERTIES.
    - Every node must have a 'recommendations' array (can be empty if no recommendations found for that entity).
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
    - **REJECT any node with type='Recommendation' or type='Recommendations' - recommendations belong in properties.recommendations, not as separate nodes.**

    Return:
    - nodes with extract_nodes(nodes=[...])
    - edges with extract_edges(edges=[...])


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
            "outside_msio": boolean,           // Whether the entity is outside the MSIO ontology
            "global_objective_goal": "string", // The global objective goal
            "global_objective_target": "string", // The global objective target
            "attributes": [                     // Array of attribute objects (see STEP 6)
                {{
                    "name": "string",           // Attribute name from ontology (e.g., "Design flowrate")
                    "value": "number|null",     // Attribute value (e.g., 500) or null if not present
                    "unit": "string|null",      // Attribute unit (e.g., "gpm") or null if not present
                    "evidence_text": "string|null", // Text snippet used to extract attribute
                    "confidence": 0.0-1.0        // Confidence score for this attribute
                }},
                {{
                    "cost_value": "number|null",     // Cost value (e.g., 100000) or null if not present
                    "currency": "string|null",      // Currency (e.g., "USD") or null if not present
                    "basis_year": "string|null",    // Basis year (e.g., "2024") or null if not present
                    "evidence_text": "string|null", // Text snippet used to extract cost value and currency
                    "confidence": 0.0-1.0        // Confidence score for this cost value and currency
                }},
                {{
                    "name": " ",
                    "value": "currency_1",
                    "unit": "currency_1",
                    "evidence_text": "evidence_text_2",
                    "confidence": 0.9,
                }},
                {{
                    "name": "basis_year",
                    "value": "basis_year_1",
                    "unit": "basis_year_1",
                    "evidence_text": "evidence_text_3",
                    "confidence": 0.9,
                }}
            ],
            "recommendations": [
                {{
                    "id": "recommendation_1",
                    "type": "recommendation",
                    "name": "recommendation_name_1",
                    "rationale": "recommendation_rationale_1",
                    "relevance": "primary", # ["primary", "secondary", "other"]
                    "change_direction": "increase", # ["increase", "decrease", "no change"]
                    "change_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                    "change_magnitude": "100", # ["100", "200", "300", etc.]
                    "change_magnitude_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                    "change_magnitude_direction": "increase", # ["increase", "decrease", "no change"]
                    "evidence_text": "evidence_text_1", # text snippets, page numbers, section references
                    "confidence": 0.9, # [0.0-1.0]; 1.0 is the highest confidence
                }}
            ],
            "evidence_text": "short supporting snippet", # Evidence snippet
            "confidence": 0.0-1.0                        # Confidence score (0.0 to 1.0)
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
              "evidence_text": "short supporting snippet",
              "confidence": 1.0
          }}
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
        "id": "mech_pump_001",
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
            "recommendations": [
                {{
                    "id": "recommendation_1",
                    "type": "recommendation",
                    "name": "recommendation_name_1",
                    "rationale": "recommendation_rationale_1",
                    "relevance": "primary", # ["primary", "secondary", "other"]
                    "change_direction": "increase", # ["increase", "decrease", "no change"]
                    "change_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                    "change_magnitude": "100", # ["100", "200", "300", etc.]
                    "change_magnitude_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                    "change_magnitude_direction": "increase", # ["increase", "decrease", "no change"]
                    "evidence_text": "evidence_text_1", # text snippets, page numbers, section references
                    "confidence": 0.9, # [0.0-1.0]; 1.0 is the highest confidence
                }}
            ],
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


def get_recommendation_based_entity_extraction_prompt() -> str:
    """
    Build a prompt for recommendation-based entity extraction based on global objective goal and target. The prompt seeks to build entities and embed recommendations and rationale within the entities. The prompt is assembled in the following steps:
    1. The prompt directs the LLM to exhaustive find all possible ways to achieve the global objective goal and target.
    2. The recommendations can be primary, secondary, or other.
    3. For each recommendation, the prompt directs the LLM to build a complete node structure for the entity that is relevant to the recommendation.
    4. The prompt directs the LLM to return the entities and recommendations in the following format:
    {
        "entities": [
            {
                "id": "entity_1",
                "name": "entity_1",
                "type": "entity",
                "properties": {
                    "msio_discipline": "discipline_1",
                    "msio_category": "category_1",
                    "msio_subcategory": "subcategory_1",
                    "msio_entity_type": "entity_type_1",
                    "outside_msio": false,
                    "global_objective_goal": "global_objective_goal_1",
                    "global_objective_target": "global_objective_target_1",
                    "attributes": [
                        {
                            "name": "attribute_1",
                            "value": "value_1",
                            "unit": "unit_1",
                            "evidence_text": "evidence_text_1",
                            "confidence": 0.9,
                        },
                        {
                            "name": "attribute_2",
                            "value": "value_2",
                            "unit": "unit_2",
                            "evidence_text": "evidence_text_2",
                            "confidence": 0.8,
                        },{
                          "name": "cost_value",
                          "value": "cost_value_1",
                          "unit": "currency_1",
                          "evidence_text": "evidence_text_1",
                          "confidence": 0.9,
                        },
                        {
                          "name": "currency",
                          "value": "currency_1",
                          "unit": "currency_1",
                          "evidence_text": "evidence_text_1",
                          "confidence": 0.9,
                        },
                        {
                          "name": "basis_year",
                          "value": "basis_year_1",
                          "unit": "basis_year_1",
                          "evidence_text": "evidence_text_1",
                          "confidence": 0.9,
                        }
                    ],
                    "recommendations": [
                        {
                            "id": "recommendation_1",
                            "type": "recommendation",
                            "name": "recommendation_name_1",
                            "rationale": "recommendation_rationale_1",
                            "relevance": "primary", # ["primary", "secondary", "tertiary"]
                            "change_direction": "increase", # ["increase", "decrease", "no change"]
                            "change_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                            "change_magnitude": "100", # ["100", "200", "300", etc.]
                            "change_magnitude_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                            "change_magnitude_direction": "increase", # ["increase", "decrease", "no change"]
                            "change_magnitude_unit": "gpm", # ["gpm", "tons/hr", "units/day", etc.]
                            "evidence_text": "evidence_text_1", # text snippets, page numbers, section references
                            "confidence": 0.9, # [0.0-1.0]; 1.0 is the highest confidence
                        }
                    ]
                }
            }
        ],
        "relationships": [
          {
            "id": "relationship_1",
            "type": "relationship",
            "name": "relationship_name_1",
            "source_entity_id": "entity_1",
            "target_entity_id": "entity_2",
            "type": "relationship_type_1", # ["PART_OF", "CONTAINS", "USES", "PRODUCES", "CONSUMES", "OTHER"]
            "properties": {
              "evidence_text": "evidence_text_1", # text snippets, page numbers, section references
              "confidence": 0.9, # [0.0-1.0]; 1.0 is the highest confidence
            }
          }
        ]
    }
    """

    base_prompt = f"""
      --------------------------------------------------------------------------------
      RECOMMENDATION-BASED ENTITY EXTRACTION
      --------------------------------------------------------------------------------

      You are an expert process engineer and cost estimator. You are given a global objective goal and target.
      You are tasked with exhaustively finding all possible ways to achieve the global objective goal and target.
      You are to return the entities and recommendations in the following format:
      1. Comprehensively analyze the base case document in the context of the global objective goal (type) and target (magnitude of change).
      2. Identify a COMPREHENSIVE set of recommendations (aim for 15-30+ recommendations) categorized as:
          - PRIMARY recommendations (5-10): High-impact, direct solutions that directly address the objective
          - SECONDARY recommendations (5-10): Supporting changes that enhance or enable primary recommendations
          - OTHER recommendations (5-10): Alternative approaches, lower-priority options, or innovative solutions
      3. Explore ALL aspects of the system across multiple categories:
          - Equipment Upgrades: Capacity increases, replacements, additions, technology upgrades
          - Process Optimization: Flow improvements, efficiency gains, throughput enhancements
          - Operational Changes: Shift patterns, staffing, procedures, scheduling
          - Infrastructure: Utilities, buildings, site work, foundations, structures
          - Material Changes: Raw materials, consumables, feedstocks, product specifications
          - Control Systems: Automation, instrumentation, SCADA, control logic
          - Energy Efficiency: Power consumption, heat recovery, waste minimization
          - Maintenance Strategy: Reliability improvements, preventive maintenance, spare parts
          - Safety Enhancements: Safety systems, procedures, equipment, training
          - Environmental Improvements: Emissions reduction, waste treatment, compliance
      4. For each recommendation, classify it with:
          - recommendation_category: "primary", "secondary", or "other"
          - type: Specific category (e.g., "Equipment Upgrade", "Process Optimization", etc.)
          - estimated_cost_range: Rough cost estimate
          - time_to_implement: Implementation timeline
          - dependencies: Other recommendations this depends on (if any)
          - alternative_to: Alternative approaches to other recommendations (if any)
      5. Identify ALL entities relevant for achieving each recommendation.

      --------------------------------------------------------------------------------
      ENTITY EXTRACTION RULES
      --------------------------------------------------------------------------------

      Produce a clean, deduplicated entities and relationships mapped to global objective goal and target for mining/process-engineering content aligned to the configured Mining System Integration Ontology (MSIO/msio). You read a base-case report (text/tables) and extract entities that match the MSIO hierarchy (Discipline → Category → Subcategory → Entity). If an entity cannot be matched to MSIO ontology, create a new node with the entity name and the MSIO hierarchy that is closest to the entity name (e.g., "Concrete Spread Footings" -> "Concrete" -> "Foundations" -> "Footings" -> "Spread footings") and set the attribute "outside_msio" to true. You then emit a single JSON object with nodes and edges, plus evidence and confidence.

      --------------------------------------------------------------------------------
      INPUTS AND OUTPUTS
      --------------------------------------------------------------------------------

      # NODES & RELATIONS EXTRACTION RULES
      {objective_driven_nodes_and_relations_extraction_directives}

      # ONTOLOGY MAPPING
      {msio_classification_workflow}


      # ENTITY DEDUPLICATION (MANDATORY - MERGE DUPLICATE NODES)
      {entity_deduplication_block}
      
      
      # PROVENANCE & CONFIDENCE
      {prov_conf_block}
    
    
      # UNIT NORMALIZATION & DEDUPLICATION
      {units_normalization_block}
      --------------------------------------------------------------------------------

      --------------------------------------------------------------------------------
      DO / DO NOT
      --------------------------------------------------------------------------------
      
      RECOMMENDATIONS (CRITICAL):
      ✓ Do: Exhaustively identify all recommendations (primary, secondary, other) that can achieve the global objective.
      ✓ Do: For each recommendation, identify the relevant entity/entities (Equipment, Process, Material, etc.) and embed the recommendation in each entity's properties.recommendations array.
      ✓ Do: Include complete recommendation details: id, type, name, rationale, relevance (primary/secondary/other), change_direction, change_magnitude, evidence_text, and confidence.
      ✗ Don't: Create nodes with type='Recommendation' or type='Recommendations' - STRICTLY FORBIDDEN.
      ✗ Don't: Create separate nodes for recommendations - they MUST be embedded in properties.recommendations arrays of entity nodes.
      
      ENTITY EXTRACTION:
      ✓ Do: Identify all entities (Equipment, Process, Material, Control, Infrastructure, etc.) relevant to achieving the global objective.
      ✓ Do: Extract complete entity information: MSIO classification, attributes, relationships, and associated recommendations.
      ✓ Do: Create entity nodes for all relevant entities, even if they don't have explicit recommendations (recommendations array can be empty).
      ✓ Do: Map entities to MSIO ontology (discipline → category → subcategory → entity) with highest possible specificity.
      ✗ Don't: Extract entities that are not relevant to the global objective - focus on objective-driven extraction.
      
      DATA QUALITY:
      ✓ Do: Produce clean, deduplicated entities following the Entity Deduplication and Merging Policy.
      ✓ Do: Include evidence_text and confidence scores for all extracted information (entities, attributes, recommendations).
      ✓ Do: Set confidence scores based on MSIO matching quality: exact match = 0.9-1.0, partial = 0.7-0.8, inferred = <0.7.
      ✓ Do: Follow the strict output contract: single JSON object with nodes and edges.
      ✗ Don't: Hallucinate entities, relationships, recommendations, or properties not present in the text.
      ✗ Don't: Infer information not explicitly or strongly implied by the input text.

      --------------------------------------------------------------------------------
      FINAL DELIVERABLE
      --------------------------------------------------------------------------------
      Return nodes with extract_nodes(nodes=[...]), edges with extract_edges(edges=[...]) as per the output contract.

      """

    return base_prompt
