# prompt_rules.py
from typing import List


def _bulleted(items: List[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def gen_prompt(ontology) -> str:
    has_costrule = "CostRule" in ontology["NODE_TYPES"]

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
{table_extraction_block}

--------------------------------------------------------------------------------
COST EXTRACTION POLICIES
--------------------------------------------------------------------------------
Cost & Method policy
{costrule_block}

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
{units_normalization_block}
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
