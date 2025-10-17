from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
import logging
import json
import openai
from openai import OpenAI

from ..bronze_store import db
from ..vector_db.vector_operations import (
    search_entities_by_embedding,
    retrieve_relevant_entities_for_scenario,
)

logger = logging.getLogger(__name__)
client = OpenAI()


def build_general_costing_prompt(
    scenario_description: str, intent: str, change_type: str
) -> str:
    """
    Build an elaborate prompt for cost estimation based on scenario description, intent, and change type.
    """
    prompt = f"""
You are an expert in industrial project cost estimation.

# SCENARIO OVERVIEW
- **Description:** {scenario_description}
- **Intent:** {intent}
- **Change Type:** {change_type}

# TASK
Given the above scenario, your job is to:
1. Identify which equipment, materials, or processes are relevant to the user's requirements.
2. Estimate the costs for both the current (base case) and proposed configuration.
3. Break down costs into capital, installation, operating (annual), and maintenance (annual).
4. Clearly state any assumptions made, especially for missing or estimated data.
5. Provide a confidence rating (high/medium/low) and explain your reasoning.

# OUTPUT FORMAT
Respond with a valid JSON object containing:
- base_case_total
- proposed_total
- delta
- proposed_entities (with reasons for selection)
- assumptions
- confidence
- confidence_explanation
- notes

Use actual cost values whenever possible. If data is missing, explain your estimation method and assumptions.
"""
    return prompt


# Step 0: Map user specs to embedding
def get_scenario_embedding(scenario_description, intent, change_type):
    # Example using OpenAI embedding API (replace with your provider as needed)
    from openai import OpenAI

    client = OpenAI()
    text = f"{scenario_description}\nIntent: {intent}\nChange Type: {change_type}"
    # text = build_general_costing_prompt(scenario_description, intent, change_type)
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    embedding = embedding_response.data[0].embedding
    return embedding


# Step 1: Retrieve related base case entities using vector search
def retrieve_base_case_entities(embedding, project_id, entity_types):
    # Example: Use your vector DB to search for relevant entities

    results = search_entities_by_embedding(
        embedding=embedding, project_id=project_id, entity_types=entity_types, top_k=10
    )
    # Each result should be a full entity dict
    return results


# Step 2: For each base entity, retrieve related tabular entities
def retrieve_tabular_entities(base_entities, project_id):
    from ..vector_db.vector_operations import search_entities_by_embedding

    tabular_entities = []
    for entity in base_entities:
        # Use entity name/type to build embedding for tabular search
        text = (
            f"{entity.get('properties', {}).get('name', '')} {entity.get('type', '')}"
        )
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        embedding = embedding_response.data[0].embedding
        results = search_entities_by_embedding(
            embedding=embedding,
            project_id=project_id,
            entity_types=["Material", "Equipment"],
            top_k=5,
        )
        tabular_entities.extend(results)
    # Remove duplicates by entity id
    seen = set()
    unique_tabular = []
    for t in tabular_entities:
        eid = t.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            unique_tabular.append(t)
    return unique_tabular


def match_tabular_entities_to_base(base_entities, project_id):
    """
    For each base entity, find the best matching tabular entity by partial name match.
    If no match, create an empty entry.
    Returns a list of dicts: {base_entity, tabular_entity}
    """

    matches = []
    tabular_entities = []
    query = {
        "properties.project_id": project_id,
        "type": {"$in": ["Material", "Equipment"]},
        "properties.artifact_type": "tabular_data",
    }
    results = list(db().entities.find(query).limit(20))
    tabular_entities.extend(results)

    tabular_names = [
        (t, (t.get("properties", {}).get("name") or t.get("name") or "").lower())
        for t in tabular_entities
    ]

    for base in base_entities:
        base_name = (
            base.get("properties", {}).get("name") or base.get("name") or ""
        ).lower()
        # Find tabular entity with best partial match
        best_match = None
        best_score = 0
        for t, t_name in tabular_names:
            # Simple substring match, but prefer longest common substring
            if base_name and t_name and (base_name in t_name or t_name in base_name):
                # if base_name and t_name and base_name == t_name:
                score = min(len(base_name), len(t_name))
                if score > best_score:
                    best_score = score
                    best_match = t
            # Also check for token overlap (for variations)
            elif base_name and t_name:
                base_tokens = set(base_name.split())
                t_tokens = set(t_name.split())
                overlap = len(base_tokens & t_tokens)
                if overlap > best_score:
                    best_score = overlap
                    best_match = t
        if best_match:
            matches.append({"base_entity": base, "tabular_entity": best_match})
            # matches.append(best_match)
        # else:
        #     matches.append({"base_entity": base, "tabular_entity": {}})
    return matches


def retrieve_tabular_entities_from_database(base_entities, project_id):
    """
    Retrieve tabular entities from the database based on base entities.
    """
    D = db()
    tabular_entities = []
    for entity in base_entities:
        name = entity.get("properties", {}).get("name")
        if not name:
            continue
        query = {
            "project_id": project_id,
            "type": {"$in": ["Material", "Equipment"]},
            "properties.name": name,
            "properties.artifact_type": "tabular_data",
        }
        results = list(D.entities.find(query).limit(5))
        tabular_entities.extend(results)
    # Remove duplicates by entity id
    seen = set()
    unique_tabular = []
    for t in tabular_entities:
        eid = t.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            unique_tabular.append(t)
    return unique_tabular


# Step 3: Parse cost fields from both base and tabular entities
def extract_costs(entities):
    def parse_cost(value):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value.replace("$", "").replace(",", "").strip())
            except Exception:
                return None
        return None

    costs = []
    for e in entities:
        props = e.get("properties", {})
        cost = (
            parse_cost(props.get("cost"))
            or parse_cost(props.get("cost_value"))
            or parse_cost(props.get("base_cost"))
            or parse_cost(props.get("unit_cost"))
        )
        if cost:
            costs.append(
                {
                    "id": e.get("id"),
                    "name": props.get("name") or e.get("name"),
                    "type": e.get("type"),
                    "cost": cost,
                }
            )
    return costs


# Step 4: Compute scenario deltas and build output
def compute_deltas(
    base_costs, tabular_costs, scenario_description, goal, change_type, uncertainty=0.05
):
    multiplier = 20 if "increase" in (goal or "").lower() else 1

    base_total = sum([item["cost"] for item in base_costs])
    proposed_total = sum([item["cost"] for item in tabular_costs])
    # installation = proposed_total * 0.2
    # operating_annual = proposed_total * multiplier
    # maintenance_annual = proposed_total * 0.1
    # proposed_total = proposed_total + installation + operating_annual + maintenance_annual

    delta = {
        # "proposed_total": round(proposed_total * (1 + uncertainty), 2),
        # "installation": round(installation * (1 + uncertainty), 2),
        # "operating_annual": round(operating_annual * (1 + uncertainty), 2),
        # "maintenance_annual": round(maintenance_annual * (1 + uncertainty), 2),
        # "total": round(proposed_total * (1 + uncertainty), 2),
    }

    # When building cost_breakdown, include cost_calculation_details in each CostBreakdown
    cost_calculation_details = (
        "Base case total is the sum of costs from base case entities. "
        "Proposed scenario costs are calculated as follows:\n"
        "- Capital cost: sum of costs from selected tabular entities.\n"
        # "- Installation cost: 20% of updated cost.\n"
        # f"- Operating annual cost: updated cost multiplied by scenario multiplier ({multiplier}x for 'increase' intent).\n"
        # "- Maintenance annual cost: 10% of updated cost.\n"
        # f"- All proposed costs are adjusted by the uncertainty factor ({uncertainty*100:.1f}%)."
    )

    return {
        "base_case_total": {
            # "capital": base_total,
            # "installation": None,
            # "operating_annual": None,
            # "maintenance_annual": None,
            "base_total": base_total,
            "cost_calculation_details": cost_calculation_details,
        },
        "proposed_total": {
            "proposed_total": proposed_total,
            # "installation": installation,
            # "operating_annual": operating_annual,
            # "maintenance_annual": maintenance_annual,
            # "total": proposed_total,
            # "costs": tabular_costs,
            "cost_calculation_details": cost_calculation_details,
        },
        # "delta": {
        #     "capital": round(capital * (1 + uncertainty), 2),
        #     "installation": round(installation * (1 + uncertainty), 2),
        #     "operating_annual": round(operating_annual * (1 + uncertainty), 2),
        #     "maintenance_annual": round(maintenance_annual * (1 + uncertainty), 2),
        #     "total": round(proposed_total * (1 + uncertainty), 2),
        #     "cost_calculation_details": cost_calculation_details,
        # },
    }


def run_costing_pipeline(
    scenario_description: str,
    project_id: str,
    scenario_id: str,
    cost_id: Optional[str] = None,
    entity_types: Optional[List[str]] = None,
    uncertainties: Optional[Dict[str, Any]] = None,
    goal: Optional[str] = None,
    change_type: Optional[str] = None,
    selected_entities: Optional[List[Dict[str, Any]]] = None,
    equipment_types: Optional[List[str]] = None,
    capacity_range: Optional[tuple] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    #     user_specs,
    #     project_id,
    #     entity_types=["Equipment", "Material", "Process"],
    #     uncertainty=0.025,
    # ):
    print(f"[run_costing_pipeline] selected_entities: {selected_entities}")
    # Step 0
    embedding = get_scenario_embedding(scenario_description, goal, change_type)
    # Step 1
    base_entities = retrieve_base_case_entities(embedding, project_id, entity_types)

    # Step 2
    # tabular_entities = retrieve_tabular_entities(base_entities, project_id)
    cost_details = match_tabular_entities_to_base(base_entities, project_id)

    # Step 3
    # base_costs = extract_costs(base_entities)
    # tabular_costs = extract_costs(tabular_entities)
    # Step 4
    # cost_breakdown = compute_deltas(
    #     base_costs, tabular_costs, scenario_description, goal, change_type, 0.025
    # )
    # If uncertainties is not a dict, convert it
    if not isinstance(uncertainties, dict):
        uncertainties = {
            "cost_variation": uncertainties if uncertainties is not None else 0.025
        }

    # Build output JSON
    estimate_id = cost_id or f"{uuid.uuid4()}"
    output = {
        "id": estimate_id,
        "estimate_id": estimate_id,
        "scenario_id": scenario_id,
        "project_id": project_id,
        "scenario_description": scenario_description,
        "status": "completed",
        "metadata": {
            "confidence": "medium",
            "cost_details": cost_details,
        },
    }

    return output



# # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # #


def _build_cost_estimation_prompt(
    scenario_description: str,
    scenario: Optional[Dict[str, Any]],
    base_case_entities: List[Dict[str, Any]],
    tabular_entities: List[Dict[str, Any]],
    goal: Optional[str] = None,
    change_type: Optional[str] = None,
    uncertainties: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a detailed prompt for LLM-based cost estimation.

    Args:
        scenario_description: User's description of desired changes
        scenario: Full scenario object from database
        base_case_entities: Entities from base case documents
        tabular_entities: Entities from tabular data
        goal: Scenario goal
        change_type: Type of change (Equipment, Material, Process)
        uncertainties: Uncertainty parameters

    Returns:
        Formatted prompt string
    """
    # Extract scenario metadata
    scenario_name = scenario.get("name", "Unnamed Scenario") if scenario else "N/A"
    scenario_goal = (
        goal or (scenario.get("goal") if scenario else None) or "Not specified"
    )
    scenario_change_type = (
        change_type
        or (scenario.get("change_type") if scenario else None)
        or "Not specified"
    )

    # Prepare entity summaries
    def summarize_entity(entity: Dict[str, Any]) -> str:
        props = entity.get("properties", {})
        name = entity.get("name") or props.get("name") or "Unknown"
        entity_type = entity.get("type", "Unknown")

        cost_info = []
        if props.get("capital_cost"):
            cost_info.append(f"Capital: ${props['capital_cost']:,.2f}")
        if props.get("installation_cost"):
            cost_info.append(f"Installation: ${props['installation_cost']:,.2f}")
        if props.get("operating_cost_annual"):
            cost_info.append(
                f"Operating (annual): ${props['operating_cost_annual']:,.2f}"
            )
        if props.get("maintenance_cost_annual"):
            cost_info.append(
                f"Maintenance (annual): ${props['maintenance_cost_annual']:,.2f}"
            )

        cost_str = ", ".join(cost_info) if cost_info else "No cost data"

        details = []
        if props.get("capacity"):
            details.append(
                f"Capacity: {props['capacity']} {props.get('capacity_unit', '')}"
            )
        if props.get("manufacturer"):
            details.append(f"Manufacturer: {props['manufacturer']}")
        if props.get("description"):
            details.append(f"Description: {props['description']}")

        details_str = " | ".join(details) if details else ""

        return f"- {name} ({entity_type}): {cost_str}{' | ' + details_str if details_str else ''}"

    base_case_summary = (
        "\n".join([summarize_entity(e) for e in base_case_entities[:15]])
        or "No base case entities available"
    )

    tabular_summary = (
        "\n".join([summarize_entity(e) for e in tabular_entities[:15]])
        or "No tabular entities available"
    )

    # Build prompt
    prompt = f"""You are a cost estimation expert for industrial projects. Your task is to estimate costs for a proposed scenario based on available base case data and equipment/material information.

# SCENARIO DETAILS
**Scenario Name:** {scenario_name}
**Goal:** {scenario_goal}
**Change Type:** {scenario_change_type}
**Description:** {scenario_description}

# BASE CASE ENTITIES (Current Configuration)
These are entities from the existing base case configuration:
{base_case_summary}

# AVAILABLE EQUIPMENT/MATERIALS (From Tabular Data)
These are available equipment and materials with known costs:
{tabular_summary}

# UNCERTAINTY PARAMETERS
{json.dumps(uncertainties, indent=2) if uncertainties else "No uncertainty parameters provided"}

# YOUR TASK
Based on the scenario description, estimate the following:

1. **Base Case Total Costs**: Calculate total costs for the current configuration (sum from base case entities)
2. **Proposed Configuration**: Identify which entities from available equipment/materials would be needed for the proposed scenario
3. **Proposed Total Costs**: Calculate total costs for the proposed configuration
4. **Cost Delta**: Calculate the difference (Proposed - Base Case)

# COST BREAKDOWN STRUCTURE
For both Base Case and Proposed, provide:
- Capital Cost (equipment purchase)
- Installation Cost (setup, rigging, site preparation)
- Operating Cost (Annual) (utilities, labor, consumables)
- Maintenance Cost (Annual) (if provided, otherwise estimate as 10% of capital)
- Total Cost

# ASSUMPTIONS
List all assumptions you make, such as:
- Which equipment from available options best matches the scenario needs
- Any scaling factors applied (e.g., capacity multipliers)
- Estimated costs for items without explicit pricing
- Uncertainty ranges applied

# CONFIDENCE ASSESSMENT
Provide a confidence level (high/medium/low) based on:
- Availability of exact equipment matches
- Completeness of cost data
- Clarity of scenario description
- Number of assumptions required

# OUTPUT FORMAT
Respond with a valid JSON object in this exact structure:

{{
  "base_case_total": {{
    "capital": <number or null>,
    "installation": <number or null>,
    "operating_annual": <number or null>,
    "maintenance_annual": <number or null>,
    "total": <number>
  }},
  "proposed_total": {{
    "capital": <number or null>,
    "installation": <number or null>,
    "operating_annual": <number or null>,
    "maintenance_annual": <number or null>,
    "total": <number>
  }},
  "delta": {{
    "capital": <number or null>,
    "installation": <number or null>,
    "operating_annual": <number or null>,
    "maintenance_annual": <number or null>,
    "total": <number>
  }},
  "proposed_entities": [
    {{
      "entity_id": "<entity_id from available equipment>",
      "name": "<entity name>",
      "type": "<Equipment|Material|Process>",
      "quantity": <number>,
      "unit_capital_cost": <number>,
      "total_capital_cost": <number>,
      "reason": "<why this entity was selected>"
    }}
  ],
  "assumptions": [
    "<assumption 1>",
    "<assumption 2>"
  ],
  "confidence": "<high|medium|low>",
  "confidence_explanation": "<explanation of confidence level>",
  "notes": "<additional notes or caveats>"
}}

IMPORTANT: 
- Use actual cost values from the provided entities whenever possible
- If an entity doesn't have a cost field, clearly state this in assumptions
- All monetary values should be numbers (not strings)
- Ensure proposed_entities reference actual entity_ids from the available equipment/materials
- Be conservative in estimates - prefer underestimation to overestimation
"""

    return prompt


def _call_llm_for_cost_estimation(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 4000,
) -> Dict[str, Any]:
    """
    Call OpenAI LLM for cost estimation.

    Args:
        prompt: Formatted prompt for cost estimation
        temperature: Sampling temperature (lower = more deterministic)
        max_tokens: Maximum response tokens

    Returns:
        Parsed JSON response from LLM
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cost estimation expert. Always respond with valid JSON matching the requested structure.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        logger.info(f"[LLM_COST_ESTIMATION] Successfully received response from LLM")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"[LLM_COST_ESTIMATION] Failed to parse LLM response as JSON: {e}")
        return {
            "error": "Failed to parse LLM response",
            "base_case_total": {"total": 0},
            "proposed_total": {"total": 0},
            "delta": {"total": 0},
            "proposed_entities": [],
            "assumptions": ["LLM response parsing failed"],
            "confidence": "low",
            "confidence_explanation": f"JSON parsing error: {str(e)}",
        }

    except Exception as e:
        logger.error(f"[LLM_COST_ESTIMATION] LLM call failed: {e}")
        return {
            "error": str(e),
            "base_case_total": {"total": 0},
            "proposed_total": {"total": 0},
            "delta": {"total": 0},
            "proposed_entities": [],
            "assumptions": ["LLM call failed"],
            "confidence": "low",
            "confidence_explanation": f"LLM error: {str(e)}",
        }


def _filter_entities_by_cost_fields(
    entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Filter entities that have cost-related information.
    Prioritizes entities with capital_cost, installation_cost, or operating_cost.

    Args:
        entities: List of entity dictionaries

    Returns:
        Filtered list of entities with cost information
    """
    entities_with_costs = []
    entities_without_costs = []

    for entity in entities:
        props = entity.get("properties", {})
        has_cost_info = any(
            [
                props.get("capital_cost"),
                props.get("installation_cost"),
                props.get("operating_cost_annual"),
                props.get("maintenance_cost_annual"),
            ]
        )

        if has_cost_info:
            entities_with_costs.append(entity)
        else:
            entities_without_costs.append(entity)

    # Prioritize entities with cost info, but include others if needed
    return entities_with_costs + entities_without_costs


def estimate_cost(
    scenario_description: str,
    project_id: str,
    scenario_id: str,
    cost_id: Optional[str] = None,
    entity_types: Optional[List[str]] = None,
    uncertainties: Optional[Dict[str, Any]] = None,
    goal: Optional[str] = None,
    change_type: Optional[str] = None,
    equipment_types: Optional[List[str]] = None,
    capacity_range: Optional[tuple] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Estimate costs for a scenario using vector-based retrieval and LLM.

    Steps:
    1. Retrieve relevant entities from Pinecone (semantic search)
    2. Fallback to MongoDB if vector search fails
    3. Build LLM prompt with entities
    4. Call LLM for cost estimation
    5. Parse and structure response
    6. Store estimate in MongoDB
    7. Return estimate

    Args:
        scenario_description: What the user wants to change
        project_id: Project identifier
        scenario_id: Scenario identifier
        cost_id: Cost estimate identifier (auto-generated if not provided)
        entity_types: Types of entities to consider (Equipment, Material, Process)
        uncertainties: Uncertainty parameters for cost estimation
        goal: Scenario goal (optional)
        change_type: Type of change (optional)
        equipment_types: List of equipment types to filter (optional)
        capacity_range: Tuple of (min_capacity, max_capacity) to filter (optional)
        user_id: User identifier

    Returns:
        Cost estimate dictionary
    """
    # Generate estimate_id from cost_id or create new one
    estimate_id = cost_id or f"estimate_{uuid.uuid4().hex[:12]}"

    # Default entity types if not provided
    if entity_types is None:
        entity_types = ["Equipment", "Material", "Process"]

    logger.info(
        f"[COST_ESTIMATOR] Starting estimation: {estimate_id} "
        f"for scenario: {scenario_id}"
    )

    try:
        # Fetch scenario from database
        scenario = db().scenarios.find_one({"id": scenario_id}, {"_id": 0})
        if not scenario:
            logger.warning(
                f"[COST_ESTIMATOR] Scenario {scenario_id} not found in database"
            )

        # Step 1: Retrieve relevant entities using vector search
        base_case_entities = []
        tabular_entities = []
        retrieval_method = "vector_search"

        try:
            logger.info(
                f"[COST_ESTIMATOR] Retrieving relevant entities from Pinecone "
                f"for project: {project_id}, entity_types: {entity_types}"
            )

            relevant_entities = retrieve_relevant_entities_for_scenario(
                scenario_description=scenario_description,
                project_id=project_id,
                equipment_types=equipment_types or [],
                capacity_range=capacity_range,
            )

            # If relevant_entities is empty or missing keys, raise an error to trigger fallback
            if not relevant_entities or not isinstance(relevant_entities, dict):
                raise ValueError("No relevant entities found from vector search")

            base_case_entities = relevant_entities.get("base_case", [])
            tabular_entities = relevant_entities.get("tabular", [])

            logger.info(
                f"[COST_ESTIMATOR] Vector search retrieved {len(base_case_entities)} base case "
                f"and {len(tabular_entities)} tabular entities"
            )

        except Exception as vector_error:
            logger.warning(
                f"[COST_ESTIMATOR] Vector search failed: {vector_error}. "
                f"Falling back to MongoDB query."
            )
            retrieval_method = "mongodb_fallback"

            # Fallback: Query MongoDB directly
            entity_type_filter = [t for t in entity_types]

            base_case_entities = list(
                db()
                .entities.find(
                    {
                        "properties.project_id": project_id,
                        "properties.artifact_type": "base_case",
                        "type": {"$in": entity_type_filter},
                    },
                    {"_id": 0},
                )
                .limit(50)
            )

            tabular_entities = list(
                db()
                .entities.find(
                    {
                        "properties.project_id": project_id,
                        "properties.artifact_type": "tabular_data",
                        "type": {"$in": entity_type_filter},
                    },
                    {"_id": 0},
                )
                .limit(50)
            )

            logger.info(
                f"[COST_ESTIMATOR] MongoDB fallback retrieved {len(base_case_entities)} base case "
                f"and {len(tabular_entities)} tabular entities"
            )

        # Filter entities to prioritize those with cost information
        base_case_entities = _filter_entities_by_cost_fields(base_case_entities)
        tabular_entities = _filter_entities_by_cost_fields(tabular_entities)

        # Limit to top entities (vector search already sorted by relevance)
        base_case_entities = base_case_entities[:20]
        tabular_entities = tabular_entities[:20]

        logger.info(
            f"[COST_ESTIMATOR] After filtering, using {len(base_case_entities)} base case "
            f"and {len(tabular_entities)} tabular entities"
        )

        # Step 2: Build prompt for LLM
        prompt = _build_cost_estimation_prompt(
            scenario_description=scenario_description,
            scenario=scenario,
            base_case_entities=base_case_entities,
            tabular_entities=tabular_entities,
            goal=goal,
            change_type=change_type,
            uncertainties=uncertainties,
        )

        # Step 3: Call LLM for cost estimation
        logger.info(f"[COST_ESTIMATOR] Calling LLM for cost estimation")
        llm_response = _call_llm_for_cost_estimation(prompt)

        # Extract cost breakdown from LLM response
        base_case_total = llm_response.get("base_case_total", {})
        proposed_total = llm_response.get("proposed_total", {})
        delta = llm_response.get("delta", {})
        proposed_entities = llm_response.get("proposed_entities", [])
        assumptions = llm_response.get("assumptions", [])
        confidence = llm_response.get("confidence", "medium")
        confidence_explanation = llm_response.get("confidence_explanation", "")
        notes = llm_response.get("notes", "")

        # Check for errors
        if "error" in llm_response:
            logger.error(
                f"[COST_ESTIMATOR] LLM returned error: {llm_response['error']}"
            )
            status = "failed"
        else:
            status = "completed"

        # Step 4: Structure response
        estimate = {
            "id": cost_id or f"estimate_{uuid.uuid4().hex}",
            "user_id": user_id,
            "estimate_id": estimate_id,
            "scenario_id": scenario_id,
            "scenario_description": scenario_description,
            "project_id": project_id,
            "entity_types": entity_types,
            "uncertainties": uncertainties,
            "goal": goal,
            "change_type": change_type,
            "status": status,
            "confidence": confidence,
            "retrieval_method": retrieval_method,
            "cost_breakdown": {
                "base_case_total": {
                    "capital": base_case_total.get("capital"),
                    "installation": base_case_total.get("installation"),
                    "operating_annual": base_case_total.get("operating_annual"),
                    "maintenance_annual": base_case_total.get("maintenance_annual"),
                    "total": base_case_total.get("total", 0),
                },
                "proposed_total": {
                    "capital": proposed_total.get("capital"),
                    "installation": proposed_total.get("installation"),
                    "operating_annual": proposed_total.get("operating_annual"),
                    "maintenance_annual": proposed_total.get("maintenance_annual"),
                    "total": proposed_total.get("total", 0),
                },
                "delta": {
                    "capital": delta.get("capital"),
                    "installation": delta.get("installation"),
                    "operating_annual": delta.get("operating_annual"),
                    "maintenance_annual": delta.get("maintenance_annual"),
                    "total": delta.get("total", 0),
                },
            },
            "relevant_entities": {
                "base_case": base_case_entities[:10],
                "tabular": tabular_entities[:10],
                "proposed": proposed_entities,
            },
            "entity_counts": {
                "base_case_retrieved": len(base_case_entities),
                "tabular_retrieved": len(tabular_entities),
                "proposed_count": len(proposed_entities),
            },
            "assumptions": assumptions,
            "notes": notes,
            "confidence_explanation": confidence_explanation,
            "estimated_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Step 5: Store in MongoDB
        db().cost_estimates.insert_one(estimate.copy())

        logger.info(f"[COST_ESTIMATOR] Estimate stored: {estimate['id']}")

        return estimate

    except Exception as e:
        logger.error(f"[COST_ESTIMATOR] Failed to estimate cost: {e}", exc_info=True)

        # Store failed estimate
        failed_estimate = {
            "id": cost_id or f"estimate_{uuid.uuid4().hex}",  # <-- Add this line
            "estimate_id": estimate_id,
            "scenario_id": scenario_id,
            "scenario_description": scenario_description,
            "project_id": project_id,
            "entity_types": entity_types,
            "status": "failed",
            "error": str(e),
            "estimated_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        try:
            db().cost_estimates.insert_one(failed_estimate)
        except Exception as db_error:
            logger.error(f"[COST_ESTIMATOR] Failed to store error: {db_error}")

        raise
