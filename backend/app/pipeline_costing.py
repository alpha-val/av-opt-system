# etl_bronze.py
from __future__ import annotations
import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from .bronze_store import db
from .costing import estimate_cost

# Create API router
router_costing = APIRouter()


def get_base_case_entities(
    project_id: str, entity_types: List[str]
) -> List[Dict[str, Any]]:
    D = db()
    query = {
        "type": {"$in": entity_types},
        "properties.project_id": project_id,
        "properties.artifact_type": "base_case",
    }
    return list(D.entities.find(query, {"_id": 0}))


def get_scenario_entities(
    project_id: str, scenario_id: str, cost_id: str, entity_types: List[str]
) -> List[Dict[str, Any]]:
    D = db()
    # You may want to filter by scenario/cost-specific tags or properties
    query = {
        "type": {"$in": entity_types},
        "properties.project_id": project_id,
        "properties.scenario_id": scenario_id,
        "properties.cost_id": cost_id,
    }
    return list(D.entities.find(query, {"_id": 0}))


def tag_documents_with_artifact(entity_ids: List[str], artifact: str):
    D = db()
    # Tag all documents related to these entities with the artifact
    D.documents.update_many(
        {"entity_id": {"$in": entity_ids}}, {"$set": {"artifact_type": artifact}}
    )


def calculate_cost_delta(
    base_entities: List[Dict[str, Any]], scenario_entities: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    # Match entities by a canonical key (e.g., name + type)
    def entity_key(e):
        return (e.get("type"), e["properties"].get("name"))

    base_map = {entity_key(e): e for e in base_entities}
    scenario_map = {entity_key(e): e for e in scenario_entities}
    results = []
    for key, base in base_map.items():
        scenario = scenario_map.get(key)
        if not scenario:
            continue  # Entity not present in scenario
        # Example: compare units/quantities/volumes and unit costs
        base_qty = float(base["properties"].get("quantity", 0))
        scenario_qty = float(scenario["properties"].get("quantity", 0))
        unit_cost = float(scenario["properties"].get("unit_cost", 0))
        delta_qty = scenario_qty - base_qty
        total_cost = scenario_qty * unit_cost
        results.append(
            {
                "entity": key,
                "base_qty": base_qty,
                "scenario_qty": scenario_qty,
                "delta_qty": delta_qty,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "uncertainty": scenario["properties"].get("uncertainty"),
                "range": scenario["properties"].get("range"),
            }
        )
    return results


@router_costing.post("/costing/test")
def test_costing_pipeline(project_id: str = Body(...)):
    """
    Test the costing pipeline with a given project_id.
    """
    D = db()
    return {"base_entity_count": "ok"}


@router_costing.post("/costing/run")
def run_costing_pipeline(
    project_id: str = Body(...),
    scenario_id: str = Body(...),
    cost_id: str = Body(...),
    scenario_description: str = Body(...),
    entity_types: List[str] = Body(["Equipment", "Material", "Process"]),
    uncertainties: Optional[Dict[str, Any]] = Body(None),
):
    """
    Run a scenario-based costing pipeline.
    """
    artifact = f"{scenario_id}:{cost_id}"
    D = db()

    # 1. Get base case entities
    base_entities = get_base_case_entities(project_id, entity_types)
    if not base_entities:
        raise HTTPException(404, detail="No base case entities found.")

    # 2. Get scenario entities (could be updated or new entities for this scenario)
    scenario_entities = get_scenario_entities(
        project_id, scenario_id, cost_id, entity_types
    )
    if not scenario_entities:
        raise HTTPException(404, detail="No scenario entities found.")

    # 3. Tag documents for scenario entities
    scenario_entity_ids = [e["id"] for e in scenario_entities]
    tag_documents_with_artifact(scenario_entity_ids, artifact)

    # 4. Calculate cost deltas
    cost_results = calculate_cost_delta(base_entities, scenario_entities)

    # 5. Apply uncertainties/ranges if provided
    if uncertainties:
        for result in cost_results:
            ent_key = result["entity"]
            if ent_key in uncertainties:
                result["uncertainty"] = uncertainties[ent_key].get("uncertainty")
                result["range"] = uncertainties[ent_key].get("range")

    # 6. Build total cost
    total_cost = sum(r["total_cost"] for r in cost_results)
    total_uncertainty = [
        r.get("uncertainty") for r in cost_results if r.get("uncertainty")
    ]

    # 7. Store scenario version metadata
    scenario_version = {
        "project_id": project_id,
        "scenario_id": scenario_id,
        "cost_id": cost_id,
        "artifact": artifact,
        "description": scenario_description,
        "created_at": datetime.datetime.utcnow(),
        "entity_types": entity_types,
        "cost_results": cost_results,
        "total_cost": total_cost,
        "uncertainties": total_uncertainty,
    }
    D.costing_versions.insert_one(scenario_version)

    return {
        "artifact": artifact,
        "description": scenario_description,
        "cost_results": cost_results,
        "total_cost": total_cost,
        "uncertainties": total_uncertainty,
        "version_id": str(scenario_version.get("_id")),
    }
