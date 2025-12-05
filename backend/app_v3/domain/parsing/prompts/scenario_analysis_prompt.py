import json
from typing import Any, Dict, Optional

from ...ontology.ontology import ENTITY_ONTOLOGY

# Convert the ontology to JSON with all white spaces and new-line characters removed
NODE_TYPES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_types", []), indent=1).replace(" ", "").replace("\n", "")
NODE_PROPERTIES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_properties", []), indent=1).replace(" ", "").replace("\n", "")
NODE_PROP_EXAMPLES_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_prop_examples", {}), indent=1).replace(" ", "").replace("\n", "")
# EDGE_TYPES_JSON = json.dumps(ENTITY_ONTOLOGY.get("edge_types", []), indent=1).replace(" ", "").replace("\n", "")
# EDGE_PROPERTIES_JSON = json.dumps(ENTITY_ONTOLOGY.get("edge_properties", []), indent=1).replace(" ", "").replace("\n", "")
# NODE_DESCRIPTIONS_JSON = json.dumps(ENTITY_ONTOLOGY.get("node_descriptions", {}), indent=1).replace(" ", "").replace("\n", "")
# EDGE_DESCRIPTIONS_JSON = json.dumps(ENTITY_ONTOLOGY.get("edge_descriptions", {}), indent=1).replace(" ", "").replace("\n", "")
# EDGE_PROP_EXAMPLES_JSON = json.dumps(ENTITY_ONTOLOGY.get("edge_prop_examples", {}), indent=1).replace(" ", "").replace("\n", "")

ONTOLOGY_REFERENCE_BLOCK = f"""
NODE_TYPES (ENTITY_ONTOLOGY.node_types):
{NODE_TYPES_JSON}

NODE_PROPERTIES (ENTITY_ONTOLOGY.node_properties):
{NODE_PROPERTIES_JSON}

NODE_PROP_EXAMPLES:
{NODE_PROP_EXAMPLES_JSON}
""".strip()


SCENARIO_PROMPT_TEMPLATE = """
    You are a scenario reconstruction engine for industrial projects. Extract structured data from base case reports to support scenario resizing and cost estimation.

    Inputs:
    1) [SCENARIO_REQUEST]: User objective (e.g., "increase production by 20%", "reduce capex by 5%")
    2) [BASE_CASE]: Base case narrative reports (artifact_type="base_case")

    Tasks: Reconstruct baseline, parse objective, extract decision levers, and identify constraints.

    Output: Single JSON object supporting resizing and cost re-estimation. Do NOT optimize or resize—only structure information.

    -------------------------------------------------------------------------------
    OBJECTIVE CONTEXT (IF PROVIDED BY CALLER)
    -------------------------------------------------------------------------------
    __OBJECTIVE_CONTEXT_BLOCK__

    -------------------------------------------------------------------------------
    ONTOLOGY REFERENCE (AUTO-INJECTED FROM backend/app_v3/domain/ontology/ontology.py)
    -------------------------------------------------------------------------------
    __ONTOLOGY_REFERENCE_BLOCK__

    -------------------------------------------------------------------------------
    TASK DETAILS
    -------------------------------------------------------------------------------
    1) BASELINE RECONSTRUCTION
    Capture *what exists today* before scenario changes. Populate available fields; use null for unknown.

    baseline.project: name, location, design_status, service_description
    baseline.system_overview: primary_function, primary_units_or_trains, key_inputs_or_outputs, operating_mode, interfaces_or_dependencies
    baseline.performance_metrics: primary_metrics/secondary_metrics arrays of {name, value, unit, basis}
    baseline.operating_conditions: array of {name, value, unit, description} for process conditions, ambient, duty cycles
    baseline.physical_configuration: per area/asset {name, role_or_scope, key_dimensions_or_capacity[], layout_notes}, site_layout_summary
    baseline.materials_and_construction: array of {component, material, finish_or_grade, notes}
    baseline.structural_and_foundation: loads, stresses, support types, design factors, geotechnical constraints
    baseline.controls_and_automation: instruments_and_devices[], control_architecture_summary, automation_scope_options
    baseline.power_and_utilities: supply_and_distribution, powered_elements, auxiliary utilities
    baseline.safety_access_and_maintenance: safety_features, access_features, maintenance_strategy
    baseline.compliance_and_regulatory: codes_and_standards[], regulatory_requirements[], environmental_or_policy_limits[], notes
    baseline.schedule_and_execution: milestone_durations[], total_duration_range_weeks
    baseline.open_items: array of {description, impacted_area}

    2) OBJECTIVE PARSING
    Extract from [SCENARIO_REQUEST]:
    objective: {objective_text, objective_type: ["increase_capacity", "increase_production", "reduce_capex", "reduce_opex", "reduce_total_cost", "change_availability", "change_reliability", "change_instrumentation_scope", "change_containment_type", "other"], target_metric_name, target_direction: "increase"|"decrease", target_delta_type: "relative_percent"|"absolute", target_delta_value, target_unit, time_basis_or_scope, secondary_objectives[]}

    3) DECISION LEVER EXTRACTION
    Identify parameters that are tunable/optional/TBD, drive capacity/duty/cost, or participate in scaling/quantity assumptions.

    decision_levers[]: {name, category: ["capacity", "geometry", "material", "instrumentation", "electrical", "containment", "stormwater", "civil", "schedule", "cost_model"], description, baseline_value, baseline_unit, baseline_text, change_relevance_to_objective, is_discrete, options[]: {label, description}, plausible_range: {min, max, unit, source_text}, dependencies[]: {type, description}}

    Include when present: capacity/geometry (capacity_target, standard_capacity, diameter, height, aspect_ratio, units), materials (material_of_construction, containment_type), instrumentation (scope_level, device presence/absence), electrical (transformer_size, panel_type), civil (excavation_volume, borings, survey_detail), schedule (phase durations).

    Cost model levers:
    - Top-down: capacity_ratio, weight_ratio, standard_size_rule, contingency_percent, per_item_scaling_behavior (for items scaled by capacity/weight or fixed)
    - Bottom-up: unit_cost_range_selection (min/midpoint/max), quantity_assumption_levers (deck_area, steel_tonnage, concrete_volume, excavation_volume, piping_length, instrument_counts, transformer_size, etc.)

    4) COMPONENT IDENTIFICATION FOR TABULAR LOOKUP
    CRITICAL: Extract ALL major physical components and cost-carrying elements mentioned in the baseline. This is essential for accurate cost estimation.

    components_for_tabular_lookup[]: {role, key_attributes[]: {name, value, unit}, quantity}

    COMPONENT EXTRACTION RULES:
    1. INCLUDE ALL COST-CARRYING COMPONENTS: Extract every piece of equipment, structure, system, or material that has a cost impact, including:
    - Equipment: tanks, pumps, heat exchangers, vessels, compressors, filters, separators, clarifiers, chillers, heaters, blowers, fans
    - Structures: foundations, platforms, buildings, containment systems, berms, liners
    - Piping and instrumentation: major pipe runs, valves, instruments, control panels, PLC systems
    - Electrical: transformers, switchgear, motor control centers, motors, distribution systems
    - Civil: excavation, grading, roads, utilities, site preparation
    - Materials: bulk materials with significant cost (concrete, steel, liners, coatings)

    2. BE COMPREHENSIVE: When in doubt, include the component. It's better to extract too many than too few. Every component mentioned in the baseline that could affect cost should be included.

    3. MINIMUM ATTRIBUTES: Each component must have at least 2-3 key_attributes (preferably 4-6):
    - Primary sizing: capacity, volume, throughput, power, duty, diameter, height, length, area
    - Material: material_of_construction, finish_or_grade
    - Service: service, fluid, application, pressure_rating, temperature_rating
    - Configuration: orientation, type, style, mounting
    - Electrical: voltage, phase, frequency (if applicable)

    4. QUANTITY: Always include quantity (default: 1 if not specified)

    5. ROLE NAMING: Use descriptive, industry-standard names:
    - Good: "Water storage tank", "Centrifugal pump", "Heat exchanger", "Control panel"
    - Bad: "Tank 1", "Pump", "Equipment", "Item"

    6. NO DUPLICATES: Each unique component (role + key_attributes combination) appears only once.

    EXAMPLES OF COMPONENTS TO EXTRACT:
    - Storage tanks, vessels, silos, bins
    - Pumps, compressors, blowers, fans
    - Heat exchangers, chillers, heaters, boilers
    - Filters, separators, clarifiers, scrubbers
    - Control panels, PLC systems, instrumentation, transmitters
    - Transformers, switchgear, motor control centers, distribution panels
    - Foundations, platforms, structural steel, supports
    - Piping systems, valves, fittings, flanges
    - Containment systems, liners, berms, dikes
    - Buildings, shelters, enclosures, buildings
    - Roads, grading, excavation, site preparation
    - Any equipment or system with measurable cost impact

    OUTPUT: {baseline, objective, decision_levers[], components_for_tabular_lookup[], meta: {notes}}

    Rules: Valid JSON only. Use null for unknown values. No extra top-level keys. Structure only—no optimization/resizing.
    """.strip()


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


def get_scenario_prompt(objective_context: Optional[Any] = None, process_tabular_data: bool = False) -> str:
    """Return the scenario prompt with ontology and objective references injected."""
    prompt = SCENARIO_PROMPT_TEMPLATE
    
    # Replace ontology and objective context
    prompt = prompt.replace("__ONTOLOGY_REFERENCE_BLOCK__", ONTOLOGY_REFERENCE_BLOCK)
    prompt = prompt.replace("__OBJECTIVE_CONTEXT_BLOCK__", _format_objective_context(objective_context))
    
    # Handle tabular data conditional sections
    if process_tabular_data:
        prompt = prompt.replace(
            "__TABULAR_DATA_INPUT_DESCRIPTION__",
            "3) One or more supporting tables or structured data (artifact_type=\"tabular_data\"),\nincluding unit-cost workbooks and vendor size/cost tables."
        )
        prompt = prompt.replace(
            "__TABULAR_DATA_TASK_DESCRIPTION__",
            "- Identify *impacted components* that must be queried in tabular_data."
        )
        prompt = prompt.replace(
            "__TABULAR_DATA_SECTION__",
            "[TABULAR_DATA]\n<optional: narrative references to tables, BOMs, cost sheets, unit-cost workbooks,\nvendor quantity/cost tables, artifact_type=\"tabular_data\">"
        )
        prompt = prompt.replace("__TABULAR_DATA_SEPARATOR__", " and tabular_data")
        prompt = prompt.replace(
            "__TABULAR_LOOKUP_TASK__",
            "5) COMPONENT / TABULAR LOOKUP KEYS"
        )
        prompt = prompt.replace(
            "__COST_STRUCTURE_TASK__",
            "6) COST STRUCTURE, COST MODEL CONFIGURATION, AND OPTIONS"
        )
        prompt = prompt.replace(
            "__TABULAR_LOOKUP_SECTION__",
            """-------------------------------------------------------------------------------
            5) COMPONENT / TABULAR LOOKUP KEYS
            -------------------------------------------------------------------------------
            Identify all major physical components and cost-carrying elements that will need
            to be matched against tabular_data (BOM, cost tables, unit-cost workbooks,
            vendor tables)."""
        )
    else:
        prompt = prompt.replace("__TABULAR_DATA_INPUT_DESCRIPTION__", "")
        prompt = prompt.replace(
            "__TABULAR_DATA_TASK_DESCRIPTION__",
            "- Identify *impacted components* for cost estimation (tabular data not available)."
        )
        prompt = prompt.replace("__TABULAR_DATA_SECTION__", "")
        prompt = prompt.replace("__TABULAR_DATA_SEPARATOR__", "")
        prompt = prompt.replace("__TABULAR_LOOKUP_TASK__", "")
        prompt = prompt.replace(
            "__COST_STRUCTURE_TASK__",
            "5) COST STRUCTURE, COST MODEL CONFIGURATION, AND OPTIONS"
        )
        prompt = prompt.replace(
            "__TABULAR_LOOKUP_SECTION__",
            """-------------------------------------------------------------------------------
            5) COMPONENT IDENTIFICATION (TABULAR DATA NOT AVAILABLE)
            -------------------------------------------------------------------------------
            Identify all major physical components and cost-carrying elements. Note that
            tabular data (BOM, cost tables, unit-cost workbooks, vendor tables) is not
            available in this analysis, so extract component information from the base case
            reports only."""
        )
    
    return prompt


SCENARIO_PROMPT = get_scenario_prompt()

