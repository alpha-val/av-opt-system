"""
Cost calculation utilities for cost estimates.

This module provides functions for:
- Finding related tabular entities using semantic search
- Extracting cost information from entities
- Building cost comparison reports
"""
from typing import Dict, Any, List, Optional
import logging

from ..parsing.storage.vector_store import (
    generate_embeddings,
    search_entities_by_embedding,
    EntityVectorStore,
)

logger = logging.getLogger(__name__)

# Initialize entity vector store for building text representations
_entity_vector_store = EntityVectorStore()


def find_related_tabular_entities(
    entity: Dict[str, Any],
    project_id: str,
    top_k: int = 10,
    cutoff: float = 0.25,
) -> List[Dict[str, Any]]:
    """
    Find related tabular_data entities for a base case entity using semantic search.

    Args:
        entity: Base case entity dictionary
        project_id: Project identifier
        top_k: Maximum number of related entities to return
        cutoff: Minimum similarity score threshold

    Returns:
        Ranked list of related tabular_data entities with relevance scores
    """
    try:
        # Build text representation for embedding
        text_for_embedding = ""
        # entity_name = entity.get("properties", {}).get("name") or "null"
        # entity_type = entity.get("type")
        # entity_discipline = entity.get("properties", {}).get("discipline") or "null"
        # entity_category = entity.get("properties", {}).get("category") or "null"
        # entity_subcategory = entity.get("properties", {}).get("subcategory") or "null"
        # entity_entity = entity.get("properties", {}).get("entity") or "null"
        # entity_attributes = entity.get("properties", {}).get("attributes") or []
        # attributes_to_include = ["name", "value", "unit"]
        # for attribute in entity_attributes:
        #     for attribute_property in attributes_to_include:
        #         text_for_embedding += f"{attribute_property}: {attribute.get(attribute_property)}\n"
        # text_for_embedding = f"Name: {entity_name}\nType: {entity_type}\nDiscipline: {entity_discipline}\nCategory: {entity_category}\nSubcategory: {entity_subcategory}\nEntity: {entity_entity}\nAttributes: {text_for_embedding}"
        
        text_for_embedding = _entity_vector_store.build_text_for_embedding(entity)
        
        logger.debug(
            f"Finding tabular entities for base entity {entity.get('id')}: "
            f"project_id={project_id}, top_k={top_k}, cutoff={cutoff}"
        )
        logger.debug(f"Entity text for embedding: {text_for_embedding[:200]}...")

        # REMOVE THIS LATER
        return []
        # Generate embedding
        embeddings = generate_embeddings([text_for_embedding])
        if not embeddings:
            logger.error(f"Failed to generate embedding for entity {entity.get('id')}")
            return []

        embedding = embeddings[0]
        logger.debug(f"Generated embedding vector of length {len(embedding)}")

        # Search for tabular_data entities using semantic search
        # Filter for Equipment and Material entity types
        results = search_entities_by_embedding(
            embedding=embedding,
            project_id=project_id,
            artifact_type="tabular_data",
            entity_types=["Equipment", "Material"],
            top_k=top_k,
            cutoff=cutoff,
        )

        # Ensure returned items are tabular_data (double-check)
        filtered = [
            e
            for e in results
            if (e.get("properties", {}) or {}).get("artifact_type") == "tabular_data"
        ]

        logger.info(
            f"Found {len(filtered)} tabular entities for base entity {entity.get('id')}"
        )

        return filtered[:top_k]

    except Exception as e:
        logger.error(
            f"Failed to find related tabular entities for entity {entity.get('id')}: {e}",
            exc_info=True,
        )
        return []


def extract_cost_info(entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract cost information from entity properties.

    Handles both old format (cost_information object) and new format (direct properties).

    Args:
        entity: Entity dictionary

    Returns:
        Dictionary with cost information:
        {
            "value": float or None,
            "currency": str or None,
            "unit": str or None,
            "basis": str or None,
            "type": str or None,  # CAPEX, OPEX, Total, Other
        }
    """
    props = entity.get("properties", {}) or {}
    
    # Try new format first (direct properties)
    cost_value = props.get("cost_value")
    cost_currency = props.get("cost_currency")
    cost_type = props.get("cost_type")
    cost_basis = props.get("cost_basis") or props.get("cost_basis_year")
    
    # If not found, try old format (cost_information object)
    if cost_value is None:
        cost_info = props.get("cost_information", {}) or {}
        cost_value = cost_info.get("cost_value")
        cost_currency = cost_info.get("cost_currency", "USD")
        cost_type = cost_info.get("cost_type")
        cost_basis = cost_info.get("cost_basis") or cost_info.get("cost_basis_year")
    
    # Handle cost_value if it's a string (convert to float)
    if isinstance(cost_value, str):
        try:
            # Remove currency symbols and commas
            cost_value = float(
                cost_value.replace(",", "").replace("$", "").replace("USD", "").strip()
            )
        except (ValueError, AttributeError):
            cost_value = None
    elif cost_value is not None:
        try:
            cost_value = float(cost_value)
        except (ValueError, TypeError):
            cost_value = None
    
    # Default currency to USD if not specified
    if cost_currency is None:
        cost_currency = "USD"
    
    return {
        "value": cost_value,
        "currency": cost_currency,
        "unit": props.get("cost_unit") or props.get("unit"),
        "basis": cost_basis,
        "type": cost_type,
    }


def build_cost_comparison_report(
    base_entities: List[Dict[str, Any]],
    matched_tabular_entities: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Build cost comparison report from base entities and their matched tabular entities.

    Args:
        base_entities: List of base case entities
        matched_tabular_entities: Dictionary mapping base entity ID to list of matched tabular entities

    Returns:
        List of cost comparison report entries, each containing:
        {
            "entity_id": str,
            "entity_name": str,
            "entity_type": str,
            "base_cost_info": Dict,
            "tabular_matches": List[Dict],  # Each with entity_id, entity_name, entity_type, cost_info, score
        }
    """
    cost_comparison_report = []

    for base_entity in base_entities:
        entity_id = base_entity.get("id")
        if not entity_id:
            logger.warning(f"Base entity missing 'id' field: {base_entity}")
            continue

        entity_name = base_entity.get("properties", {}).get("name", "Unknown")
        entity_type = base_entity.get("type", "Unknown")

        # Extract base case cost
        base_cost_info = extract_cost_info(base_entity)

        # Get matched tabular entities for this base entity
        tabular_matches = []
        matched_tabular = matched_tabular_entities.get(entity_id, [])

        for tabular_entity in matched_tabular:
            tabular_id = tabular_entity.get("id")
            if not tabular_id:
                logger.warning(f"Tabular entity missing 'id' field: {tabular_entity}")
                continue

            tabular_name = tabular_entity.get("properties", {}).get("name", "Unknown")
            tabular_type = tabular_entity.get("type", "Unknown")
            tabular_cost_info = extract_cost_info(tabular_entity)
            relevance_score = tabular_entity.get("relevance_score", 0.0)

            tabular_matches.append({
                "entity_id": tabular_id,
                "entity_name": tabular_name,
                "entity_type": tabular_type,
                "cost_info": tabular_cost_info,
                "score": relevance_score,
            })

        # Add row to cost comparison report
        cost_comparison_report.append({
            "entity_id": entity_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "base_cost_info": base_cost_info,
            "tabular_matches": tabular_matches,
        })

    return cost_comparison_report

