from typing import List, Dict, Any
from ..build_prompt import gen_prompt


def _bulleted(items: List[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def gen_prompt_with_tables(ontology: Dict[str, Any]) -> str:
    """Generate hybrid prompt that handles both text and table data."""

    base_prompt = gen_prompt(ontology)  # Your existing prompt

    table_section = """
================================================================================
PART B: TABLE DATA INTEGRATION
================================================================================

You will receive TWO types of input:
1. **Narrative text** - Extract entities/relationships using Part A rules
2. **Structured tables** - Already parsed into rows/columns

--------------------------------------------------------------------------------
TABLE HANDLING STRATEGY
--------------------------------------------------------------------------------

For pre-parsed table data (marked with [TABLE] tags):

1. **Recognize the table type** from context or headers:
   - equipment_cost: Equipment purchase/installed costs
   - equipment_sizing: Technical specifications and capacities
   - lang_factor: Installation cost multipliers
   - escalation_index: Cost escalation indices (CEPCI, CPI, etc.)
   - performance_data: Operating/performance metrics
   - wbs_breakdown: Work breakdown structure costs

2. **Create entities directly from rows**:
   - Each row = one entity node
   - Columns map to properties (use ontology NODE_PROPERTIES)
   - Confidence = 1.0 (explicit tabular data)
   - Preserve all numeric precision
   - Include table_id in source metadata

3. **Table-specific entity mapping**:

   **equipment_cost table** → Equipment nodes:
   ```
   Columns: Manufacturer | Model | Type | Capacity | Power | Cost | Year
   →
   Entity: {
     type: "Equipment",
     manufacturer: "Metso",
     model: "CH880",
     equipment_type: "cone_crusher",
     capacity_tph: 900,
     power_kw: 500,
     purchase_cost: 1850000,
     currency: "USD",
     cost_year: 2021,
     confidence: 1.0,
     source: "table:<table_id>:row:<row_idx>"
   }
   ```

   **lang_factor table** → LangFactor nodes:
   ```
   Columns: Equipment Type | Lang Factor | Equipment % | Civil % | ...
   →
   Entity: {
     type: "LangFactor",
     equipment_category: "crushing",
     equipment_type: "gyratory_crusher",
     lang_factor: 3.5,
     equipment_pct: 28.57,
     civil_pct: 30.0,
     structural_pct: 15.0,
     mechanical_pct: 12.86,
     electrical_pct: 6.43,
     confidence: 1.0,
     source: "table:<table_id>:row:<row_idx>"
   }
   ```

   **escalation_index table** → EscalationIndex nodes:
   ```
   Columns: Year | Index Value | Change %
   →
   Entity: {
     type: "EscalationIndex",
     index_name: "CEPCI",  # from table name/description
     year: 2023,
     index_value: 801.3,
     change_pct: -1.8,
     confidence: 1.0,
     source: "table:<table_id>:row:<row_idx>"
   }
   ```

   **equipment_sizing table** → Equipment nodes with specs:
   ```
   Columns: Model | Feed Opening | CSS Range | Capacity Min | Capacity Max | Power
   →
   Entity: {
     type: "Equipment",
     model: "Superior MKII 60-89",
     feed_opening_in: 60.0,
     css_range_min_in: 6.0,
     css_range_max_in: 10.0,
     capacity_min_tph: 4000,
     capacity_max_tph: 6000,
     power_kw: 1120,
     confidence: 1.0,
     source: "table:<table_id>:row:<row_idx>"
   }
   ```

4. **Column name normalization**:
   - "Capacity (tph)" → capacity_tph
   - "Cost (USD)" → purchase_cost, currency="USD"
   - "Power (kW)" → power_kw
   - "Diameter (m)" → diameter_m
   - "CSS (in)" → css_in
   - "Work Index" → work_index
   - Strip units, convert to snake_case property names

5. **Create Table metadata nodes**:
   ```
   {
     type: "Table",
     name: "<descriptive_name>",
     table_type: "<type>",
     table_id: "<table_id>",
     row_count: <count>,
     column_count: <count>,
     confidence: 1.0,
     source: "document:<doc_id>:page:<page>"
   }
   ```

6. **Link entities to tables**:
   - Create :SOURCED_FROM edge from entity to Table node
   - Preserve row index in edge properties: {row_idx: <n>}

7. **Handle numeric values**:
   - Remove commas: "1,234,567" → 1234567
   - Parse units: "5.5 in" → value=5.5, unit="in"
   - Handle ranges: "4000-6000 tph" → capacity_min_tph=4000, capacity_max_tph=6000
   - Currency codes: "$1.85M" → 1850000, currency="USD"

8. **Quality rules for table data**:
   - Always confidence=1.0 (explicit data)
   - Never hallucinate values not in the cell
   - Preserve all significant digits
   - Flag NULL/empty cells explicitly
   - Include row_idx for traceability

--------------------------------------------------------------------------------
HYBRID EXTRACTION WORKFLOW
--------------------------------------------------------------------------------

When you receive input:

1. **Scan for [TABLE] markers**:
   - If found: Process using table rules above
   - Table data will be formatted as:
     ```
     [TABLE table_id="<id>" table_type="<type>" page="<n>"]
     | Header1 | Header2 | Header3 |
     | Value1  | Value2  | Value3  |
     [/TABLE]
     ```

2. **Process remaining text**:
   - Apply Part A rules (your existing entity/relation extraction)
   - Use confidence scoring for inferred data

3. **Cross-reference**:
   - If text mentions equipment also in a table, create :SAME_AS edge
   - Link text-extracted costs to table-extracted equipment
   - Example: "The Metso CH880 crusher costs $1.85M" + table row → link them

4. **Merge strategy**:
   - Table data wins for explicit properties (capacity, cost, specs)
   - Text data adds context (location, purpose, relationships)
   - Create composite nodes with both sources

--------------------------------------------------------------------------------
OUTPUT FORMAT FOR HYBRID DATA
--------------------------------------------------------------------------------

Return JSON with two sections:

```json
{
  "text_entities": [
    // Entities extracted from narrative text (Part A rules)
  ],
  "text_relationships": [
    // Relationships from text (Part A rules)
  ],
  "table_entities": [
    // Entities from table rows (Part B rules)
  ],
  "table_metadata": [
    // Table descriptor nodes
  ],
  "cross_references": [
    // Links between text and table entities
    {
      "text_entity_id": "<id>",
      "table_entity_id": "<id>",
      "relationship_type": "SAME_AS",
      "confidence": 0.95
    }
  ]
}
```

================================================================================
"""

    # Add table-specific node types if not already in ontology
    table_node_types = [
        "Table",
        "LangFactor",
        "EscalationIndex",
        "Performance",
        "WBSItem",
        "CostEstimate",
    ]

    table_edge_types = [
        "SOURCED_FROM",
        "REFERENCES",
        "COSTED_BY",
        "SIZED_FROM",
        "ESCALATED_BY",
    ]

    ontology_addendum = f"""

--------------------------------------------------------------------------------
EXTENDED ONTOLOGY FOR TABLE DATA
--------------------------------------------------------------------------------

Additional NODE_TYPES for table entities:
{_bulleted(table_node_types)}

Additional EDGE_TYPES for table relationships:
{_bulleted(table_edge_types)}

Additional NODE_PROPERTIES for mining/process engineering:
- capacity_tph, capacity_tpd, throughput_tph
- power_kw, power_mw
- diameter_m, length_m, feed_opening_in, css_in
- purchase_cost, installed_cost, total_installed_cost
- lang_factor, equipment_pct, civil_pct, structural_pct
- escalation_year, escalation_multiplier, index_value
- work_index, specific_energy_kwh_per_tonne
- availability_pct, utilization_pct
- wbs_code, cost_percentage
- table_id, row_idx, table_type
"""

    return base_prompt + table_section + ontology_addendum
