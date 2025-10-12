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
* Reserve the 'CostRule' node type **only** for reusable cost-estimation methods.
  Examples: factors, parametric curves, scale exponents, lookup tables,
  regressions, escalation/deflation formulas, or vendor price lists used as a
  *method* (not just a one-off price).
* Do **NOT** create a 'CostRule' node just because a dollar amount appears.
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
* Do **NOT** create any 'CostRule' nodes.
* When costs/prices appear in text, attach them directly as properties on the
  relevant node (e.g., Equipment/Process) **or** use dedicated costing nodes
  defined in your ontology (e.g., 'CostEstimate') and edges from EDGE_TYPES
  (e.g., :COSTED_BY / :AGGREGATES, if present).
"""
    )

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
1. **Identify table boundaries**: Start/end rows, column spans
2. **Parse headers**: 
   - Top row(s) define property names
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
* Recognize data types:
  - Numeric: parse numbers, preserve precision
  - Monetary: extract amount + currency
  - Boolean: Yes/No, ✓/✗, True/False
  - Categorical: map to ontology enums if applicable

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
  - Use "Name" or "Model" column if present
  - Synthesize from key attributes: "{Type} {Dimension}"
  - Ensure uniqueness within table scope

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
✗ Never merge distinct rows into one entity
✗ Never split one row into multiple entities (unless clearly composite)
✗ No hallucinated values for empty cells
✗ No assumptions about missing units
"""

    return f"""
Extract a knowledge graph from the user's text.

=== Mission ===
Produce a **clean, deduplicated** knowledge graph for mining/process-engineering content
aligned **exactly** to the configured ontology.

You MUST:
- Extract only what is explicitly or strongly implied by the text.
- Do not infer or assume information not present.
- Emit only node/edge **types** that appear in the ontology.
- Each nodes **must** have a type or property["label"] that maps to NODE_TYPES.
- Use only node/edge **property names** that appear in the ontology metadata lists.
- Attach evidence and a confidence score to every node and edge **using the
  allowed property names** from NODE_PROPERTIES / EDGE_PROPERTIES.
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
OUTPUT CONTRACT (strict)
--------------------------------------------------------------------------------
Node object (each item in extract_nodes.nodes) MUST have:
- "id": stable unique string identifier (uuid)
-- prefer deterministic, stable unique IDs, e.g., using uuid
-- If you must create a temporary reference, use a placeholder **type present in your ontology**. Never emit an empty/unknown type.
- "type": one of NODE_TYPES; a Node object **must** have a type
- "properties": object/dict containing:
    • follow the properties mentioned in NODE_PROPERTIES in the ontology
    • prioritize finding cost associated with an entity (e.g., 'cost', 'price', 'cost_value', 'currency', 'basis_year', 'expenditure')
- enforce a 'name' property for the node

Edge object (each item in extract_edges.edges) MUST have:
- "source": node id
- "target": node id
- "type": one of EDGE_TYPES
- "properties": object/dict containing ONLY:
    • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
    • any **domain** attributes the ontology expects for that edge (if any)

ID rules:
- Prefer deterministic, stable unique IDs, e.g., using uuid.
- If you must create a temporary reference, use a placeholder **type present in your ontology**.
  Never emit an empty/unknown type.

{costrule_block}

{table_extraction_block}

--------------------------------------------------------------------------------
NORMALIZATION & DEDUP
--------------------------------------------------------------------------------
- Canonicalize names for comparison: lowercase; strip punctuation/underscores/dashes/spaces.
- Merge if (same type) AND (canonical names match). Otherwise keep separate but
  you may create a low-confidence equivalence edge (if your ontology defines one).
- Maintain 'aliases' inside the node 'properties' if variants appear in text.

Units & values:
- Normalize units (prefer SI where sensible) but preserve the original in an
  auxiliary field (e.g., 'display_value' or 'orig_unit') if helpful.
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
QUALITY GATE (pre-return)
--------------------------------------------------------------------------------
- Every node: non-empty, unique 'id' (uuid), valid 'type', and a 'properties' dict.
- Every node has a 'name' property; populate it with the proper entity name.
- Every node has a 'type' property that matches NODE_TYPES.
- Every node property key matches NODE_PROPERTIES.
- For nodes of type 'Equipment', 'Process', 'Material', 'Product', 'Waste', etc., acquire cost details if they appear in text.
- For nodes of type 'CostRule', ensure compliance with COST & METHOD POLICY above.
- For nodes of type 'CostEstimate' or similar, ensure costing details are present.
- For node properties that are costs/prices, include currency and basis_year when available.
- Every edge: valid 'source', 'target', 'type', and a 'properties' dict.
- Every edge property key matches EDGE_PROPERTIES.
- All nodes must be linked with type that matches EDGE_TYPES.
- Only ontology-approved types and meta property keys are used.
- Deduplication applied; aliases captured; evidence present; confidence sensible.
- Do not hallucinate entities, relationships, or properties.
- Maintain a clear audit trail for all extracted data.
- Confidence reflects evidence strength.

Return nodes with extract_nodes(nodes=[...]) and edges with extract_edges(edges=[...]).
"""
