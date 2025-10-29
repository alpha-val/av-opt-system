"""
build_prompt_basecase.py
Alpha-Val Optionality – Base Case Extraction Prompt (v2, policy-bound)
----------------------------------------------------------------------
Generates a prescriptive prompt to extract a *Baseline* graph from
technical reports and tables, using the Alpha-Val ontology (Core + extensions).

Enhancements in v2:
- Accepts `rules: List[str]`. When "TABLE_EXTRACTION" is present, injects a
  strict TABLE EXTRACTION POLICY and binds it to behavior.
- Replaces/augments normalization with UNITS NORMALIZATION & DEDUPLICATION POLICY,
  including capacity parsing, unit mapping, min/max ranges, dual units, and
  "capacity variations" (+/-% and multipliers).
"""

from typing import Dict, Any, List


def _bulleted(lines: List[str]) -> str:
    return "\n".join(f"- {x}" for x in lines)


def _kv(d: Dict[str, Any]) -> str:
    return "\n".join(f"- {k}: {d[k]}" for k in d)


# --- Static policy blocks (verbatim from user) ---


def create_global_objects_block(objectives_spec: Dict[str, Any]) -> str:
    return f"""
    --------------------------------------------------------------------------------
    GLOBAL OBJECTS SUMMARY (FOR OPTIONALITY & COST ALTERNATIVES)
    --------------------------------------------------------------------------------
    Using global objective specs ({objectives_spec.get("description") or None}, build a consolidated summary of global
    objects mentioned in the base case text/tables and place it under:
      meta.global_objectives  (shape provided by the spec)

    Categories to extract:
    {', '.join(objectives_spec.get("categories", {}).keys())}
    Rules:
    1) Use the categories and node/edge mappings from global objective spec categories:
      - kpis → node_types: KPI
      - constraints → Constraint
      - cost → CostItem (+ HAS_COST/BREAKS_DOWN_TO/DERIVED_FROM/INDEXED_BY)
      - risk → Risk (+ HAS_RISK/REDUCES_RISK/INCREASES_RISK)
      - levers → Lever (+ ENABLES/AFFECTS_COST/IMPACTS_KPI)
      - alternatives → Alternative (+ ALTERNATIVE_TO/AFFECTS_COST/IMPACTS_KPI)
      - decision_variables → DecisionVariable
      - cost_drivers → CostDriver (+ DRIVES/AFFECTS_COST)
      - uncertainties → Uncertainty
      - assumptions → Assumption
      - schedule → Schedule/Milestone/Event (+ PRECEDES/FOLLOWS/CONTEMPORANEOUS_WITH/NEXT)
      - permits → Permit (+ PERMITTED_BY/REGULATED_BY)
      - data_gaps → DataGap

    2) For each item in a category:
      - Include the fields listed in the spec (e.g., KPI: name, formula, unit, direction).
      - Add a "refs" array of node_ids and edge_ids that support the summary item.
      - Add minimal provenance with sourceDoc/sourcePage where available.

    3) De-duplication:
      - If multiple nodes represent the same conceptual item (e.g., two risks with same name), merge and union their refs.

    4) Do NOT hallucinate categories not evidenced in the source.

    Output location:
    - Place the object under the single top-level key: "meta.global_objectives".
    - Conform to ontology.GLOBAL_OBJECTIVES_SPEC.output_shape keys; omit empty categories only if not present in spec.

    Example (schematic):
    "meta": {{
      "global_objectives": {{
        "kpis": [{{"name":"OPEX Intensity","unit":"USD/t","direction":"minimize","refs":["kpi_1"]}}],
        "constraints": [{{"name":"Power cap","expression":"powerKw <= 2500","refs":["constraint_7"]}}],
        "cost": [{{"name":"Primary crusher","price":{{"amount":2100000,"currency":"USD","currencyYear":2015}},"estimateClass":"AACE_Class_4","refs":["cost_12","edge_99"]}}],
        "risk": [{{"name":"Ore variability","risk_severity":"high","risk_probability":"likely","refs":["risk_3"]}}],
        "levers": [{{"name":"Vendor Selection","category":"Vendor","refs":["lever_1","alt_2","edge_40"]}}],
        "alternatives": [{{"name":"Vendor A","leverRef":"lever_1","assumptions":"FOB pricing","refs":["alt_2"]}}],
        "decision_variables": [{{"name":"Throughput","domain":"[500, 1500] tph","unit":"tph","defaultValue":800,"refs":["dv_1"]}}],
        "cost_drivers": [{{"name":"Power","driverType":"power","unit":"kW","refs":["driver_1","edge_55"]}}],
        "uncertainties": [{{"name":"Au grade","distribution":"lognormal(μ,σ)","low":0.6,"high":1.2,"refs":["unc_1"]}}],
        "assumptions": [{{"name":"Maintenance regime","short_description":"Preventive monthly","refs":["ass_2"]}}],
        "schedule": [{{"name":"Commissioning","time":{{"start":"2026-07-01T00:00:00Z"}},"refs":["ev_9"]}}],
        "permits": [{{"name":"Air Permit","issuingAuthority":"Region EPA","validFrom":"2024-01-10","refs":["permit_5"]}}],
        "data_gaps": [{{"name":"Missing vendor lead time","missingField":"leadTimeDays","context":"Vendor table lacks delivery info","refs":["tbl_4:r7c5"]}}]
      }}
    }}
    """


def create_node_extraction_block(ontology: dict, rules: List[str]) -> str:
    has_costrule = "CostRule" in ontology.get("NODE_TYPES", [])
    costrule_block = (
        """
      --------------------------------------------------------------------------------
      COST & METHOD POLICY (Enforced by Ontology)
      --------------------------------------------------------------------------------
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
      """
        if has_costrule
        else """
    --------------------------------------------------------------------------------
    COST POLICY (Ontology has no 'CostRule')
    --------------------------------------------------------------------------------
    * Do not create any 'CostRule' nodes.
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
    )

    units_normalization_block = """
      --------------------------------------------------------------------------------
      UNITS NORMALIZATION & DEDUPLICATION POLICY
      --------------------------------------------------------------------------------
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

    table_extraction_block = """
      --------------------------------------------------------------------------------
      TABLE EXTRACTION POLICY
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

    return f"""
    Extract a knowledge graph from the user's text.

    === Mission ===
    Produce a clean, deduplicated knowledge graph for mining/process-engineering content
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

    --------------------------------------------------------------------------------
    ONTOLOGY (from config.py)
    --------------------------------------------------------------------------------
    Allowed node types (NODE_TYPES):
    {_bulleted(ontology["NODE_TYPES"])}

    Allowed edge types (EDGE_TYPES):
    {_bulleted(ontology["EDGE_TYPES"])}

    --------------------------------------------------------------------------------
    TABLES
    --------------------------------------------------------------------------------
    Table extraction policy
    {table_extraction_block if 'TABLE_EXTRACTION' in rules else ''}

    --------------------------------------------------------------------------------
    COST EXTRACTION POLICIES
    --------------------------------------------------------------------------------
    Cost & Method policy
    {costrule_block if 'COST_RULE' in rules else ''}

    --------------------------------------------------------------------------------
    OUTPUT CONTRACT (strict)
    --------------------------------------------------------------------------------
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
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    NORMALIZATION & DEDUPLICATION RULES
    --------------------------------------------------------------------------------
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

    --------------------------------------------------------------------------------
    NORMALIZATION & DEDUPLICATION POLICY
    {units_normalization_block if 'UNITS_NORMALIZATION' in rules else ''}
    --------------------------------------------------------------------------------

    --------------------------------------------------------------------------------
    QUALITY GATE (pre-return)
    --------------------------------------------------------------------------------
    - Every node: non-empty, unique 'id' (uuid), valid 'type', and a 'properties' dict.
    - Every node has a 'name' property; populate it with the proper entity name.
    - Every node has a 'type' property that matches NODE_TYPES.
    - Every node property key matches NODE_PROPERTIES.
    - For nodes of type 'Equipment', 'Process', 'Material', 'Product', 'Waste', etc., acquire cost details if they appear in text.
    - For nodes of type 'CostRule', ensure compliance with COST & METHOD POLICY above.
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

    Return nodes with extract_nodes(nodes=[...]) and edges with extract_edges(edges=[...]).
    """


def gen_basecase_prompt(
    ontology: Dict[str, Any], rules: List[str] | None = None
) -> str:
    rules = rules or []

    node_types = ontology.get("CORE", {}).get("NODE_TYPES", [])
    edge_types = ontology.get("CORE", {}).get("EDGE_TYPES", [])
    node_props = ontology.get("CORE", {}).get("NODE_PROPERTIES", [])
    edge_props = ontology.get("CORE", {}).get("EDGE_PROPERTIES", [])
    ext = ontology.get("EXTENSIONS", {}).get("mining_process", {})
    node_types_ext = ext.get("NODE_TYPES_ADD", [])
    edge_types_ext = ext.get("EDGE_TYPES_ADD", [])

    templates = ontology.get("TEMPLATES", {})
    enums = ontology.get("ENUMS", {})
    mn = ontology.get("METRIC_NORMALIZATION", {})
    qg = ontology.get("QUALITY_GATE", {})
    syn = ontology.get("SYNONYMS", {})
    hints = ontology.get("EXTRACTION_HINTS", {})
    patterns = ontology.get("PATTERNS", {})
    defaults = ontology.get("DEFAULTS", {})

    quantity_shape = mn.get(
        "quantity_shape", {"value": "float", "unit": "unit_code", "basis": "string?"}
    )
    units_standard = mn.get("units_standard", "SI")
    power_unit = mn.get("power_unit", "kW")
    thr_examples = mn.get("throughput_unit_examples", ["tph"])
    price_examples = mn.get("price_unit_examples", ["USD/t"])
    grade_examples = mn.get("grade_unit_examples", ["%", "g/t", "ppm"])
    mn_policy = mn.get("policy", [])

    objectives_spec = ontology.get("GLOBAL_OBJECTIVES_SPEC", {})

    qg_edges_declared = qg.get("edges_must_use_declared_types", True)
    qg_singletons = qg.get("allow_singleton_nodes", True)
    qg_req_prov = qg.get(
        "require_provenance_fields", ["sourceDoc", "extractionMethod", "createdBy"]
    )
    qg_reject_on_templates = qg.get("reject_if_missing_required_template_fields", True)

    entity_patterns = hints.get("entity_patterns", [])
    table_aliases = hints.get("table_column_aliases", {})

    syn_lines = [f"{k}: {', '.join(v)}" for k, v in syn.items()]

    patt_lines = []
    for name, spec in patterns.items():
        nodes = spec.get("nodes", [])
        edges = spec.get("edges", [])
        patt_lines.append(f"{name} → nodes:{nodes} | edges:{edges}")

    basecase_targets = [
        "Project",
        "Site",
        "Facility",
        "Process",
        "ProcessStep",
        "Equipment",
        "EquipmentVariant",
        "Material",
        "Utility",
        "CostItem",
        "Quote",
        "Vendor",
        "Manufacturer",
        "Permit",
        "Schedule",
        "Milestone",
        "KPI",
        "Assumption",
        "Document",
        "Table",
        "Chunk",
    ]

    nodes_and_rels_extraction_block = create_node_extraction_block(ontology, rules)
    global_objectives_block = create_global_objects_block(objectives_spec)

    return f"""
================================================================================
ALPHA-VAL – BASE CASE EXTRACTION PROMPT (policy-bound, v2)
================================================================================
ROLE
You are an expert extraction system that reads a *base case* (baseline) report
and its tables to produce a typed knowledge graph consistent with the Alpha-Val
ontology. You MUST apply every policy below and prove compliance in the output.

--------------------------------------------------------------------------------
BASE CASE CONTRACT (MANDATORY)
1) Create exactly one node of type "Baseline" named "Base Case" (or report-native name).
2) All extracted facts MUST be *attachable* to this Baseline via edges:
   - Scenario (optional, if present) --BASELINES--> Baseline
   - Every entity discovered must be reachable from Baseline through the Project or
     the Facility (e.g., Project PART_OF Baseline, Facility PART_OF Project, Equipment PART_OF Area/PART_OF Facility).
3) Do NOT invent scenarios/options here; the goal is the *baseline configuration* as stated.

--------------------------------------------------------------------------------
ONTOLOGY CONTRACT (CANONICAL VOCAB)
{nodes_and_rels_extraction_block}
--------------------------------------------------------------------------------
GLOBAL OBJECTIVES EXTRACTION
{global_objectives_block}
--------------------------------------------------------------------------------

Use only declared labels. Each node must satisfy typed fields in TEMPLATES.

--------------------------------------------------------------------------------
BASE CASE TARGETS (PRIORITY ORDER)
Extract these if present, in this order:
{_bulleted(basecase_targets)}

Minimum viable pattern (if evidence exists):
- Project → Site → Facility
- Facility HAS_PART Area / Process / ProcessStep
- Equipment (classified) PART_OF Area or ProcessStep
- Equipment --HAS_COST--> CostItem (optional → Quote → Vendor)
- Materials/Utilities linked via FEEDS/CONSUMES/USES_UTILITY
- Permit → Facility/Process via PERMITTED_BY
- Schedule/Milestones if present
- KPIs/Assumptions for baseline metrics

--------------------------------------------------------------------------------
STRICT OUTPUT FORMAT (single JSON object)
{{
  "nodes": [
    {{
      "id": "stable_id-or-uuid",
      "type": "<NodeType>",
      "name": "string",
      "properties": {{
        {node_props},
        "provenance": {{
          "sourceDoc": "string",
          "sourcePage": "int?",
          "extractionMethod": "LLM",
          "createdBy": "AlphaVal"
        }}
      }}
    }}
  ],
  "edges": [
    {{
      "source": "<node_id>",
      "target": "<node_id>",
      "type": "<EdgeType>",
      "properties": {{
        {edge_props},
        "confidence": 0.0-1.0,
        "rationale": "short reason",
        "provenance": {{
          "sourceDoc": "string",
          "sourcePage": "int?",
          "extractionMethod": "LLM",
          "createdBy": "AlphaVal"
        }}
      }}
    }}
  ],
  "meta": {{
    "policyCompliance": {{
      "appliedPatterns": [],
      "synonymMappings": [],
      "tableAliasMappings": [],
      "normalizations": [],
      "defaultsUsed": [],
      "dedupe": {{"rulesApplied": [], "mergedPairs": []}},
      "qualityGate": {{
        "declaredEdgeTypesOnly": true/false,
        "singletonNodesAllowed": true/false,
        "provenanceFieldsPresent": true/false,
        "templatesSatisfied": true/false
      }}
    }},
    "global_objectives": {{
      "kpis": [{{"name":"OPEX Intensity","unit":"USD/t","direction":"minimize","refs":["kpi_1"]}}],
      "constraints": [{{"name":"Power cap","expression":"powerKw <= 2500","refs":["constraint_7"]}}],
      "cost": [{{"name":"Primary crusher","price":{{"amount":2100000,"currency":"USD","currencyYear":2015}},"estimateClass":"AACE_Class_4","refs":["cost_12","edge_99"]}}],
      "risk": [{{"name":"Ore variability","risk_severity":"high","risk_probability":"likely","refs":["risk_3"]}}],
      "levers": [{{"name":"Vendor Selection","category":"Vendor","refs":["lever_1","alt_2","edge_40"]}}],
      "alternatives": [{{"name":"Vendor A","leverRef":"lever_1","assumptions":"FOB pricing","refs":["alt_2"]}}],
      "decision_variables": [{{"name":"Throughput","domain":"[500, 1500] tph","unit":"tph","defaultValue":800,"refs":["dv_1"]}}],
      "cost_drivers": [{{"name":"Power","driverType":"power","unit":"kW","refs":["driver_1","edge_55"]}}],
      "uncertainties": [{{"name":"Au grade","distribution":"lognormal(μ,σ)","low":0.6,"high":1.2,"refs":["unc_1"]}}],
      "assumptions": [{{"name":"Maintenance regime","short_description":"Preventive monthly","refs":["ass_2"]}}],
      "schedule": [{{"name":"Commissioning","time":{{"start":"2026-07-01T00:00:00Z"}},"refs":["ev_9"]}}],
      "permits": [{{"name":"Air Permit","issuingAuthority":"Region EPA","validFrom":"2024-01-10","refs":["permit_5"]}}],
      "data_gaps": [{{"name":"Missing vendor lead time","missingField":"leadTimeDays","context":"Vendor table lacks delivery info","refs":["tbl_4:r7c5"]}}]
    }}
  }}
}}

KEYS:
- lowerCamelCase property names (e.g., powerKw, throughput, costBasis).
- For quantities/money, emit both raw and normalized when conversion occurred.

--------------------------------------------------------------------------------
POLICY 1 — UNITS NORMALIZATION & DEDUPLICATION (BOUND)
See the node extraction block.

Additionally, align with ontology METRIC_NORMALIZATION:
- quantity shape: {quantity_shape}
- preferred: power={power_unit}; throughput={', '.join(thr_examples)}; price={', '.join(price_examples)}; grade={', '.join(grade_examples)}
Normalization principles:
{_bulleted(mn_policy) if mn_policy else "- Preserve source + add normalized fields; include currencyYear for money."}

Name pairs (STRICT examples):
- powerKwRaw / powerKwNorm
- throughputRaw / throughputNorm
- priceRaw / priceNorm
- gradeRaw / gradeNorm
- capacity_value(_min/_max), capacity_unit(_imperial/_metric)

--------------------------------------------------------------------------------
POLICY 2 — QUALITY_GATE (BOUND)
- edges_must_use_declared_types = {qg_edges_declared} ⇒ Only ontology EDGE_TYPES allowed.
- allow_singleton_nodes = {qg_singletons} ⇒ Singleton nodes {("allowed" if qg_singletons else "not allowed")}.
- require_provenance_fields = {qg_req_prov} ⇒ Present on EVERY node/edge.
- reject_if_missing_required_template_fields = {qg_reject_on_templates} ⇒ If required missing, omit node.
- Confidence: omit facts with confidence < 0.40.

--------------------------------------------------------------------------------
POLICY 3 — SYNONYMS (BOUND; CANONICAL TYPE RESOLUTION)
Map source synonyms to canonical types before emission and log mapping.
{_bulleted(syn_lines) if syn_lines else "- (No synonyms provided.)"}

Record in meta.policyCompliance.synonymMappings as:
[{{"from":"machine","to":"Equipment"}}]

--------------------------------------------------------------------------------
POLICY 4 — EXTRACTION_HINTS (BOUND)
Entity patterns (prioritize):
{_bulleted(entity_patterns) if entity_patterns else "- (No entity patterns provided.)"}

Table header aliasing (apply BEFORE assigning field names):
{_kv(table_aliases) if table_aliases else "- (No table alias mapping.)"}

Log alias mappings under meta.policyCompliance.tableAliasMappings.

Global Objectives Specification:
{global_objectives_block}

Templates: {', '.join(templates.keys())}

--------------------------------------------------------------------------------
POLICY 5 — PATTERNS (BOUND; SATISFY WHEN EVIDENCE EXISTS)
Try to assemble nodes/edges to satisfy at least one relevant pattern:
{_bulleted(patt_lines) if patt_lines else "- (No patterns provided.)"}

For Base Case, prioritize:
- EquipmentWithCost
- MaterialPriceSeries (attach Currency)
- TemporalChain (Events → PRECEDES)

--------------------------------------------------------------------------------
POLICY 6 — DEFAULTS & FALLBACKS (BOUND)
Apply defaults only if the value is truly absent after aliasing & normalization.

Defaults:
{_kv(defaults) if defaults else "- (No defaults provided.)"}

Log any default used: meta.policyCompliance.defaultsUsed = [{{"field":"currency","value":"{defaults.get('currency','USD')}"}}]

--------------------------------------------------------------------------------
BASE CASE FIELD SHAPES (TEMPLATE-GUIDED; ABRIDGED)
Equipment (classification replaces flat types):
- required: stable_id(id), name(string)
- optional: equipment_class(path e.g., "Equipment/Crusher/Gyratory"),
            equipment_kind(enum {', '.join(enums.get('equipment_kind', []))}),
            manufacturer(string), model(string),
            powerKw(Quantity), throughput(Quantity),
            availabilityPct(float), provenance(Provenance)

Process / ProcessStep:
- Process: required stable_id, name
- ProcessStep: required stable_id, name; optional sequenceOrder(int), duty(text)

Material:
- required: stable_id, name
- optional: material_class(string e.g., "Ore","Reagent","Product"),
            grade(Quantity), bulkDensity(Quantity), moisture(Quantity),
            price(Money), composition(CompositionItem), provenance(Provenance)

CostItem:
- required: stable_id, name, price(Money)
- optional: costBasis(string), estimateClass(enum), errorPlusPct/MinusPct(float), effectiveDate(iso_date)

Facility / Site / Project:
- Facility: required stable_id, name, siteRef(id)
- Project: required stable_id, name, status(enum)
- Site: as Core Location/Site; link with LOCATED_IN

Permit:
- required: stable_id, name, issuingAuthority(string), validFrom(iso_date)

Quote / Vendor / Manufacturer:
- Equipment --HAS_COST--> CostItem --QUOTED_IN--> Quote --SUPPLIED_BY--> Vendor

Document / Table / Chunk:
- ALWAYS emit a Document for each source, Tables for structured content, and Chunks for quoted spans;
  connect factual nodes via :DERIVED_FROM / :MENTIONS

--------------------------------------------------------------------------------
CLASSIFICATION RULES (EQUIPMENT)
- Prefer a single Equipment node with:
  equipment_class: "Equipment/<family>/<subfamily>" (e.g., "Equipment/Crusher/Gyratory")
  equipment_kind: enum (Rotating, Fixed, Mobile, Electrical, Control)
- Do not create separate types for "Crusher", "Mill", "Pump".

--------------------------------------------------------------------------------
DE-DUPLICATION & VERSIONING (BOUND)
- Merge duplicates when same logical entity (type + manufacturer+model OR equipment_class+duty).
- Record merges under meta.policyCompliance.dedupe.mergedPairs.
- Superseding values → create new node and link with :REVISES (or :VERSION_OF).

--------------------------------------------------------------------------------
VALIDATE BEFORE EMITTING
1) Templates satisfied for each node type (required fields present).
2) Edge labels allowed by ontology; reject others.
3) Provenance present on every node/edge ({', '.join(qg_req_prov)}).
4) Confidence ≥ 0.40.
5) If evidence suffices, satisfy at least one minimal pattern.

--------------------------------------------------------------------------------
STRICT EXAMPLES (SCHEMATIC)

A) Equipment with Cost (Base Case)
Input: "Primary gyratory crusher 60-110; capacity 800 TPH; 450 kW motor; price USD 2.1M (2015)."
Emit:
- Equipment(properties: equipment_class="Equipment/Crusher/Gyratory",
           throughputRaw={{"value":800,"unit":"TPH"}}, powerKwRaw={{"value":450,"unit":"kW"}},
           capacity_value=800, capacity_unit="tons/hr")
- CostItem(price={{"amount":2100000,"currency":"USD","currencyYear":2015}})
- Equipment --HAS_COST--> CostItem

B) Capacity variations (Table)
Row: "125 (−50%) …", "250 (base) …", "500 (2×) …"
Emit for each row:
- capacity_value: 125 | 250 | 500
- capacity_adjustment: "−50%" | "base" | "2×"
- Keep original cell text; set confidence=1.0; attach table_id/row_index/col_index

--------------------------------------------------------------------------------
POLICY COMPLIANCE FOOTER (REQUIRED in meta.policyCompliance)
"meta": {{
  "policyCompliance": {{
    "appliedPatterns": ["EquipmentWithCost"],
    "synonymMappings": [{{"from":"machine","to":"Equipment"}}],
    "tableAliasMappings": [{{"from":"installed power","to":"powerKw"}}],
    "normalizations": [
      {{"field":"capacity","raw":{{"value":800,"unit":"TPH"}}, "norm":{{"capacity_value":800,"capacity_unit":"tons/hr"}}}}
    ],
    "defaultsUsed": [{{"field":"currency","value":"{defaults.get('currency','USD')}"}}],
    "dedupe": {{
      "rulesApplied": ["manufacturer+model","equipment_class+duty"],
      "mergedPairs": []
    }},
    "qualityGate": {{
      "declaredEdgeTypesOnly": {str(qg_edges_declared).lower()},
      "singletonNodesAllowed": {str(qg_singletons).lower()},
      "provenanceFieldsPresent": true,
      "templatesSatisfied": true
    }}
  }},
  "global_objectives": {{
    "kpis": [{{"name":"OPEX Intensity","unit":"USD/t","direction":"minimize","refs":["kpi_1"]}}],
    "constraints": [{{"name":"Power cap","expression":"powerKw <= 2500","refs":["constraint_7"]}}],
    "cost": [{{"name":"Primary crusher","price":{{"amount":2100000,"currency":"USD","currencyYear":2015}},"estimateClass":"AACE_Class_4","refs":["cost_12","edge_99"]}}],
    "risk": [{{"name":"Ore variability","risk_severity":"high","risk_probability":"likely","refs":["risk_3"]}}],
    "levers": [{{"name":"Vendor Selection","category":"Vendor","refs":["lever_1","alt_2","edge_40"]}}],
    "alternatives": [{{"name":"Vendor A","leverRef":"lever_1","assumptions":"FOB pricing","refs":["alt_2"]}}],
    "decision_variables": [{{"name":"Throughput","domain":"[500, 1500] tph","unit":"tph","defaultValue":800,"refs":["dv_1"]}}],
    "cost_drivers": [{{"name":"Power","driverType":"power","unit":"kW","refs":["driver_1","edge_55"]}}],
    "uncertainties": [{{"name":"Au grade","distribution":"lognormal(μ,σ)","low":0.6,"high":1.2,"refs":["unc_1"]}}],
    "assumptions": [{{"name":"Maintenance regime","short_description":"Preventive monthly","refs":["ass_2"]}}],
    "schedule": [{{"name":"Commissioning","time":{{"start":"2026-07-01T00:00:00Z"}},"refs":["ev_9"]}}],
    "permits": [{{"name":"Air Permit","issuingAuthority":"Region EPA","validFrom":"2024-01-10","refs":["permit_5"]}}],
    "data_gaps": [{{"name":"Missing vendor lead time","missingField":"leadTimeDays","context":"Vendor table lacks delivery info","refs":["tbl_4:r7c5"]}}]
  }}

}}

--------------------------------------------------------------------------------
EXPANSION HOOKS (RESERVED)
# schedules: emit Schedule/Milestone with TimeWindow; attach to Project/Facility
# reliability: FailureMode/WorkOrder/Sensor/Measurement flow
# sustainability: baseline CO2e and water intensity as KPI
# cost rollups: CostBreakdown attachment; validate against PATTERNS
================================================================================
Return nodes with extract_nodes(nodes=[...]), edges with extract_edges(edges=[...]), and meta with extract_meta(meta=[...]).

END
""".strip()
