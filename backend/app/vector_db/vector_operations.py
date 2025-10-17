from typing import List, Dict, Optional
import os
import openai
from app.config_adapter import SETTINGS
from pinecone import Pinecone
from typing import List, Dict, Any
from datetime import datetime
from app.bronze_store import db

# Initialize Pinecone (do this once at startup)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "av-opt-entities"))

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


def search_entities_by_embedding(
    embedding: list,
    project_id: str,
    entity_types: list,
    top_k: int = 20,
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

    # Extract entity IDs
    entity_ids = [match.metadata["entity_id"] for match in results.matches]

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
    scores = {m.metadata["entity_id"]: m.score for m in results.matches}
    for entity in entities:
        entity["relevance_score"] = scores.get(entity["id"], 0.0)

    # Sort by relevance
    entities.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    return entities


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
    Concatenate key fields that define the entity.
    """
    parts = []

    # Core fields
    name = entity.get("name") or entity.get("id", "Unknown")
    parts.append(f"Name: {name}")

    entity_type = entity.get("type", "unknown")
    parts.append(f"Type: {entity_type}")

    # Properties
    props = entity.get("properties", {})

    if props.get("category"):
        parts.append(f"Category: {props['category']}")

    if props.get("description"):
        parts.append(f"Description: {props['description']}")

    # Cost fields
    if props.get("capital_cost"):
        parts.append(f"Capital Cost: ${props['capital_cost']}")

    if props.get("installation_cost"):
        parts.append(f"Installation Cost: ${props['installation_cost']}")

    if props.get("operating_cost_annual"):
        parts.append(f"Operating Cost (Annual): ${props['operating_cost_annual']}")

    # Capacity fields
    if props.get("capacity"):
        unit = props.get("capacity_unit", "")
        parts.append(f"Capacity: {props['capacity']} {unit}".strip())

    if props.get("power_rating"):
        parts.append(f"Power Rating: {props['power_rating']} kW")

    # Location
    if props.get("location"):
        parts.append(f"Location: {props['location']}")

    if props.get("process_area"):
        parts.append(f"Process Area: {props['process_area']}")

    # Manufacturer/Model
    if props.get("manufacturer"):
        parts.append(f"Manufacturer: {props['manufacturer']}")

    if props.get("model"):
        parts.append(f"Model: {props['model']}")

    # Join all parts
    text = ". ".join(parts)
    return text if text else name


def normalize_entity_for_vector_db(
    entity: Dict[str, Any], project_id: str, artifact_type: str
) -> Dict[str, Any]:
    """
    Normalize entity from MongoDB format to vector DB metadata format.
    Maps field names and extracts filterable fields to root level.

    NOTE: Pinecone metadata only supports primitives (string, number, boolean, list of strings).
    Nested objects are NOT supported, so we don't include the full 'properties' dict.
    """
    props = entity.get("properties", {})

    # Build metadata with correct field names
    metadata = {
        # Map id -> entity_id
        "entity_id": entity.get("id"),
        # Core identifiers
        "project_id": project_id,
        "user_id": props.get("user_id"),
        "artifact_id": props.get("doc_id"),  # Map doc_id -> artifact_id
        "artifact_type": artifact_type,
        # Map type -> entity_type
        "entity_type": entity.get("type", "unknown"),
        # Name
        "name": entity.get("name", entity.get("id", "Unknown")),
        "status": "active",
        # Timestamps
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        # Extract filterable cost fields to root
        "capital_cost": props.get("capital_cost"),
        "installation_cost": props.get("installation_cost"),
        "operating_cost_annual": props.get("operating_cost_annual"),
        "currency": props.get("currency", "USD"),
        # Extract filterable capacity fields to root
        "capacity": props.get("capacity"),
        "capacity_unit": props.get("capacity_unit"),
        "power_rating": props.get("power_rating"),
        # Extract filterable location fields to root
        "location": props.get("location"),
        "process_area": props.get("process_area"),
        # Extract category to root
        "category": props.get("category"),
        # "properties": props,  # This causes the error!
        # Generate text content for embedding
        "text_content": build_text_for_embedding(entity),
        # === Additional commonly used fields (flatten important ones) ===
        "manufacturer": props.get("manufacturer"),
        "model": props.get("model"),
        "description": props.get("description"),
    }

    # Remove None values to save space
    metadata = {k: v for k, v in metadata.items() if v is not None}

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

    print(f"[INFO] Normalized {len(normalized_entities)} entities")
    print(f"[INFO] Generating embeddings for {len(texts)} texts...")

    # Generate embeddings in batches (OpenAI has a limit)
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        try:
            batch_embeddings = generate_embeddings(batch_texts)
            all_embeddings.extend(batch_embeddings)
            print(
                f"[INFO] Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}"
            )
        except Exception as e:
            print(f"[ERROR] Failed to generate embeddings for batch {i}: {e}")
            # Fill with dummy embeddings to maintain alignment
            all_embeddings.extend([[0.0] * 1536] * len(batch_texts))

    print(f"[INFO] Generated {len(all_embeddings)} embeddings")

    # Prepare vectors for Pinecone
    vectors = []
    for entity_meta, embedding in zip(normalized_entities, all_embeddings):
        vectors.append(
            {
                "id": entity_meta["entity_id"],
                "values": embedding,
                "metadata": entity_meta,
            }
        )

    if not vectors:
        print("[WARN] No vectors to upsert")
        return 0

    # Upsert to Pinecone in batches
    print(f"[INFO] Upserting {len(vectors)} vectors to Pinecone...")

    batch_size = 100
    upserted_count = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        try:
            index.upsert(vectors=batch, namespace=project_id)
            upserted_count += len(batch)
            print(
                f"[INFO] Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}"
            )
        except Exception as e:
            print(f"[ERROR] Failed to upsert batch {i}: {e}")

    print(f"[INFO] Successfully upserted {upserted_count}/{len(vectors)} vectors")

    return upserted_count
