from ..ontology import AV_MSIO_ONTOLOGY, load_ontology

ont = load_ontology()

# Extract ontology components
node_types = ont.get("NODE_TYPES", [])
edge_types = ont.get("EDGE_TYPES", [])

# Construct the prompt in parts
scenario_extraction_prompt_v0 = """
--------------------------------------------------------------------------------
SCENARIO EXTRACTION PROMPT — BASE CASE → SCENARIO VARIANTS
--------------------------------------------------------------------------------
Goal
Given:
1) A base case technical report or cost summary (as input text/tables)
2) A user-defined scenario request containing:
   * target: List[str]  — overall goal(s), e.g. ["Increase production"]
   * change_type: List[str]  — affected domain(s), e.g. ["Equipment", "Material"]
   * description: str  — freeform description, e.g. "Increase production by 8%"

Task
Extract all relevant design, cost, and operational aspects of the requested
scenario, grounded strictly in the base case context. Identify specific entities,
parameters, assumptions, constraints, and cost estimation guidelines that would
be modified or impacted by the scenario.

Strictly map extracted information to the provided ontology terms (e.g., NODE_TYPES,
NODE_PROPERTIES, RELATION_TYPES). Focus on quantitative and technical details
that would inform cost modeling and design adjustments under the scenario.
""".strip()

# Append ontology terms
scenario_extraction_prompt_v0 += f"\n{node_types}\n{edge_types}\n{AV_MSIO_ONTOLOGY}"

scenario_extraction_prompt_v0 += """
--------------------------------------------------------------------------------
WHAT TO EXTRACT (STRUCTURED OUTPUT REQUIRED)
--------------------------------------------------------------------------------
Return the output as a JSON object with the following structure:

{
  "scenario_summary": {
    "target": "<from user input>",
    "change_type": [ ... ],
    "description": "<from user input>",
    "related_sections": [ "Section 2 – Major Equipment", "Section 3 – Design Criteria", ... ],
    "derived_entities": [
      {
        "entity_name": "...",
        "entity_type": "Equipment | Material | Process | Control | Utility | Other",
        "base_values": { "parameter": "...", "value": "...", "units": "..." },
        "potential_modifications": [ "Upsize pump", "Add secondary tank", ... ],
        "expected_impact": {
          "direction": "increase | decrease | neutral",
          "magnitude_estimate": "...%",
          "cost_driver": "capex | opex | throughput | reliability"
        },
        "refs": [ "<source page or node id>" ]
      }
    ]
  },

  "assumptions": [
    { "text": "...", "type": "Design | Market | Environmental | Operational", "refs": [...] }
  ],

  "policies": [
    { "text": "...", "domain": "Safety | Code | Cost | Procurement | Quality", "refs": [...] }
  ],

  "constraints": [
    { "constraint": "...", "basis": "Physical | Regulatory | Budgetary | Schedule", "refs": [...] }
  ],

  "cost_estimation_guidelines": [
    {
      "item": "Pump",
      "base_cost": 8500,
      "cost_basis": "Vendor price, 10-hp pump, 2025 USD",
      "scaling_rule": "Cost ∝ (capacity)^0.6",
      "risk_factor": "Market volatility, stainless-steel pricing",
      "recommendation": "Use vendor quote or scale using cost exponent"
    }
  ],

  "uncertainties_or_gaps": [
    { "gap": "...", "suggested_action": "Obtain vendor quotes / validate hydraulics", "priority": "High" }
  ]
}

--------------------------------------------------------------------------------
INSTRUCTIONS
--------------------------------------------------------------------------------
* Use quantitative values directly from the report where possible.
* Keep entity names and relationships consistent with ontology terms (e.g., NODE_TYPES).
* Identify implicit dependencies (e.g., increasing flow → larger tank → higher motor hp).
* Extract numerical assumptions, constraints, and codes/standards that would govern
  modifications under the scenario.
* Capture relevant cost relationships, escalation factors, and sensitivity notes.
* Exclude generic narrative text not tied to technical or cost implications.
* Maintain concise phrasing for all text fields (max 2–3 sentences each).

--------------------------------------------------------------------------------
EXAMPLE INPUT
--------------------------------------------------------------------------------
target = ["Increase production"]
change_type = ["Equipment", "Quantity"]
description = "Increase production by 6.5%"

--------------------------------------------------------------------------------
EXAMPLE OUTPUT (ABBREVIATED)
--------------------------------------------------------------------------------
{
  "scenario_summary": {
    "target": "Increase production",
    "change_type": ["Equipment", "Quantity"],
    "description": "Increase production by 6.5%",
    "derived_entities": [
      {
        "entity_name": "Pump + Motor",
        "entity_type": "Equipment",
        "base_values": {"flow": "100 gpm", "motor_power": "10 hp"},
        "potential_modifications": ["Upsize pump to 12 hp", "Add parallel pump"],
        "expected_impact": {"direction": "increase", "magnitude_estimate": "≈10%", "cost_driver": "Capex"},
        "refs": ["§2 Major Equipment", "§7 Design Notes"]
      },
      {
        "entity_name": "Storage Tank",
        "entity_type": "Equipment",
        "base_values": {"capacity": "1,000 gal @ 80%"},
        "potential_modifications": ["Increase volume to 1,200 gal gross", "Add secondary tank"],
        "expected_impact": {"direction": "increase", "magnitude_estimate": "≈5–10%", "cost_driver": "Capex"},
        "refs": ["§2 Major Equipment"]
      }
    ]
  },
  "assumptions": [
    {"text": "Steady 100 gpm flow maintained; pump scaled linearly for flow increase", "type": "Design"}
  ],
  "policies": [
    {"text": "Tank and piping shall remain stainless steel per ASME B31.3", "domain": "Quality"}
  ],
  "constraints": [
    {"constraint": "No pressurization; tank remains atmospheric", "basis": "Safety"}
  ],
  "cost_estimation_guidelines": [
    {"item": "Tank", "base_cost": 15000, "scaling_rule": "Cost ∝ capacity^0.65", "recommendation": "Vendor quote ±20%"}
  ],
  "uncertainties_or_gaps": [
    {"gap": "Hydraulic TDH not specified for higher flow", "suggested_action": "Perform hydraulic calc", "priority": "High"}
  ]
}
"""


scenario_extraction_prompt_v1 = """
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
Use the following ontology terms to classify and standardize all extracted
entities, parameters, relationships, and cost roles.
{node_types}
{edge_types}
{AV_MSIO_ONTOLOGY}

--------------------------------------------------------------------------------
QUALITY & STYLE
--------------------------------------------------------------------------------
- Be concise, specific, and quantitative.
- Keep terms consistent with ontology (if provided).
- Use SI/US units exactly as in the base case; include units on all numeric values.
- Use explicit references to section headers, tables, or page anchors (e.g., "§2 Major Equipment").
- Ensure both scenario types (Production Change, Capex Change) are populated when relevant data exists.

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
        "related_sections": ["§2 Major Equipment", "§3 Design Criteria"]
      },

      "template_parameters": {
        "change_direction": "increase | decrease",
        "change_magnitude": "<percent or unit value, e.g., 5%, 2 gpm>",
        "baseline_metric": "<production rate, flow, capacity, cost, etc.>",
        "baseline_value": "<numeric + units>",
        "target_metric": "<same as baseline_metric>",
        "target_value": "<numeric + units>",
        "measurement_basis": "<steady-state | design | rated>"
      },

      "approach_options": [
        {
          "option_id": "<slug>",
          "title": "<short label>",
          "rationale": "<why this option helps achieve the goal>",
          "expected_effects": {
            "throughput": {"direction": "increase|decrease|neutral", "estimate_pct": "<string|null>"},
            "capex":      {"direction": "increase|decrease|neutral", "notes": "<string>"},
            "opex":       {"direction": "increase|decrease|neutral", "notes": "<string>"},
            "quality":    {"direction": "increase|decrease|neutral", "notes": "<string>"}
          },
          "dependencies": ["<e.g., TDH validation, electrical capacity>"],
          "refs": ["<anchors>"]
        }
      ],

      "relevant_entities": [
        {
          "entity_name": "<Pump, Tank, System>",
          "entity_type": "Equipment | Process | Material | Control | Civil | Electrical | Other",
          "base_values": [{"key": "flow_rate", "value": "100", "units": "gpm"}],
          "proposed_modifications": [
            {"parameter": "flow_rate", "change": "increase", "suggested_value": "108", "units": "gpm"}
          ],
          "expected_impacts": {
            "capex": {"direction": "increase", "magnitude_note": "+5%"},
            "opex": {"direction": "increase", "magnitude_note": "+2%"}
          },
          "cost_role": "CostItem | CostRule | None",
          "refs": ["§2 Major Equipment"]
        }
      ],

      "assumptions": [
        {"text": "<design or operational assumption>", "type": "Design | Operational | Market | Environmental"}
      ],

      "policies": [
        {"text": "<policy or code>", "domain": "Safety | Code | Cost | Procurement | Quality | Environmental"}
      ],

      "constraints": [
        {"constraint": "<limitation>", "basis": "Physical | Regulatory | Budgetary | Schedule | Availability"}
      ],

      "cost_guidelines": [
        {
          "item": "<e.g., Tank, Pump, Electrical>",
          "base_cost_value": 8500,
          "currency": "USD",
          "basis_year": 2025,
          "scaling_rule": "C2 = C1 * (S2/S1)^0.6",
          "risk_notes": "Vendor price variability, material volatility",
          "estimation_note": "Use vendor quote if deviation > ±20%"
        }
      ],

      "uncertainties": [
        {"gap": "<missing or estimated data>", "impact": "Low | Med | High", "action": "obtain vendor quote | recalc hydraulics"}
      ]
    }
  ]
}

--------------------------------------------------------------------------------
STRICTNESS
--------------------------------------------------------------------------------
- Output MUST be valid JSON with a top-level key `"scenarios"`.
- Always generate both templates (Production Change, Capex Change) if applicable.
- Each scenario must be independently analyzable and reusable.
- Avoid narrative or commentary outside the JSON.
- Exhaustively find and map ALL POSSIBLE relevant data in the base case text.
  - For example, if multiple production change options exist, include them all. E.g.,
    `Pump and motor efficiencies can be improved with minimal cost.` → include as separate entities.
--------------------------------------------------------------------------------

""".strip()


scenario_extraction_prompt_v2 = """
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
Use the following ontology terms to classify and standardize all extracted
entities, parameters, relationships, and cost roles.
{node_types}
{edge_types}
{AV_MSIO_ONTOLOGY}

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
