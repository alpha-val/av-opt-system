import json
from typing import Any, Dict, Optional

from ...ontology.ontology import AV_MSIO_ONTOLOGY, ENTITY_ONTOLOGY, get_default_ontology
from ...ontology.ontology import ENTITY_ONTOLOGY

# Convert the ontology to JSON with all white spaces and new-line characters removed
NODE_TYPES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_types", []), indent=1).replace("\n", "")
NODE_PROPERTIES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_properties", []), indent=1).replace("\n", "")

# Load MSIO ontology
MSIO_ONTOLOGY_TEXT = json.dumps(AV_MSIO_ONTOLOGY, indent=1).replace("\n", "")

ONTOLOGY_REFERENCE_BLOCK = f"""
    MSIO_ONTOLOGY:
    {MSIO_ONTOLOGY_TEXT}

    NODE_TYPES (ENTITY_ONTOLOGY.node_types):
    {NODE_TYPES_JSON}

    NODE_PROPERTIES (ENTITY_ONTOLOGY.node_properties):
    {NODE_PROPERTIES_JSON}
    """.strip()


# Modular prompt sections
OBJECTIVE_PARSING_SECTION = """
-------------------------------------------------------------------------------
OBJECTIVE PARSING
-------------------------------------------------------------------------------
Extract from SCENARIO_REQUEST into "objective" block:

objective: {
  "objective_text": string, // REQUIRED
  "objective_type": string, // REQUIRED: one of ["increase_capacity", "increase_production", "reduce_capex", "reduce_opex", "reduce_total_cost", "change_availability", "change_reliability", "change_instrumentation_scope", "change_containment_type", "other"],
  "target_metric_name": string|null,
  "target_direction": string|null, // "increase" or "decrease"
  "target_delta_type": string|null, // "relative_percent" or "absolute"
  "target_delta_value": number|null,
  "target_unit": string|null,
  "time_basis_or_scope": string|null,
  "secondary_objectives": [string] // array of strings if multiple objectives
}

Interpret only; do not optimize.
"""

COMPONENT_IDENTIFICATION_SECTION = """
-------------------------------------------------------------------------------
COMPONENT IDENTIFICATION & DECISION LEVERS
-------------------------------------------------------------------------------
CRITICAL: Identify ALL components that could be changed to achieve the objective. For each component, extract ALL attributes as separate decision levers. Rank components by relevance_score (1.0 = critical, 0.5 = moderate, 0.0 = minimal).

**SYSTEMATIC COMPONENT EXPLORATION PROCESS**:
Follow this systematic approach to ensure comprehensive component identification:

STEP 1: Scan the base_case text for ALL physical and system components mentioned, even if they seem peripheral.

STEP 2: For EACH component found, ask: "Could changing this component or its attributes help achieve the objective?" If YES, include it.

STEP 3: Check these component categories systematically (include ALL that are present):
- PRIMARY EQUIPMENT: Storage tanks, vessels, pumps, heat exchangers, reactors, etc.
- FOUNDATIONS & STRUCTURAL: Concrete pads, piles, ring walls, support platforms, structural steel
- CONTAINMENT SYSTEMS: Containment basins, berms, liners, secondary containment
- STORMWATER MANAGEMENT: Drainage systems, stormwater basins, grading
- INSTRUMENTATION & CONTROLS: Level transmitters, pressure sensors, temperature sensors, PLCs, HMIs, alarms
- ELECTRICAL SYSTEMS: Transformers, panels, motor control centers, power distribution, lighting
- CIVIL & SITEWORK: Excavation, backfill, site grading, access roads, utilities
- SAFETY & ACCESS: Guardrails, platforms, stairs, ladders, manways, safety equipment
- MATERIALS: Material of construction for each component (tank shell, containment, structural, etc.)

STEP 4: For each component, extract ALL attributes as separate decision levers. Do NOT skip attributes because they seem "obvious" or "less important". Every attribute is a potential lever.

**CRITICAL: Attribute Extraction Checklist** - For EACH component, systematically extract ALL of these attribute types as separate decision levers:

GEOMETRY & DIMENSIONS (MANDATORY - extract ALL present):
- For cylindrical tanks/vessels: diameter, height, wall_thickness, head_type, head_thickness
- For rectangular components: width, length, height, thickness
- For platforms/structures: platform_area, platform_elevation, deck_thickness, beam_depth, column_size
- For foundations: pad_width, pad_length, pad_thickness, pile_diameter, pile_length, pile_count
- For containment: basin_length, basin_width, basin_depth, berm_height, liner_thickness
- Aspect ratios: height_to_diameter_ratio, length_to_width_ratio (if specified)
- Orientation: vertical, horizontal, angle (if specified)

CAPACITY & PERFORMANCE:
- Capacity (storage volume, flow rate, throughput)
- Number of units/trains
- Design pressure, operating pressure
- Design temperature, operating temperature
- Flow rates (inlet, outlet, recirculation)

MATERIALS & CONSTRUCTION:
- Material_of_construction (shell, heads, liners, structural)
- Coating/linings (epoxy, HDPE, etc.)
- Insulation type and thickness
- Weld specifications, joint types

CONFIGURATION & LAYOUT:
- Number of units/trains
- Arrangement/orientation
- Elevation/height above grade
- Location/positioning
- Connection types (flanged, welded, threaded)

COMPONENT-SPECIFIC ATTRIBUTES:
- Tanks: manway_size, manway_count, drain_size, vent_size, nozzle_sizes, support_type
- Foundations: bearing_capacity, soil_type, excavation_depth, backfill_type
- Platforms: deck_material, guardrail_height, stair_count, ladder_type
- Containment: containment_volume, freeboard, liner_type, drainage_system
- Instrumentation: sensor_type, transmitter_range, alarm_setpoints, communication_protocol
- Electrical: voltage, phase, kVA_rating, panel_type, circuit_count

STEP 5: Assign relevance_score based on directness of impact, but include ALL components regardless of score.

**EXPECTED COMPONENT COUNT**: For a typical industrial system, expect 8-15+ components. If you identify fewer than 5 components, you are likely missing components. Re-examine the base_case text more carefully.

**Component Schema**:
{
  "component_id": string, // REQUIRED: unique identifier (e.g., "tank_001", "foundation_001")
  "role": string, // REQUIRED: standard industry terminology
  "key_attributes": [  // REQUIRED: min 2 items for vector search - MUST include geometric dimensions
    {
      "name": string, // REQUIRED - prioritize: capacity, diameter, height, width, length, material_of_construction
      "value": string|number|null,
      "unit": string|null
    }
  ],
  // Example: For a cylindrical tank, key_attributes should include: capacity, diameter, height, material_of_construction (at minimum)
  "quantity": number|null, // numeric count
  "relevance_to_objective": string, // REQUIRED: How this component relates to achieving the objective
  "relevance_score": number, // REQUIRED: 0.0-1.0 (1.0 = critical, 0.5 = moderate, 0.0 = minimal) - REQUIRED for ranking
  "decision_levers": [  // REQUIRED: min 1 item - ALL editable attributes as separate decision levers
    {
      "lever_id": string, // REQUIRED: unique identifier (e.g., "tank_001_capacity", "tank_001_diameter")
      "attribute_name": string, // REQUIRED: attribute name (e.g., "capacity", "diameter", "height", "material_of_construction")
      "category": string, // REQUIRED: enum ["capacity", "geometry", "material", "instrumentation", "electrical", "containment", "stormwater", "civil", "schedule", "cost_model"]
      "baseline_value": string|number|null, // Current baseline value for this attribute
      "baseline_unit": string|null, // Unit of measure
      "baseline_text": string|null, // Evidence snippet from source
      "description": string|null, // What this parameter controls
      "change_relevance_to_objective": string|null, // How changing this attribute affects the objective
      "is_discrete": boolean|null, // Whether this is a discrete choice (true) or continuous value (false)
      "options": [  // Array of options if is_discrete=true
        {
          "label": string, // REQUIRED: option label/value
          "description": string|null // What this option means
        }
      ],
      "plausible_range": {  // Valid range for this attribute (null if unbounded)
        "min": number|null, // Minimum value (null if no lower bound)
        "max": number|null, // Maximum value (null if no upper bound)
        "unit": string|null, // Unit for min/max
        "source_text": string|null // Source of the range constraint
      },
      "dependencies": [  // Other attributes/components affected when this changes
        {
          "type": string|null, // e.g., "structural", "containment", "stormwater", "aspect_ratio"
          "description": string|null // How the dependency works
        }
      ]
    }
  ]
}

**Geometry Attributes - CRITICAL**: 
- Break down geometry into separate attributes (e.g., "diameter", "height", "width", "length", "thickness") rather than combined "geometry" strings.
- For cylindrical tanks, extract: diameter, height, wall_thickness, head_type, head_thickness as SEPARATE attributes and SEPARATE decision levers.
- For rectangular components, extract: width, length, height, thickness as SEPARATE attributes and SEPARATE decision levers.
- For foundations, extract: pad_width, pad_length, pad_thickness, pile_diameter, pile_length, pile_count as SEPARATE attributes and SEPARATE decision levers.
- For platforms, extract: platform_area, platform_elevation, deck_thickness as SEPARATE attributes and SEPARATE decision levers.
- Include ALL geometric dimensions mentioned in the base_case, even if they seem "standard" or "obvious".
- If the base_case mentions "H:D = 2:1" or similar ratios, extract both height AND diameter as separate levers, plus the aspect_ratio as a separate lever.

**Component Types** (treat separately when present - DO NOT combine):
- Storage tanks/vessels (each tank is a separate component)
- Foundations (concrete pads, piles, ring walls - treat as separate components)
- Support platforms and access structures (platforms, stairs, ladders)
- Containment systems (basins, berms, liners - treat separately)
- Stormwater management systems (drainage, basins, grading)
- Instrumentation packages (sensors, transmitters, controllers)
- Electrical systems (transformers, panels, distribution)
- Civil siteworks (excavation, backfill, grading, utilities)
- Safety and access features (guardrails, platforms, manways)

**Critical Rules**:
1. EXPLORE ALL POSSIBILITIES: Identify EVERY component mentioned in the base_case, even if impact seems indirect. When in doubt, include it.
2. NO COMPONENT LEFT BEHIND: If the base_case mentions a component (tank, foundation, platform, instrumentation, electrical, containment, etc.), it should appear in your components array unless it is completely irrelevant to ANY possible change.
3. RANK BY RELEVANCE: Assign relevance_score based on directness of impact on objective (1.0 = direct primary lever, 0.5 = supporting/secondary, 0.0 = minimal/indirect). But include ALL components regardless of score.
4. ALL ATTRIBUTES AS LEVERS - MANDATORY: For each component, extract EVERY attribute as a separate decision lever. Do not combine attributes. If a tank has capacity, diameter, height, material, insulation, manway size, drain size - each becomes a separate lever. If the base_case mentions "9.48 ft diameter" and "18.96 ft height", you MUST extract both as separate levers: "tank_001_diameter" and "tank_001_height".
5. GEOMETRY FIRST: For every component, prioritize extracting ALL geometric dimensions (diameter, height, width, length, thickness, area, volume, elevation) as separate levers. These are often the most important decision levers.
6. COMPREHENSIVE COVERAGE: Include components from ALL categories present in the base_case. Do not focus only on the "obvious" primary component.
7. BASELINE CONTEXT: Include baseline_value, baseline_unit, and baseline_text for each lever to provide context.
8. MINIMUM EXPECTATION: For a typical industrial system with tanks, foundations, containment, instrumentation, and electrical, expect at least 8-12 components. If you have fewer, you are missing components.
9. MINIMUM LEVERS PER COMPONENT: For a primary component like a storage tank, expect at least 8-15+ decision levers (capacity, diameter, height, material, insulation, manway_size, drain_size, vent_size, nozzle_sizes, support_type, elevation, orientation, etc.). If a component has fewer than 3 levers, you are likely missing attributes.
10. KEY ATTRIBUTES MUST INCLUDE GEOMETRY: The key_attributes array should include geometric dimensions (diameter, height, etc.) to enable better vector search matching. Do not limit key_attributes to just capacity and material.

**Relevance Scoring Guidelines**:
- 1.0: Direct primary lever (e.g., tank capacity for "increase production" objective)
- 0.8-0.9: Strong secondary lever (e.g., number of units, material selection for cost objectives)
- 0.5-0.7: Supporting lever (e.g., instrumentation scope, containment type)
- 0.2-0.4: Indirect lever (e.g., schedule, site preparation)
- 0.0-0.1: Minimal relevance (include for completeness but low priority)
"""

MINIMAL_BASELINE_SECTION = """
-------------------------------------------------------------------------------
MINIMAL BASELINE CONTEXT
-------------------------------------------------------------------------------
Extract minimal baseline context needed to understand the system:

baseline: {
  "project": {
    "name": string|null,
    "location": string|null,
    "design_status": string|null,
    "service_description": string|null
  },
  "system_overview": {
    "primary_function": string|null,
    "primary_units_or_trains": string|null,
    "main_inputs_or_outputs": [string], // array of strings
    "operating_mode": string|null
  },
  "performance_metrics": {
    "primary_metrics": [
      {
        "name": string, // REQUIRED
        "value": number|null,
        "unit": string|null,
        "basis": string|null
      }
    ],
    "secondary_metrics": [
      {
        "name": string, // REQUIRED
        "value": number|null,
        "unit": string|null,
        "basis": string|null
      }
    ]
  }
}

**CRITICAL**: The baseline object MUST contain ONLY these three fields: "project", "system_overview", and "performance_metrics". Do NOT include any other fields such as "operating_conditions", "geometry_and_layout", "materials_of_construction", "loads_and_structural", "instrumentation_and_controls", "electrical", "safety_access_and_maintenance", "containment_and_stormwater", "codes_and_standards", "schedule", or "open_items". Those details belong in the components array, not in baseline.

Keep baseline minimal - focus on components and decision levers.
"""

CONSTRAINTS_SECTION = """
-------------------------------------------------------------------------------
CONSTRAINTS AND DESIGN RULES
-------------------------------------------------------------------------------
Extract constraints/rules that couple or limit decision levers:

{
  "name": string, "type": string, "expression": string|null, "operator": ["<=", ">=", "=", "rule"],
  "lhs_quantity": string|null, "rhs_quantity_or_value": string|null, "unit": string|null, "source_text": string
}

**Examples**: Geotechnical limits, aspect ratios (H:D = 2:1), containment requirements (110% tank volume), stormwater basis (1-inch capture), standard-size selection rules, code requirements.
"""

OUTPUT_FORMAT_SECTION = """
-------------------------------------------------------------------------------
OUTPUT FORMAT
-------------------------------------------------------------------------------
Single JSON object with EXACTLY these top-level fields:
{
  "baseline": {...}, // minimal baseline context - ONLY project, system_overview, performance_metrics
  "objective": {...}, // parsed objective
  "components": [...], // ALL components ranked by relevance_score, each with decision_levers array
  "constraints_and_rules": [...], // constraints that limit levers
  "meta": {"notes": string|null}
}

**CRITICAL OUTPUT RULES**: 
- Valid JSON, use null for unknown values
- DO NOT include "components_for_tabular_lookup" or "costs" fields - these are NOT part of V3 schema
- Baseline MUST contain ONLY: project, system_overview, performance_metrics (no other fields)
- Components MUST be sorted by relevance_score (descending: highest first)
- Each component MUST have decision_levers array with ALL editable attributes (min 1 lever per component)
- Each decision lever MUST have REQUIRED fields: lever_id, attribute_name, category
- Each decision lever SHOULD include: baseline_value, baseline_unit, baseline_text, description, change_relevance_to_objective
- Structure only (no optimization/cost estimation)
- Expected component count: 8-15+ for typical industrial systems. If fewer than 5, re-examine base_case.
"""

# Main prompt
SCENARIO_PROMPT_V3 = f"""
You are a component and decision lever identification engine for scenario analysis.

**Role**: Identify ALL components that could be changed to achieve an objective, extract ALL attributes as separate decision levers, and rank components by relevance. Do NOT optimize, resize, or estimate costs.

**Inputs**:
- [SCENARIO_REQUEST] __OBJECTIVE_CONTEXT_BLOCK__
- [ONTOLOGY_REFERENCE_BLOCK] __ONTOLOGY_REFERENCE_BLOCK__
- [BASE_CASE] Base case narrative reports (artifact_type="base_case")

**Core Focus**:
1. Identify components for change that map to the objective
2. Explore ALL possibilities systematically - include EVERY component mentioned in base_case, but rank by relevance_score
3. Extract ALL attributes as separate decision-levers for the user to play with

**IMPORTANT**: GPT-4o and similar models tend to:
1. Focus only on the most obvious primary component - You MUST systematically identify ALL components mentioned in the base_case text, including foundations, platforms, containment, instrumentation, electrical, civil works, and safety features.
2. Extract only 2-3 attributes per component - You MUST extract ALL attributes mentioned in the base_case, especially geometric dimensions (diameter, height, width, length, thickness, area, elevation, etc.). For a tank with mentioned dimensions, extract diameter AND height as separate levers, not just capacity.
3. Skip "obvious" or "standard" attributes - Every attribute is a potential lever. If the base_case mentions "9.48 ft diameter", extract it as a lever even if it seems standard.

Do not stop after identifying just the primary storage tank or vessel. Look for supporting and peripheral components as well. For each component, extract ALL attributes systematically using the attribute extraction checklist above.

{OBJECTIVE_PARSING_SECTION}

{MINIMAL_BASELINE_SECTION}

{COMPONENT_IDENTIFICATION_SECTION}

{CONSTRAINTS_SECTION}

{OUTPUT_FORMAT_SECTION}
"""


def _format_objective_context(objective: Optional[Any]) -> str:
    """Render a human-readable objective context block for the prompt."""
    default_msg = "Objective context not provided; rely on [SCENARIO_REQUEST] input."

    if objective is None:
        return default_msg

    if isinstance(objective, str):
        text = objective.strip()
        return text or default_msg

    if not isinstance(objective, Dict):
        return default_msg

    lines = []

    def add_line(label: str, key: str) -> None:
        value = objective.get(key)
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            value_str = ", ".join(str(v) for v in value if v is not None)
        else:
            value_str = str(value)
        if value_str:
            lines.append(f"- {label}: {value_str}")

    add_line("Objective text", "objective_text")
    add_line("Objective type", "objective_type")
    add_line("Target metric", "target_metric_name")
    add_line("Target direction", "target_direction")
    add_line("Target delta type", "target_delta_type")
    add_line("Target delta value", "target_delta_value")
    add_line("Target unit", "target_unit")
    add_line("Time basis / scope", "time_basis_or_scope")
    add_line("Change direction", "change_direction")
    add_line("Change magnitude", "change_magnitude")
    add_line("Change unit", "change_unit")
    add_line("Description", "description")

    if objective.get("secondary_objectives"):
        secondary = objective["secondary_objectives"]
        if isinstance(secondary, (list, tuple)):
            sec_text = ", ".join(str(item) for item in secondary if item is not None)
        else:
            sec_text = str(secondary)
        if sec_text:
            lines.append(f"- Secondary objectives: {sec_text}")

    return "\n".join(lines) if lines else default_msg


def get_scenario_prompt_v3(objective_context: Optional[Any] = None) -> str:
    """Return the V3 scenario prompt with ontology and objective references injected."""
    prompt = SCENARIO_PROMPT_V3
    
    # Replace objective context
    prompt = prompt.replace("__OBJECTIVE_CONTEXT_BLOCK__", _format_objective_context(objective_context))
    
    return prompt

