"""
Rules for interpreting structured table data and converting to knowledge graph entities.
"""

TABULAR_RULES = """
================================================================================
TABULAR DATA EXTRACTION RULES
================================================================================

Process structured table data row-by-row to create complete entity nodes.

PRINCIPLES:
-----------
1. Each row is ONE complete entity with ALL its attributes
2. Empty cells are NULL, not zero
3. Units from headers apply to all values in that column
4. Preserve both imperial and metric when present
5. Never invent values not in the source row

ROW-TO-ENTITY MAPPING:
---------------------
Input row format:
{
  "row_id": "unique_identifier",
  "row_index": 0,
  "cells": {
    "Type": "Single Stage",
    "Capacity_stph": "4",
    "Capacity_mtph": "3.6",
    "Roll_diameter_in": "12",
    "Capital_Cost_USD": "58000"
  }
}

Output entity format:
{
  "id": "deterministic-uuid",
  "type": "Equipment",
  "properties": {
    "name": "Single Stage Roll Crusher",
    "equipment_type": "roll_crusher",
    "stage_configuration": "single_stage",
    "capacity_stph": 4.0,
    "capacity_mtph": 3.6,
    "roll_diameter_in": 12.0,
    "capital_cost": 58000.0,
    "currency": "USD",
    "row_index": 0,
    "source_table_id": "...",
    "confidence": 1.0
  }
}

COLUMN NORMALIZATION:
--------------------
Remove units from column names, add as separate unit property:
- "Capacity (stph)" → capacity_stph: 4.0
- "Weight (lbs)" → weight_lbs: 3600.0
- "Cost USD" → capital_cost: 58000.0, currency: "USD"

Convert to snake_case:
- "Roll Diameter" → roll_diameter
- "Feed Width" → feed_width
- "Capital Cost" → capital_cost

DUAL UNITS:
-----------
When both systems present, store both:
{
  "weight_lbs": 3600,
  "weight_kg": 1633,
  "diameter_in": 12,
  "diameter_cm": 30.5
}

VALUE PARSING:
--------------
- Numbers: remove commas → "1,234" becomes 1234
- Currency: "$58K" → 58000, currency: "USD"
- Percentages: "95%" → 95.0, unit: "percent"
- Ranges: "10-20" → min: 10, max: 20
- Boolean: "Yes"/"No" → true/false

TYPE INFERENCE:
---------------
Determine entity type from column patterns:
- Has "Model", "Manufacturer", "Capacity" → Equipment
- Has "Grade", "Composition", "Purity" → Material  
- Has "Stage", "Throughput", "Yield" → Process
- Default for equipment tables → Equipment

ENTITY NAMING:
--------------
Build descriptive name from key columns:
- Use "Type" or "Model" column if present
- Add distinguishing features: "Single Stage Roll Crusher"
- If no name column, use: "{type} {key_dimension}"

REQUIRED PROPERTIES:
-------------------
Every entity must have:
- id: deterministic UUID
- type: valid NODE_TYPE from ontology
- properties.name: human-readable identifier
- properties.row_index: source row number
- properties.source_table_id: table identifier
- properties.confidence: 1.0 (explicit data)

LINEAGE:
--------
Create these edges for traceability:
1. Entity --DERIVES_FROM--> TableRow
   properties: {row_index: N, extraction_method: "tabular"}

2. TableRow --PART_OF--> Table
   properties: {row_index: N}

EXAMPLE COMPLETE EXTRACTION:
----------------------------
For roll crusher row:
{
  "id": "uuid-12345",
  "type": "Equipment",
  "properties": {
    "name": "Single Stage Roll Crusher 12in",
    "equipment_type": "roll_crusher",
    "stage_configuration": "single_stage",
    "capacity_stph": 4.0,
    "capacity_mtph": 3.6,
    "capacity_unit": "tph",
    "roll_diameter_in": 12.0,
    "roll_diameter_cm": 30.5,
    "feed_width_in": 12.0,
    "feed_width_cm": 30.5,
    "weight_lbs": 3600.0,
    "weight_kg": 1633.0,
    "horsepower": 5.0,
    "power_unit": "HP",
    "capital_cost": 58000.0,
    "currency": "USD",
    "cost_type": "capital",
    "row_index": 0,
    "source_table_id": "tbl::doc123::p1::0",
    "confidence": 1.0,
    "extraction_method": "tabular_direct"
  }
}

QUALITY CHECKS:
---------------
✓ All non-empty columns included
✓ Units preserved or normalized
✓ Name is descriptive
✓ Type matches ontology
✓ Numeric values are numbers, not strings
✓ Row lineage preserved
✗ No invented values
✗ No zero for empty cells
✗ No merged rows
"""
