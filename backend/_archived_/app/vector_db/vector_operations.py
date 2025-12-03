from typing import List, Dict, Optional
import os
import openai
from app.config_adapter import SETTINGS
from app.text_clean import sanitize_metadata
from pinecone import Pinecone
from typing import List, Dict, Any
from datetime import datetime
from app.bronze_store import db
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Pinecone (do this once at startup)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "alphval-pro"))
index_name = os.getenv("PINECONE_INDEX_NAME", "alphaval-pro")
# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


def search_entities_by_embedding(
    embedding: list,
    project_id: str,
    entity_types: list,
    top_k: int = 20,
    cutoff: Optional[float] = 0.25,
    artifact_type: str = "base_case",
) -> list:
    """
    Search Pinecone for entities by embedding and entity types.
    Returns full entity data from MongoDB.
    """
    # Build filter for Pinecone
    pinecone_filter = {
        "project_id": {"$eq": project_id},
        "entity_type": {"$in": entity_types},
        "artifact_type": {"$eq": artifact_type},
    }

    # Query Pinecone
    results = index.query(
        vector=embedding,
        top_k=top_k,
        filter=pinecone_filter,
        namespace=project_id,
        include_metadata=True,
    )

    # Filter matches based on the cutoff score
    filtered_matches = [
        match for match in results.matches if match.score >= cutoff
    ]

    # Extract entity IDs from filtered matches
    entity_ids = [match.metadata["entity_id"] for match in filtered_matches]

    # Fetch full entities from MongoDB
    entities = (
        list(
            db().entities.find(
                {"id": {"$in": entity_ids}},
                {"_id": 0},
            )
        )
        if entity_ids
        else []
    )

    # Add relevance scores
    scores = {m.metadata["entity_id"]: m.score for m in filtered_matches}
    for entity in entities:
        entity["relevance_score"] = scores.get(entity["id"], 0.0)

    # Sort by relevance
    entities.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    return entities

def find_related_entities_by_embedding(
    entity: Dict[str, Any],
    artifact_type: str,
    project_id: str,
    top_k: int = 10,
    cutoff: Optional[float] = 0.25,
) -> List[Dict[str, Any]]:
    """
    Given an entity id, find related <artifact_type> entities using embedding similarity.

    Args:
        entity_id: ID of the base_case entity (string).
        artifact_type: The type of artifact to search for (e.g., "base_case" or "tabular_data").
        project_id: The project ID to filter tabular entities.
        top_k: Maximum number of related entities to return.

    Returns:
        Ranked list of related <artifact_type> entities.
    """

    # Normalize the entity for vector DB operations
    normalized_entity = normalize_entity_for_vector_db(
        entity, project_id, artifact_type=artifact_type
    )
    props_text = normalized_entity["text_content"]

    try:
        # Get embedding for the entity text
        embedding_response = openai.embeddings.create(
            model="text-embedding-3-small", input=props_text
        )
        embedding = embedding_response.data[0].embedding
    except Exception as e:
        logger.error(
            f"[EMBEDDING] Failed to get embedding for entity {entity.get('id')}: {e}"
        )
        return []

    try:
        # Search for tabular_data entities using the embedding
        results = search_entities_by_embedding(
            embedding=embedding,
            project_id=project_id,
            entity_types=["Material", "Equipment"],
            top_k=top_k,
            cutoff=cutoff,
            artifact_type=artifact_type,
        )
    except Exception as e:
        logger.error(f"[VECTOR_SEARCH] Failed to search for related entities: {e}")
        return []

    # # Ensure returned items are tabular_data
    filtered = [
        e
        for e in results
        if (e.get("properties", {}) or {}).get("artifact_type") == artifact_type
    ]

    return filtered[:top_k]


def retrieve_relevant_entities_for_scenario(
    scenario_description: str,
    project_id: str,
    equipment_types: List[str],
    capacity_range: Optional[tuple] = None,
) -> Dict[str, List[Dict]]:
    """
    Retrieve relevant entities using Pinecone vector search + filtering.
    Returns full entity data from MongoDB.
    """
    # Generate embedding
    query_embedding = (
        openai.embeddings.create(
            model="text-embedding-3-small", input=scenario_description
        )
        .data[0]
        .embedding
    )

    # Build filters
    base_filter = {
        "project_id": {"$eq": project_id},
        # "entity_type": {"$eq": "Equipment"},
        "status": {"$eq": "active"},
    }

    if equipment_types:
        base_filter["category"] = {"$in": equipment_types}

    if capacity_range:
        min_cap, max_cap = capacity_range
        base_filter["capacity"] = {"$gte": min_cap, "$lte": max_cap}

    # Query Pinecone for base case
    base_case_filter = {**base_filter, "artifact_type": {"$eq": "base_case"}}

    print("=" * 80)
    print("BASE CASE FILTER:")
    print(base_case_filter)
    print("=" * 80)

    base_case_results = index.query(
        vector=query_embedding,
        top_k=20,
        filter=base_case_filter,
        namespace=project_id,
        include_metadata=True,
    )

    print("=" * 80)
    print("BASE CASE RESULTS:")
    print(f"Number of matches: {len(base_case_results.matches)}")
    print("-" * 80)
    for i, match in enumerate(base_case_results.matches[:5], 1):
        print(f"Match {i}:")
        print(f"  ID: {match.id}")
        print(f"  Score: {match.score}")
        print(f"  Metadata: {match.metadata}")
        print("-" * 80)
    print("=" * 80)

    # Query Pinecone for tabular
    tabular_filter = {**base_filter, "artifact_type": {"$eq": "tabular_data"}}

    print("=" * 80)
    print("TABULAR FILTER:")
    print(tabular_filter)
    print("=" * 80)

    tabular_results = index.query(
        vector=query_embedding,
        top_k=20,
        filter=tabular_filter,
        namespace=project_id,
        include_metadata=True,
    )

    print("=" * 80)
    print("TABULAR RESULTS:")
    print(f"Number of matches: {len(tabular_results.matches)}")
    print("-" * 80)
    for i, match in enumerate(tabular_results.matches[:5], 1):  # Show first 5
        print(f"Match {i}:")
        print(f"  ID: {match.id}")
        print(f"  Score: {match.score}")
        print(f"  Entity Type: {match.metadata.get('entity_type')}")
        print(f"  Name: {match.metadata.get('name')}")
        print("-" * 80)
    print("=" * 80)

    # Extract entity IDs
    base_case_ids = [match.metadata["entity_id"] for match in base_case_results.matches]
    tabular_ids = [match.metadata["entity_id"] for match in tabular_results.matches]

    print("=" * 80)
    print("EXTRACTED ENTITY IDS:")
    print(f"Base case IDs ({len(base_case_ids)}): {base_case_ids[:5]}")  # Show first 5
    print(f"Tabular IDs ({len(tabular_ids)}): {tabular_ids[:5]}")  # Show first 5
    print("=" * 80)

    # Fetch full entities from MongoDB
    base_case_entities = (
        list(
            db().entities.find(
                {"id": {"$in": base_case_ids}},
                {"_id": 0},
            )
        )
        if base_case_ids
        else []
    )

    tabular_entities = (
        list(
            db().entities.find(
                {"id": {"$in": tabular_ids}},
                {"_id": 0},
            )
        )
        if tabular_ids
        else []
    )

    print("=" * 80)
    print("MONGODB RESULTS:")
    print(f"Base case entities found: {len(base_case_entities)}")
    print(f"Tabular entities found: {len(tabular_entities)}")
    if base_case_entities:
        print(f"Sample base case entity ID: {base_case_entities[0].get('id')}")
    if tabular_entities:
        print(f"Sample tabular entity ID: {tabular_entities[0].get('id')}")
    print("=" * 80)

    # Preserve relevance scores
    base_case_scores = {
        m.metadata["entity_id"]: m.score for m in base_case_results.matches
    }
    tabular_scores = {m.metadata["entity_id"]: m.score for m in tabular_results.matches}

    # Add scores to entities
    for entity in base_case_entities:
        entity["relevance_score"] = base_case_scores.get(entity["id"], 0.0)

    for entity in tabular_entities:
        entity["relevance_score"] = tabular_scores.get(entity["id"], 0.0)

    # Sort by relevance
    base_case_entities.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    tabular_entities.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    return {
        "base_case": base_case_entities,
        "tabular": tabular_entities,
    }


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI"""
    response = openai.embeddings.create(model="text-embedding-3-small", input=texts)
    return [item.embedding for item in response.data]


def build_text_for_embedding(entity: Dict[str, Any]) -> str:
    """
    Build text representation of entity for embedding.
    Dynamically flatten all properties and concatenate key fields.
    Excludes keys that are IDs (contain "_id") or "confidence".
    """
    parts = []

    # Core fields
    name = entity.get("name") or entity.get("id", "Unknown")
    parts.append(f"Name: {name}")

    entity_type = entity.get("type", "unknown")
    parts.append(f"Type: {entity_type}")

    # Flatten all properties dynamically
    props = entity.get("properties", {})
    for key, value in props.items():
        if value is not None and not key.lower().endswith("_id") and key != "confidence" and key != "status":
            # Format key-value pairs into "Key: Value" strings
            parts.append(f"{key.replace('_', ' ').capitalize()}: {value}")

    # Join all parts into a single text string
    text = ". ".join(parts)
    return text if text else name


def normalize_entity_for_vector_db(
    entity: Dict[str, Any], project_id: str, artifact_type: str
) -> Dict[str, Any]:
    """
    Normalize entity from MongoDB format to vector DB metadata format.
    Retains key attributes and flattens the rest from entity["properties"].
    Excludes any keys that are IDs (contain "_id") or "confidence".

    Args:
        entity: The raw entity data from MongoDB.
        project_id: The ID of the project the entity belongs to.
        artifact_type: The type of artifact (e.g., "base_case", "tabular_data").

    Returns:
        A dictionary containing normalized metadata for Pinecone.
    """
    props = entity.get("properties", {})

    # Retain key attributes
    metadata = {
        "entity_id": entity.get("id"),
        "project_id": project_id,
        "artifact_type": artifact_type,
        "entity_type": entity.get("type", "unknown"),
        "name": entity.get("name", entity.get("id", "Unknown")),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Flatten properties, excluding any IDs or "confidence"
    flattened_props = {
        k: v
        for k, v in props.items()
        if v is not None and not k.lower().endswith("_id") and k != "confidence" and k != "status"
    }

    # Merge flattened properties into metadata
    metadata.update(flattened_props)

    # Generate text content for embedding
    metadata["text_content"] = build_text_for_embedding(entity)

    return metadata


def upsert_entities_to_pinecone(
    entities: List[Dict[str, Any]], project_id: str, artifact_type: str = "base_case"
) -> int:
    """
    Generate embeddings for entities and upsert to Pinecone.
    Returns number of vectors upserted.
    """
    if not entities:
        return 0

    print(f"[INFO] Processing {len(entities)} entities for vector DB")

    # Normalize entities and build text content
    normalized_entities = []
    texts = []

    for entity in entities:
        try:
            normalized = normalize_entity_for_vector_db(
                entity, project_id, artifact_type
            )
            normalized_entities.append(normalized)
            texts.append(normalized["text_content"])
        except Exception as e:
            print(f"[ERROR] Failed to normalize entity {entity.get('id')}: {e}")
            continue

    if not normalized_entities:
        print("[WARN] No entities to upsert after normalization")
        return 0

    # Generate embeddings in batches (OpenAI has a limit)
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        try:
            batch_embeddings = generate_embeddings(batch_texts)
            all_embeddings.extend(batch_embeddings)
            # print(
            #     f"[INFO] Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}"
            # )
        except Exception as e:
            print(f"[ERROR] Failed to generate embeddings for batch {i}: {e}")
            # Fill with dummy embeddings to maintain alignment
            all_embeddings.extend([[0.0] * 1536] * len(batch_texts))

    # print(f"[INFO] Generated {len(all_embeddings)} embeddings")

    # Prepare vectors for Pinecone
    vectors = []
    for entity_meta, embedding in zip(normalized_entities, all_embeddings):
        sanitized_metadata = sanitize_metadata(entity_meta)
        vectors.append(
            {
                "id": entity_meta["entity_id"],
                "values": embedding,
                "metadata": sanitized_metadata,
            }
        )

    if not vectors:
        print("[WARN] No vectors to upsert")
        return 0

    # Upsert to Pinecone in batches
    batch_size = 100
    upserted_count = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        try:
            index.upsert(vectors=batch, namespace=project_id)
            upserted_count += len(batch)
            # print(
            #     f"[INFO] Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}"
            # )
        except Exception as e:
            print(f"[ERROR] Failed to upsert batch {i}: {e}")
            return 0

    print(f"[INFO] Successfully upserted {upserted_count}/{len(vectors)} vectors")

    return upserted_count
