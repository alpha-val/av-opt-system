"""
LLM prompt for scenario analysis.

Analyzes relevant entities from base case to identify local objectives for a given global objective.
Follows app_v2 patterns using LangChain message format.
"""

from typing import Dict, Any
from ...ontology.ontology import get_default_ontology
from ...ontology.loader import get_ontology as get_ontology_instance

# Get ontology instance
default_ontology = get_default_ontology()
ontology_instance = get_ontology_instance()
entity_ont = ontology_instance.entity_ontology

# Convert EntityOntology to dict format
ontology_dict = {
    "NODE_TYPES": entity_ont.node_types,
    "EDGE_TYPES": entity_ont.edge_types,
    "NODE_PROPERTIES": entity_ont.node_properties,
    "EDGE_PROPERTIES": entity_ont.edge_properties,
    "NODE_DESCRIPTIONS": entity_ont.node_descriptions,
    "EDGE_DESCRIPTIONS": entity_ont.edge_descriptions,
    "NODE_PROP_EXAMPLES": entity_ont.node_prop_examples,
    "EDGE_PROP_EXAMPLES": entity_ont.edge_prop_examples,
}

# Get MSIO ontology
from ...ontology.ontology import AV_MSIO_ONTOLOGY
msio_ontology_text = str(AV_MSIO_ONTOLOGY)


def get_scenario_analysis_prompt(
    global_objective: Dict[str, Any],
    entities_summary: str,
    base_case_text: str = "",
) -> str:
    """
    Generate the LLM prompt for scenario analysis.
    
    Args:
        global_objective: Dictionary with goal_type, change_direction, change_magnitude, change_unit, description
        entities_summary: Summary of entities from base case (JSON or formatted text)
        base_case_text: Optional full base case text for context
    
    Returns:
        Formatted prompt string
    """
    
    goal_type = global_objective.get("goal_type", "other")
    change_direction = global_objective.get("change_direction", "increase")
    change_magnitude = global_objective.get("change_magnitude", 0)
    change_unit = global_objective.get("change_unit", "%")
    description = global_objective.get("description", "")
    
    prompt = f"""
--------------------------------------------------------------------------------
SYSTEM PROMPT — SCENARIO ANALYSIS FROM BASE CASE ENTITIES
--------------------------------------------------------------------------------
ROLE
You are an expert process engineer & cost estimator.
Your task is to analyze entities extracted from a base case technical or cost report
and identify which entities and parameters are relevant to achieving a GLOBAL OBJECTIVE.

--------------------------------------------------------------------------------
GLOBAL OBJECTIVE
--------------------------------------------------------------------------------
Goal Type: {goal_type}
Change Direction: {change_direction}
Change Magnitude: {change_magnitude} {change_unit}
Description: {description}

--------------------------------------------------------------------------------
SCOPE
--------------------------------------------------------------------------------
Identify all **local objectives**: entity-parameter pairs that directly govern
or constrain the global objective (first- or second-order effects).

For Production Change scenarios:
- Identify entities that affect throughput, capacity, flow rate, production rate
- Consider equipment, processes, materials, controls that limit or enable production
- Identify bottlenecks and dependencies

For Capex Change scenarios:
- Identify entities that drive capital costs (equipment, materials, civil, electrical)
- Consider cost-reduction or cost-increase levers
- Identify trade-offs (quality, reliability, schedule)

--------------------------------------------------------------------------------
INPUTS
--------------------------------------------------------------------------------
1) ENTITIES FROM BASE CASE:
{entities_summary}

2) BASE CASE TEXT (for context and evidence):
{base_case_text[:5000] if base_case_text else "Not provided - use entity data only"}

3) ONTOLOGY:
Node Types: {', '.join(ontology_dict.get('NODE_TYPES', [])[:20])}...
Edge Types: {', '.join(ontology_dict.get('EDGE_TYPES', [])[:20])}...

MSIO Ontology: Available for entity classification

--------------------------------------------------------------------------------
ANALYSIS POLICY
--------------------------------------------------------------------------------
- Ground every value, quote, and rationale in the base case entities or text
- No hallucinations: if data are missing, set fields to `null` and create an
  `uncertainties` entry with a remediation action
- Preserve units exactly as shown in the base case; do not convert
- Use explicit references (entity IDs, section headers, page numbers)
- Calculate relevance_score (0.0-1.0) based on how directly the entity affects the global objective
- First-order effects (direct impact) should have relevance_score >= 0.7
- Second-order effects (indirect impact) should have relevance_score 0.4-0.7
- Loosely related entities should have relevance_score < 0.4

--------------------------------------------------------------------------------
OUTPUT — STRICT JSON ONLY
--------------------------------------------------------------------------------
Return a single JSON object with the following structure:

{{
  "scenario_summary": "<summary of base case relevant to this scenario; 300-500 words; markdown format>",
  "local_objectives": [
    {{
      "entity_id": "<entity ID from base case>",
      "entity_name": "<entity name>",
      "entity_type": "<Equipment|Process|Material|Control|Civil|Electrical|Other>",
      "parameter": "<parameter name, e.g., flow_rate, capacity, power, cost_value>",
      "relevance_score": 0.0-1.0,
      "base_value": "<original value from base case>",
      "base_unit": "<unit if applicable>",
      "rationale": "<explanation of why this entity/parameter is relevant; 100-200 words>",
      "evidence": ["<relevant excerpts or references from base case>"]
    }}
  ],
  "assumptions": [
    {{
      "text": "<assumption text>",
      "assumption_type": "Design|Operational|Market|Environmental",
      "refs": ["<section/page references>"]
    }}
  ],
  "policies": [
    {{
      "text": "<policy or code/standard text>",
      "domain": "Safety|Code|Cost|Procurement|Quality|Environmental",
      "refs": ["<section/page references>"]
    }}
  ],
  "constraints": [
    {{
      "constraint": "<constraint description>",
      "basis": "Physical|Regulatory|Budgetary|Schedule|Availability",
      "refs": ["<section/page references>"]
    }}
  ],
  "related_sections": ["<list of relevant section headers or page numbers>"],
  "confidence": 0.0-1.0
}}

--------------------------------------------------------------------------------
STRICT REQUIREMENTS
--------------------------------------------------------------------------------
- Output MUST be valid JSON with no additional text
- Identify ALL relevant entities, even loosely related ones (relevance_score < 0.4)
- For each local objective, provide clear rationale linking it to the global objective
- Include evidence excerpts from base case text when available
- Do not hallucinate entities or parameters not present in the input
- Only include evidence that actually appears in the base case text
- Create a thorough summary (scenario_summary) that synthesizes relevant base case information
- The analysis should inform detailed scenario development and cost estimations

--------------------------------------------------------------------------------
EXAMPLE
--------------------------------------------------------------------------------
Global Objective: Increase production by 8%

Local Objectives might include:
- Pump entity with flow_rate parameter (relevance_score: 0.9) - directly limits throughput
- Tank entity with capacity parameter (relevance_score: 0.8) - affects buffering capacity
- Process entity with throughput parameter (relevance_score: 0.85) - core production metric
- Electrical system with power parameter (relevance_score: 0.6) - enables equipment operation

--------------------------------------------------------------------------------
END
--------------------------------------------------------------------------------
"""
    
    return prompt.strip()

