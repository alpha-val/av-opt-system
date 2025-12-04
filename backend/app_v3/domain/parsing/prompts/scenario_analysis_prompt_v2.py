import json
from typing import Any, Dict, Optional

from ...ontology.ontology import AV_MSIO_ONTOLOGY, ENTITY_ONTOLOGY, get_default_ontology
from ...ontology.ontology import ENTITY_ONTOLOGY

# Convert the ontology to JSON with all white spaces and new-line characters removed
NODE_TYPES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_types", []), indent=1).replace("\n", "")
NODE_PROPERTIES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_properties", []), indent=1).replace("\n", "")
NODE_PROP_EXAMPLES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_prop_examples", {}), indent=1).replace("\n", "")

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


SCENARIO_PROMPT = """
You are Step 1 of a scenario reconstruction engine. Structure baseline configuration, objectives, components, decision levers, and constraints for downstream parameter updates and cost estimation.

**Role**: Extract and structure information. Do NOT optimize, resize, or estimate costs.

**Inputs**:
- [SCENARIO_REQUEST] __OBJECTIVE_CONTEXT_BLOCK__
- [ONTOLOGY_REFERENCE_BLOCK] __ONTOLOGY_REFERENCE_BLOCK__
- [BASE_CASE] Base case narrative reports (artifact_type="base_case")

**Tasks**:
1) BASELINE RECONSTRUCTION
2) OBJECTIVE PARSING
3) DECISION LEVER EXTRACTION
4) COMPONENT IDENTIFICATION & ATTRIBUTES
5) CONSTRAINTS AND DESIGN RULES

-------------------------------------------------------------------------------
1) BASELINE RECONSTRUCTION
-------------------------------------------------------------------------------
Extract from base_case into "baseline" block:

baseline.project: {name, location, design_status, service_description}
baseline.system: {primary_function, primary_units_or_trains, main_fluids_or_materials, operating_mode}
baseline.capacity_and_duty: {primary_capacity_metrics, secondary_capacity_metrics} - arrays of {name, value, unit, basis}
baseline.operating_conditions: array of {name, value, unit, description} for temp, pressure, fluid properties, site conditions
baseline.geometry_and_layout: {summary, site_footprint: {immediate_footprint_area, working_area}}
baseline.materials_of_construction: array of {component, material, notes}
baseline.loads_and_structural: {fluid_weight, tank_weight_allowance, total_loaded_weight, support_type, site_geotech: {allowable_bearing_capacity}}
baseline.instrumentation_and_controls: {instruments_and_devices: [{tag_or_role, type, purpose}], control_architecture_summary}
baseline.electrical: {powered_elements, supply_and_distribution, optional_loads}
baseline.safety_access_and_maintenance: {safety_features, access_features}
baseline.containment_and_stormwater: {containment_basis, containment_volume, stormwater_basis, stormwater_volume, drainage_and_grading}
baseline.codes_and_standards: list of referenced codes (ASME, AISC, ACI, NEC, NFPA, OSHA, ASTM, NACE, etc.)
baseline.schedule: {milestone_durations: [{name, duration_range_weeks}], total_duration_range_weeks}
baseline.open_items: array of {description, impacted_area}

Treat as high-level summary; component details go in "components" array.

-------------------------------------------------------------------------------
2) OBJECTIVE PARSING
-------------------------------------------------------------------------------
Extract from SCENARIO_REQUEST into "objective" block:

objective: {
  objective_text, objective_type: ["increase_capacity", "increase_production", "reduce_capex", "reduce_opex", "reduce_total_cost", "change_availability", "change_reliability", "change_instrumentation_scope", "change_containment_type", "other"],
  target_metric_name, target_direction: ["increase", "decrease"], target_delta_type: ["relative_percent", "absolute"],
  target_delta_value, target_unit, time_basis_or_scope,
  secondary_objectives: [...] // if multiple objectives
}

Interpret only; do not optimize.

-------------------------------------------------------------------------------
3) DECISION LEVER EXTRACTION
-------------------------------------------------------------------------------
Extract ALL parameters that: are tunable/optional/TBD, drive capacity/duty/configuration, govern scope, affect cost, are alternatives/options, or could achieve objective.

**Lever Schema**:
{
  "lever_id": string, "name": string, "category": string, "description": string,
  "baseline_value": number|string|null, "baseline_unit": string|null, "baseline_text": string|null,
  "change_relevance_to_objective": string, "is_discrete": bool,
  "options": [{"label": string, "description": string|null}], // if discrete
  "plausible_range": {"min": number|null, "max": number|null, "unit": string|null, "source_text": string|null},
  "dependencies": [{"type": string, "description": string}],
  "applies_to_components": [{
    "component_id": string|null, "role": string|null, "attribute_names": [string],
    "mapping_type": ["direct", "proportional", "formula", "choice", "rule_based"],
    "mapping_expression": string|null, // e.g., "component.capacity = lever_value"
    "derived_attributes": [{"attribute_names": [string], "rule_reference": string|null, "description": string|null}]
  }],
  "update_notes": string|null
}

**Categories to extract** (when present):
- capacity_and_geometry: tank_nominal_storage_capacity, selected_standard_capacity, tank_diameter, tank_height, aspect_ratio, number_of_units
- materials_and_spec: material_of_construction, containment_type
- instrumentation_and_controls: instrumentation_scope_level, device presence/absence
- electrical_scope: transformer_size_kVA, panel type, sump pump presence
- civil/earthwork/survey: excavation_volume, number_of_borings, topo_survey_detail_level
- schedule: adjustable phase durations
- operations_and_reliability: availability, redundancy, operational strategy
- cost_model_levers: capacity_ratio, weight_ratio, standard_size_rule, contingency_percent, per_item_scaling_behavior, unit_cost_range_selection, quantity_assumption_levers

**Rules**: Link levers to component attributes via applies_to_components. Merge synonyms into single lever_id. Capture derived attributes (e.g., diameter/height from capacity via H:D rule).

-------------------------------------------------------------------------------
4) COMPONENT IDENTIFICATION & ATTRIBUTES
-------------------------------------------------------------------------------
Identify ALL major components participating in: primary function, equipment, materials, capacity/duty, geometry/layout, containment/stormwater, instrumentation/electrical, civil/structural.

**Component Schema**:
{
  "role": string, // standard industry terminology
  "key_attributes": [{"name": string, "value": string|number|null, "unit": string|null}], // min 2 for vector search
  "quantity": number|null, // numeric count
  "relevance_to_objective": string, "relevance_score": number, // 0.0-1.0
  "editable_attributes": [string],
  "editable_metadata": {  // REQUIRED: Must contain entry for EVERY attribute in editable_attributes
    "attribute_name": {
      "baseline_value": string|number|null, "baseline_unit": string|null, "baseline_text": string|null,
      "category": string, "description": string|null, "change_relevance_to_objective": string|null,
      "is_discrete": boolean|null, "options": [{"label": string, "description": string|null}],
      "plausible_range": {"min": number|null, "max": number|null, "unit": string|null, "source_text": string|null},
      "dependencies": [{"type": string|null, "description": string|null}]
    }
  }
}

**Geometry Attributes**: Break down geometry into separate attributes (e.g., "diameter", "height", "width", "length", "thickness") rather than combined "geometry" strings. For cylindrical tanks, use "diameter" and "height" as separate attributes. For rectangular components, use "width", "length", "height".

**Component Types** (treat separately when present): storage tanks, foundations (pads/piles/ring walls), support platforms/access, containment basins/berms/liners, stormwater systems, instrumentation packages, electrical supply/distribution, civil siteworks.

**Critical**: 
- For EVERY decision lever, ensure corresponding component with editable attributes. Rich levers → rich components.
- editable_metadata is REQUIRED and MUST contain an entry for EVERY attribute listed in editable_attributes.
- Each editable_metadata entry must include at minimum: baseline_value, baseline_unit, category, description.

-------------------------------------------------------------------------------
5) CONSTRAINTS AND DESIGN RULES
-------------------------------------------------------------------------------
Extract constraints/rules that couple or limit levers/attributes:

{
  "name": string, "type": string, "expression": string|null, "operator": ["<=", ">=", "=", "rule"],
  "lhs_quantity": string|null, "rhs_quantity_or_value": string|null, "unit": string|null, "source_text": string
}

**Examples**: Geotechnical limits, aspect ratios (H:D = 2:1), containment requirements (110% tank volume), stormwater basis (1-inch capture), standard-size selection rules, custom vs standard equipment rules, code requirements.

-------------------------------------------------------------------------------
OUTPUT FORMAT
-------------------------------------------------------------------------------
Single JSON object:
{
  "baseline": {...}, "objective": {...}, "components": [...], "decision_levers": [...],
  "constraints_and_rules": [...], "meta": {"notes": string|null}
}

**Rules**: Valid JSON, use null for unknown values, no extra top-level keys, structure only (no optimization/cost estimation).
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


def get_scenario_prompt_v2(objective_context: Optional[Any] = None) -> str:
    """Return the scenario prompt with ontology and objective references injected."""
    prompt = SCENARIO_PROMPT
    
    # Replace ontology and objective context
    # prompt = prompt.replace("__ONTOLOGY_REFERENCE_BLOCK__", ONTOLOGY_REFERENCE_BLOCK)
    prompt = prompt.replace("__OBJECTIVE_CONTEXT_BLOCK__", _format_objective_context(objective_context))
    
    return prompt