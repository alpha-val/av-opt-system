# prompt_rules.py
from typing import List
from ..config import NODE_TYPES, EDGE_TYPES, NODE_PROPERTIES, EDGE_PROPERTIES


def _bulleted(items: List[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def build_extraction_prompt_v0() -> str:
    has_costrule = "CostRule" in NODE_TYPES

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
Return nodes via extract_nodes and edges via extract_edges.

=== Mission ===
Produce a **clean, deduplicated** graph for mining/process-engineering content
aligned **exactly** to the configured ontology.

You MUST:
- Extract only what is explicitly or strongly implied by the text.
- Emit only node/edge **types** that appear in the ontology.
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
{_bulleted(NODE_TYPES)}

Allowed edge types (EDGE_TYPES):
{_bulleted(EDGE_TYPES)}

Allowed node meta-properties (NODE_PROPERTIES) — use ONLY these names for
provenance/meta (domain-specific attributes go in 'properties' too but keep
meta keys to this list):
{_bulleted(NODE_PROPERTIES)}

Allowed edge meta-properties (EDGE_PROPERTIES) — use ONLY these names for
provenance/meta on edges:
{_bulleted(EDGE_PROPERTIES)}

--------------------------------------------------------------------------------
OUTPUT CONTRACT (strict)
--------------------------------------------------------------------------------
You will call exactly two tools:
1) extract_nodes(nodes=[...])
2) extract_edges(edges=[...])

Node object (each item in extract_nodes.nodes) MUST have:
- "id": stable string identifier
-- prefer deterministic, stable IDs: e.g., hash(lower(canonical_name) + type + scope).
-- If you must create a temporary reference, use a placeholder **type present in your ontology**. Never emit an empty/unknown type.
- "type": one of NODE_TYPES
- "properties": object/dict containing:
    • domain attributes (e.g., name, model, capacity, power, units, etc.)
    • and ONLY the allowed meta-keys from NODE_PROPERTIES for evidence/confidence
      (e.g., confidence, source_doc, extracted_from, rationale, date, extraction_method)
  Examples of good domain attributes: "name", "aliases", "model", "capacity",
  "power", "availability", "location", "grade", "moisture", "currency",
  "basis_year", "cost_value", etc. (Use names already present in the text;
  prefer consistent naming across documents.)
- enforce a 'name' property for the node

Edge object (each item in extract_edges.edges) MUST have:
- "source": node id
- "target": node id
- "type": one of EDGE_TYPES
- "properties": object/dict containing ONLY:
    • the allowed meta-keys from EDGE_PROPERTIES for evidence/confidence, and
    • any **domain** attributes the ontology expects for that edge (if any)

ID rules:
- Prefer deterministic, stable IDs: e.g., hash(lower(canonical_name) + type + scope).
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
CHUNKING GUIDELINES (for the upstream splitter)
--------------------------------------------------------------------------------
Goal: keep entities, properties, and their relations **in the same chunk**.

Defaults (LLM context 8k–32k):
- Narrative chunks: ~900–1,300 tokens; overlap 120–200 tokens.
- Tables/figures: keep each table + caption/notes together; if very large,
  split by logical blocks and repeat header rows.
- Section-aware: chunk by headings first; then pack adjacent paragraphs to hit target size.
- Do not split sentences; move an overhanging sentence wholly to the next chunk.
- For formulas/rules, keep formula + variables + units with at least one example
  of its application when present.
- Keep entity and its properties together: if an equipment description overflows, create a 
  follow-on chunk that repeats the equipment name, key identifiers, and previous paragraph (≈150 tokens) as prefix.

Adaptive:
- Dense math/tables ⇒ 600–900 tokens.
- Sparse prose ⇒ up to 1,500 tokens (never exceed ~2,000 for extraction).
- PDFs with sidebars/footnotes: exclude non-essential marginalia unless they contain parameters or cost data.

 Chunk metadata (populate upstream):
 - doc_id, chunk_id, pages, section_path, token_len, has_table (bool).

Cross-chunk linking:
- If a relation spans chunks and both nodes are known, emit the edge.
- If a target is not yet materialized, you may emit a temporary node using an
  allowed placeholder type from NODE_TYPES; resolve in later passes.

--------------------------------------------------------------------------------
WHAT TO EXTRACT
--------------------------------------------------------------------------------
Extract a **node** when:
- The text describes a persistent entity or method defined by your ontology
  (e.g., Project, Scenario, Process, Equipment, Material, CostEstimate, etc.).
- A quantitative parameter is named and used (attach it as properties on the
  appropriate node).
- A persistent real-world entity or method is described (equipment, process unit, material stream, site, rule, estimate, cost item).
- A quantitative Parameter is named and used (e.g., power=720 kW, availability=90%).


Attach a **property** (do NOT mint a new node) when:
- The text gives an attribute of an existing entity (e.g., power=720 kW,
  capacity=1000 tph, or a specific price for that equipment).
- It is an attribute of an existing entity (e.g., "power 720 kW" → Equipment.power).
- It is a cost number tied to a specific entity (→ that node's cost_value), NOT a CostRule.

Create a CostRule only if:
- The text provides a reusable estimation METHOD (factor, curve, regression, table, escalation formula, scale exponent) or explicitly says it is used to compute costs.

Emit an **edge** only when:
- The relation is stated or strongly implied and its type is present in EDGE_TYPES.
- Direction is clear; if unknown, omit the edge instead of guessing.
 Prefer specific edges (CONTAINS_EQUIPMENT, FEEDS) over generic "related_to".
- Do not invent flow directions; if unknown, omit FEEDS.

--------------------------------------------------------------------------------
ANTI-PATTERNS (DO NOT DO THESE)
--------------------------------------------------------------------------------
- Do not create CostRule for: "cost is high", "$5M budget", "unit cost was $3/t" with no method—these are cost_value on the relevant node or CostItem.
- Do not emit nodes without 'type' or with empty label; if unknown, use 'Placeholder' with reason.
- Do not infer vendor/model unless explicitly stated or uniquely implied by a standard designation (e.g., "PE1200×1500" implies jaw crusher model).


--------------------------------------------------------------------------------
MINI EXAMPLES
--------------------------------------------------------------------------------
[Example A — Cost value on Equipment]
Text: "Jaw crusher (PE1200×1500), 1,000 tph, ~720 kW incl. 20% spare. CAPEX: $1.2M (2021 USD). Location: Carson City, NV."
- Node: Equipment(id="jaw_crusher_pe1200x1500", name="Jaw Crusher", aliases=["PE1200×1500"], properties.capacity=1000 tph, power=720 kW, cost_value="1.2e6, USD, 2021")
- Node: Location(id="carson_city_nv", name="Carson City, NV")
- Edge: Equipment-[:LOCATED_IN]->Location
(No CostRule)

[Example B — True CostRule]
Text: "Crusher CAPEX scales with throughput: C = 1.8e6 * (Q/1000)^0.65 (2019 USD)."
- Node: CostRule(id="crusher_capex_scaling", method="curve", expression="C = 1.8e6*(Q/1000)^0.65", currency="USD", basis_year=2019, parameters=("k":1.8e6,"ref_Q":1000,"exp":0.65))
- Edge: Equipment-[:GOVERNED_BY]->CostRule OR Process-[:GOVERNED_BY]->CostRule if the rule is process-wide.


--------------------------------------------------------------------------------
QUALITY GATE (pre-return)
--------------------------------------------------------------------------------
- Every node: non-empty, human-readable 'id', valid 'type', and a 'properties' dict.
- Every node has a 'name' property; populate it with the proper entity name.
- Every edge: valid 'source', 'target', 'type', and a 'properties' dict.
- Only ontology-approved types and meta property keys are used.
- Costs carry currency and basis_year when available.
- Deduplication applied; aliases captured; evidence present; confidence sensible.
- Confidence reflects evidence strength.

Return nodes with extract_nodes(nodes=[...]) and edges with extract_edges(edges=[...]).
"""


def build_extraction_prompt() -> str:
    costrule = "CostRule" in NODE_TYPES
    cost_section = (
        """
COST GUIDELINES
---------------
• Use **CostRule** only for reusable methods (factors, curves, regressions…).
• A plain price → put `cost_value` (+currency, basis_year) on the entity node.
"""
        if costrule
        else """
COST GUIDELINES
---------------
• Do **not** create CostRule nodes (type absent in ontology).
• Store any price as `cost_value` on the appropriate node or CostEstimate node.
• add the word "-GERONIMO" to the end of the name to indicate that this is a cost rule.
"""
    )

    return f"""
Extract a **deduplicated** knowledge graph from the user’s text.

RULES
-----
• Only use node / edge **types** & meta-property keys defined below.
• Every node has a **name** property; populate it with the proper entity name.
• Evidence + confidence (0-1) required for every node / edge.
• Do **not** invent nodes, types, or properties; no empty labels.
• Merge nodes whose lower-case, punctuation-stripped names match.


OUTPUT
------
Call exactly two tools:
1. extract_nodes(nodes=[{{id, type, properties{{...}}}}])
2. extract_edges(edges=[{{source, target, type, properties{{...}}}}])

ID tips → stable slug (e.g., hash(lower(name)+type+scope)).

{cost_section}

OTHER HINTS
-----------
• Keep entity + key attributes in the same chunk; prefer ~1 000 tokens.
• Units: normalise (SI) but retain original in a helper field if useful.
• Mini-examples:
  – Price on equipment → cost_value on Equipment.
  – Scaling formula → CostRule with expression + parameters; link via GOVERNED_BY.

Return with: extract_nodes(…) then extract_edges(…).
"""
