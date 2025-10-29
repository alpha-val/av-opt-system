from typing import List, Tuple, Dict, Any


# Given a list of scenarios, extract and sanitize relevant entities into a single list
def extract_scenario_entities(scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract and sanitize entities from a list of scenarios."""
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
    return all_entities