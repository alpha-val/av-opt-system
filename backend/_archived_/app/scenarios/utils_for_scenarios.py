from typing import List, Dict, Any
from app.vector_db.vector_operations import find_related_entities_by_embedding
from app.bronze_store import db


# Given a list of scenarios, extract and sanitize relevant entities into a single list
def extract_scenario_entities(scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract and sanitize entities from a list of scenarios, deduplicating based on base_values."""
    all_entities: List[Dict[str, Any]] = []

    for scenario in scenarios:
        entities = scenario.get("relevant_entities", [])
        for entity in entities:
            sanitized_entity = {
                "entity_name": entity.get("name", "N/A"),
                "entity_type": entity.get("entity_type", "N/A"),
                "base_values": entity.get("base_values", []),
                "proposed_modifications": entity.get("proposed_modifications", []),
                "expected_impacts": entity.get("expected_impacts", {}),
            }
            all_entities.append(sanitized_entity)

    # Deduplicate entities based on base_values
    deduplicated_entities = []
    for entity in all_entities:
        is_subset = False
        for dedup_entity in deduplicated_entities:
            # Check if entity's base_values is a subset of dedup_entity's base_values
            if all(
                item in dedup_entity["base_values"] for item in entity["base_values"]
            ):
                # Merge properties into the entity with larger base_values
                dedup_entity["proposed_modifications"].extend(
                    entity["proposed_modifications"]
                )
                dedup_entity["expected_impacts"].update(entity["expected_impacts"])
                is_subset = True
                break
            elif all(
                item in entity["base_values"] for item in dedup_entity["base_values"]
            ):
                # If dedup_entity's base_values is a subset, replace it with the current entity
                entity["proposed_modifications"].extend(
                    dedup_entity["proposed_modifications"]
                )
                entity["expected_impacts"].update(dedup_entity["expected_impacts"])
                deduplicated_entities.remove(dedup_entity)
                deduplicated_entities.append(entity)
                is_subset = True
                break

        if not is_subset:
            deduplicated_entities.append(entity)

    return deduplicated_entities


# Take a list of local objectives and convert them to entity format
def convert_local_objectives_to_entities(
    local_objectives: List[Dict[str, Any]], project_id: str, doc_id: str
) -> List[Dict[str, Any]]:
    """Convert local objectives into entity format suitable for ingestion."""
    entities: List[Dict[str, Any]] = []

    for obj in local_objectives:
        entity = {}
        entity.setdefault("properties", {})
        entity = {
            "id": obj.get("entity_id", "N/A"),
            "type": obj.get("entity_type", "N/A"),
            "properties": {
                "name": obj.get("name", "N/A"),
                "project_id": project_id,
                "doc_id": doc_id,
            },
        }
        # Convert base_values to top-level key-value pairs
        # Convert base_values to top-level key-value pairs
        base_values = obj.get("base_values", [])
        for bv in base_values:
            key = bv.get("key")
            value = bv.get("value")
            units = bv.get("units")
            if units:
                value = f"{value} {units}"
            if key and value:
                # Check for duplicate keys and add a suffix if necessary
                if key in entity["properties"]:
                    suffix = 1
                    while f"{key}_{suffix}" in entity["properties"]:
                        suffix += 1
                    key = f"{key}_{suffix}"
                entity["properties"][key] = value

        entities.append(entity)

    return entities


# For each entity in the list, find a base case entity using embeddings and add its ID to the entity
def link_entities_in_a_list(
    entities: List[Dict[str, Any]],
    project_id: str,
    artifact_type: str = "base_case",
) -> List[Dict[str, Any]]:
    """Link each entity to a related base case entity using embeddings."""
    linked_entities: List[Dict[str, Any]] = []

    for entity in entities:
        related_entities = find_related_entities_by_embedding(
            artifact_type=artifact_type,
            project_id=project_id,
            entity=entity,
            top_k=10,
        )
        if related_entities:
            # Check the relevance score of the base_case_entities; include those with score >= 0.5
            relevant_entities = [
                re for re in related_entities if re.get("relevance_score", 0) >= 0.5
            ]

            # Add IDs of all relevant entities to the entity
            entity["linked_entity_ids"] = [
                {"id": re.get("id", ""), "score": re.get("relevance_score", 0)}
                for re in relevant_entities
            ]
        else:
            entity["linked_entity_ids"] = []

        linked_entities.append(entity)

    return linked_entities


def retrieve_entities_by_ids(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retrieve entities from the database by their IDs."""
    # Extract all linked entity IDs from objects in the list {"id": ..., "score": ...}
    entity_ids = [
        link["id"]
        for entity in entities
        for link in entity.get("linked_entity_ids", [])
    ]

    # Remove duplicates
    entity_ids = list(set(entity_ids))

    # Fetch full entities from MongoDB
    base_case_entities = (
        list(
            db().entities.find(
                {"id": {"$in": entity_ids}},
                {"_id": 0},
            )
        )
        if entity_ids
        else []
    )

    # Update the base case entities with relevance scores from the list "entities"
    for base_entity in base_case_entities:
        for entity in entities:
            # Look for matching ID in linked_entity_ids
            for link in entity.get("linked_entity_ids", []):
                if link["id"] == base_entity["id"]:
                    base_entity["properties"]["relevance_score"] = link.get("score", 0)
                    break

    return base_case_entities
