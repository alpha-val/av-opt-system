# prompt_rules.py
from typing import List
from ..utils.logging import get_logger

log = get_logger(__name__)

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

    return f"""
Extract a knowledge graph from the user's text.

=== Mission ===
Produce a **clean, deduplicated** knowledge graph for mining/process-engineering content
aligned **exactly** to the configured ontology.

You MUST:
- Extract only what is explicitly or strongly implied by the text.
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
- Keep excerpts short (≤200 chars). Populate the appropriate meta fields strictly
  from NODE_PROPERTIES / EDGE_PROPERTIES (e.g., 'source_doc', 'extracted_from', etc.).


--------------------------------------------------------------------------------
QUALITY GATE (pre-return)
--------------------------------------------------------------------------------
- Every node: non-empty, unique 'id' (uuid), valid 'type', and a 'properties' dict.
- Every node has a 'name' property; populate it with the proper entity name.
- Every node has a 'type' property that matches NODE_TYPES.
- Every edge: valid 'source', 'target', 'type', and a 'properties' dict.
- All nodes must be linked with type that matches EDGE_TYPES.
- Only ontology-approved types and meta property keys are used.
- Costs carry currency and basis_year when available.
- Deduplication applied; aliases captured; evidence present; confidence sensible.
- Confidence reflects evidence strength.

Return nodes with extract_nodes(nodes=[...]) and edges with extract_edges(edges=[...]).
"""
