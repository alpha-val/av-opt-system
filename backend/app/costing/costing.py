# in_pipeline/costing.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import re
import uuid
from datetime import datetime
import logging
from openai import OpenAI

from ..bronze_store import db
from ..vector_db.vector_operations import (
    search_entities_by_embedding,
)

logger = logging.getLogger(__name__)
client = OpenAI()

# # # # # # # # # # # # # # # # # # # # # # # #

# UTILITIES FOR COST ESTIMATION

# # # # # # # # # # # # # # # # # # # # # # # #

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
UNIT_PAIR_RE = re.compile(r"^\s*([-\d.,]+)\s*([A-Za-z/%\"-]+)?\s*$")


def _to_float(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    m = NUM_RE.search(s)
    if not m:
        return default
    try:
        return float(m.group(0).replace(",", ""))
    except Exception:
        return default


def _parse_value_unit(x: Any) -> Tuple[float, str]:
    """Return (value, unit) from strings like '1000 tph', '720 kW', '90%'."""
    if x is None:
        return 0.0, ""
    if isinstance(x, (int, float)):
        return float(x), ""
    s = str(x).strip()
    m = UNIT_PAIR_RE.match(s)
    if not m:
        return _to_float(s), ""
    val = _to_float(m.group(1))
    unit = (m.group(2) or "").strip()
    return val, unit


def _percent_to_frac(x: Any, default: float = 1.0) -> float:
    v, u = _parse_value_unit(x)
    if "%" in (u or "") or (isinstance(x, str) and "%" in x):
        return max(0.0, min(1.0, v / 100.0))
    # If someone passes 0–1 already, accept it; if >1, assume already a frac?
    if v <= 1.0:
        return v if v > 0 else default
    # Otherwise treat as %, e.g., 90 -> 0.9
    return v / 100.0


def _tpd_from_capacity(props: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Derive tpd from system_capacity and availability if present.
    Accepts '1000 tph', '20,000 tpd', etc. Defaults to 24h*availability for tph.
    """
    capacity_raw = props.get("system_capacity") or props.get("capacity") or ""
    val, unit = _parse_value_unit(capacity_raw)
    availability = _percent_to_frac(props.get("availability_target", 0.9), 0.9)

    tpd = 0.0
    if "tpd" in unit.lower():
        tpd = val
    elif "tph" in unit.lower() or "t/h" in unit.lower():
        tpd = val * 24.0 * availability
    elif "tpa" in unit.lower():  # per annum
        tpd = val / 365.0
    else:
        # unknown unit: leave as is (assume already tpd if sensible)
        tpd = val

    return tpd, {"system_capacity": capacity_raw, "availability": availability}


def scale_capex(
    base_capex: float, base_tpd: float, target_tpd: float, exponent: float = 0.6
) -> float:
    """Scale CAPEX by capacity using a cost curve exponent (default 0.6)."""
    if base_tpd <= 0 or target_tpd <= 0:
        return float(base_capex)
    return float(base_capex) * (target_tpd / max(base_tpd, 1.0)) ** float(exponent)


def _sum_known_civil_costs(props: Dict[str, Any]) -> float:
    """
    Sum obvious line items from Installation/Civil equipment nodes.
    You can expand this list as you ingest more components.
    """
    keys = [
        "site_prep",
        "transport_rigging",
        "buildings_walkways_fencing",
        "foundations",
        "civils",
        "electrical_install",
        "mechanical_install",
        "structural_steel",
        "contingency",
    ]
    total = 0.0
    for k in keys:
        total += _to_float(props.get(k, 0.0))
    return total


def _extract_project(nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for n in nodes:
        if "Project" in (n.get("labels") or []):
            return n
    return None


def _equipment_nodes_linked_to_project(
    graph: Dict[str, Any], project_node_id: str
) -> List[Dict[str, Any]]:
    nodes = graph.get("nodes", [])
    rels = graph.get("relationships", [])
    id2node = {n["id"]: n for n in nodes}
    linked = []
    for r in rels:
        if r.get("type") == "USES_EQUIPMENT" and r.get("start") == project_node_id:
            eq = id2node.get(r.get("end"))
            if eq and "Equipment" in (eq.get("labels") or []):
                linked.append(eq)
    return linked


# # # # # # # # # # # # # # # # # # # # # # # #

# COST ESTIMATION MAIN FUNCTIONS

# # # # # # # # # # # # # # # # # # # # # # # #


def find_related_tabular_entities_by_embedding(
    entity: Dict[str, Any],
    project_id: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Given a base_case entity id, find related tabular_data entities using embedding similarity.

    Args:
        entity_id: ID of the base_case entity (string).
        project_id: The project ID to filter tabular entities.
        top_k: Maximum number of related entities to return.

    Returns:
        Ranked list of related tabular_data entities.
    """

    # Flatten the entity properties into a string (excluding ids/dates)
    entity_props = entity.get("properties", {}) or {}
    props_text = ""
    if entity_props:
        logger.info(f"[EMBEDDING] entity_props: {entity_props['name']}")
        props_text = " ".join(
            f"{k}: {v}"
            for k, v in entity_props.items()
            if isinstance(v, (str, int, float))
            and not (
                "id" in k.lower()
                or "created" in k.lower()
                or "updated" in k.lower()
                or "date" in k.lower()
                or "time" in k.lower()
            )
        )
        entity_type = entity.get("type", "")
        props_text = f"{entity_type} {props_text}"
    else:
        # Fallback to name/type
        name = (
            (entity.get("properties", {}) or {}).get("name") or entity.get("name") or ""
        )
        entity_type = entity.get("type", "")
        props_text = f"{name} {entity_type}"

    try:
        # Get embedding for the entity text
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small", input=props_text
        )
        embedding = embedding_response.data[0].embedding
    except Exception as e:
        logger.error(f"[EMBEDDING] Failed to get embedding for entity {entity.get('id')}: {e}")
        return []

    try:
        # Search for tabular_data entities using the embedding
        results = search_entities_by_embedding(
            embedding=embedding,
            project_id=project_id,
            entity_types=["Material", "Equipment"],
            top_k=top_k,
            artifact_type="tabular_data",
        )
    except Exception as e:
        logger.error(f"[VECTOR_SEARCH] Failed to search for related entities: {e}")
        return []

    # Ensure returned items are tabular_data
    filtered = [
        e
        for e in results
        if (e.get("properties", {}) or {}).get("artifact_type") == "tabular_data"
    ]

    # Print names of entities found
    for e in filtered:
        name = (e.get("properties", {}) or {}).get("name") or e.get("name") or ""
        logger.info(
            f"[EMBEDDING] Found related tabular entity: {name} (ID: {e.get('id')})"
        )

    return filtered[:top_k]


def cost_estimation(
    scenario_description: str,
    project_id: str,
    scenario_id: str,
    goal: Optional[str] = None,
    change_type: Optional[str] = None,
    uncertainties: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    selected_entities: Optional[List[Dict[str, Any]]] = None,
):
    """
    Perform cost estimation based on scenario description and other parameters.

    Args:
        scenario_description: User's description of desired changes
        project_id: ID of the project
        scenario_id: ID of the scenario
        goal: Scenario goal (e.g., "increase capacity")
        change_type: Type of change (e.g., "Equipment", "Material", "Process")
        uncertainties: Uncertainty parameters
        user_id: ID of the user requesting the estimation
        selected_entities: Optional list of pre-selected entities to consider
    """
    if (
        not scenario_description
        or not project_id
        or not scenario_id
        or not selected_entities
    ):
        raise ValueError(
            "scenario_description, project_id, scenario_id, and selected_entities are required."
        )


    # Fetch the entity document from the entities collection
    base_entities = []

    # Retrieve tabular entities based on selected entities using embedding
    tabular_entities = []
    
    matched_entities = []

    # Keep track of ids we've already added so we only add unique tabular entities
    seen_tabular_ids = set()

    for entity_id in selected_entities:
        entity = db().entities.find_one({"id": entity_id}, {"_id": 0})
        if entity:
            matches = {"base_entity": entity, "tabular_entities": []}
            base_entities.append(entity)
            related = find_related_tabular_entities_by_embedding(
                entity, project_id, top_k=5
            )
            # only extend with unique entities (by id)
            for r in related:
                rid = r.get("id")
                if rid:
                    if rid not in seen_tabular_ids:
                        seen_tabular_ids.add(rid)
                        tabular_entities.append(r)
                        matches["tabular_entities"].append(r)
                else:
                    raise ValueError("Related entity missing 'id' field.")
            matched_entities.append(matches)
        else:
            raise ValueError(f"Selected entity with id {entity_id} not found.")

    # Build output JSON
    estimate_id = f"{uuid.uuid4()}"
    output = {
        "id": estimate_id,
        "estimate_id": estimate_id,
        "scenario_id": scenario_id,
        "project_id": project_id,
        "scenario_description": scenario_description,
        "status": "completed",
        "metadata": {
            "confidence": "medium",
            "cost_details": {
                "base_entities": base_entities,
                "tabular_entities": tabular_entities,
                "matched_entities": matched_entities,
            },
        },
    }

    return output
