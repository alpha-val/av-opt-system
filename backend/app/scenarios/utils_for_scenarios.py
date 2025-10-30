from typing import List, Dict, Any


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
            if all(item in dedup_entity["base_values"] for item in entity["base_values"]):
                # Merge properties into the entity with larger base_values
                dedup_entity["proposed_modifications"].extend(entity["proposed_modifications"])
                dedup_entity["expected_impacts"].update(entity["expected_impacts"])
                is_subset = True
                break
            elif all(item in entity["base_values"] for item in dedup_entity["base_values"]):
                # If dedup_entity's base_values is a subset, replace it with the current entity
                entity["proposed_modifications"].extend(dedup_entity["proposed_modifications"])
                entity["expected_impacts"].update(dedup_entity["expected_impacts"])
                deduplicated_entities.remove(dedup_entity)
                deduplicated_entities.append(entity)
                is_subset = True
                break

        if not is_subset:
            deduplicated_entities.append(entity)

    return deduplicated_entities