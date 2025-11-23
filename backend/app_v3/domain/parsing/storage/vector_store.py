"""
Vectorization and Pinecone storage operations.

Handles vectorization of text chunks and entities for similarity search in Pinecone.
"""

from typing import List, Dict, Any, Optional
import os
import openai
from datetime import datetime
from app_v3.adapters.config import SETTINGS
from app_v3.domain.parsing.utils.text_utils import sanitize_metadata
from pinecone import Pinecone
from app_v3.adapters.mongo.client import db
import logging

logger = logging.getLogger(__name__)

# Initialize Pinecone client (singleton)
_pc: Optional[Pinecone] = None
_index: Optional[Any] = None


def _get_pinecone_index():
    """Get or initialize Pinecone index."""
    global _pc, _index
    if _index is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")

        index_name = os.getenv("PINECONE_INDEX_NAME", "alphaval-pro")
        _pc = Pinecone(api_key=api_key)
        _index = _pc.Index(index_name)

    return _index


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using OpenAI text-embedding-3-small model.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (1536 dimensions each)
    """
    try:
        response = openai.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


class VectorStore:
    """Base class for vector storage operations."""

    def __init__(self):
        self.index = _get_pinecone_index()

    def upsert_vectors(
        self, vectors: List[Dict[str, Any]], namespace: str, batch_size: int = 100
    ) -> int:
        """
        Upsert vectors to Pinecone in batches.

        Args:
            vectors: List of vector dicts with 'id', 'values', 'metadata'
            namespace: Pinecone namespace (typically project_id)
            batch_size: Number of vectors per batch

        Returns:
            Number of vectors successfully upserted
        """
        if not vectors:
            return 0

        upserted_count = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                self.index.upsert(vectors=batch, namespace=namespace)
                upserted_count += len(batch)
                logger.debug(
                    f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}"
                )
            except Exception as e:
                logger.error(f"Failed to upsert batch {i}: {e}")
                raise

        logger.info(
            f"Successfully upserted {upserted_count}/{len(vectors)} vectors to Pinecone"
        )
        return upserted_count


class ChunkVectorStore(VectorStore):
    """
    Vector store for text chunks (used for base_case documents).

    Vectorizes text chunks for semantic similarity search.
    """

    def normalize_chunk_for_vector_db(
        self, chunk: Dict[str, Any], project_id: str, artifact_type: str
    ) -> Dict[str, Any]:
        """
        Normalize chunk for vector database.

        Args:
            chunk: Chunk dictionary with text and metadata
            project_id: Project identifier
            artifact_type: Type of artifact (e.g., "base_case")

        Returns:
            Normalized metadata dictionary with text_content for embedding
        """
        chunk_id = chunk.get("id") or chunk.get("chunk_id")
        text = chunk.get("text", "")

        metadata = {
            "chunk_id": chunk_id,
            "project_id": project_id,
            "artifact_type": artifact_type,
            "doc_id": chunk.get("doc_id"),
            "seq": chunk.get("seq"),
            "page": chunk.get("page"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "text_content": text,  # Used for embedding generation
        }

        # Add any additional properties
        if "properties" in chunk:
            flattened_props = {
                k: v
                for k, v in chunk["properties"].items()
                if v is not None and not k.lower().endswith("_id") and k != "confidence"
            }
            metadata.update(flattened_props)

        return metadata

    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        project_id: str,
        artifact_type: str = "base_case",
    ) -> int:
        """
        Vectorize and upsert text chunks to Pinecone.

        Args:
            chunks: List of chunk dictionaries
            project_id: Project identifier (used as Pinecone namespace)
            artifact_type: Type of artifact (default: "base_case")

        Returns:
            Number of chunks successfully upserted
        """
        if not chunks:
            logger.warning("No chunks provided for vectorization")
            return 0

        logger.info(f"Processing {len(chunks)} chunks for vector DB")

        # Normalize chunks and extract text
        normalized_chunks = []
        texts = []

        for chunk in chunks:
            try:
                normalized = self.normalize_chunk_for_vector_db(
                    chunk, project_id, artifact_type
                )
                normalized_chunks.append(normalized)
                texts.append(normalized["text_content"])
            except Exception as e:
                logger.error(f"Failed to normalize chunk {chunk.get('id')}: {e}")
                continue

        if not normalized_chunks:
            logger.warning("No chunks to upsert after normalization")
            return 0

        # Generate embeddings in batches
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            try:
                batch_embeddings = generate_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")
                raise

        # Prepare vectors for Pinecone
        vectors = []
        for chunk_meta, embedding in zip(normalized_chunks, all_embeddings):
            sanitized_metadata = sanitize_metadata(chunk_meta)
            vectors.append(
                {
                    "id": chunk_meta["chunk_id"],
                    "values": embedding,
                    "metadata": sanitized_metadata,
                }
            )

        # Upsert to Pinecone
        return self.upsert_vectors(vectors, namespace=project_id)


class EntityVectorStore(VectorStore):
    """
    Vector store for entities (used for both base_case and tabular_data).

    Vectorizes entity documents for entity similarity search.
    """

    def build_text_for_embedding(self, entity: Dict[str, Any], revised_values: Optional[List[Dict[str, Any]]] = []) -> str:
        """
        Build text representation of entity for embedding.

        Dynamically flattens all properties and concatenates key fields.
        Avoids duplication by tracking which MSIO fields were already added.

        Args:
            entity: Entity dictionary
            revised_values: List of revised attribute values. Each item contains:
                [
                    {"attr_name": str, "revised_val": number | string | null},
                    ...
                ]
                
        Returns:
            Text string suitable for embedding
        """
        parts = []

        # Core fields
        name = entity.get("properties", {}).get("name", "Unknown")
        parts.append(f"name: {name}")

        entity_type = entity.get("type", "unknown")
        parts.append(f"type: {entity_type}")

        # MSIO hierarchy fields (critical for ontology alignment)
        props = entity.get("properties", {})
        msio_fields_added = set()

        if "discipline" in props:
            parts.append(f"discipline: {props['discipline']}")
            msio_fields_added.add("discipline")
        if "category" in props:
            parts.append(f"category: {props['category']}")
            msio_fields_added.add("category")
        if "subcategory" in props:
            parts.append(f"subcategory: {props['subcategory']}")
            msio_fields_added.add("subcategory")
        if "entity" in props:
            parts.append(f"entity: {props['entity']}")
            msio_fields_added.add("entity")

        # Handle attributes specially - expand into readable text
        attr_texts = []
        
        if revised_values:
            for revised_value in revised_values:
                attr_name = revised_value.get("attr_name", "Unknown")
                attr_value = revised_value.get("revised_val")
                attr_unit = revised_value.get("unit", "")
                if attr_value is not None:
                    attr_text = f"{attr_name}: {attr_value}"
                    if attr_unit:
                        attr_text += f" {attr_unit}"
                    attr_texts.append(attr_text)
        
        if not revised_values:
            if "attributes" in props and isinstance(props["attributes"], list):
                msio_fields_added.add("attributes")  # Skip in the loop below
                attr_texts = []
                for attr in props["attributes"]:
                    if isinstance(attr, dict):
                        attr_name = attr.get("name", "Unknown")
                        attr_value = attr.get("value")
                        attr_unit = attr.get("unit", "")

                        # Build readable attribute text
                        if attr_value is not None:
                            attr_text = f"{attr_name}: {attr_value}"
                            if attr_unit:
                                attr_text += f" {attr_unit}"
                            attr_texts.append(attr_text)
        
        # Append attributes to parts if any were collected
        if attr_texts:
            parts.append(f"attributes: {', '.join(attr_texts)}")

        if "cost_information" in props and isinstance(props["cost_information"], dict):
            cost_information_texts = []
            for key, value in props["cost_information"].items():
                if value is not None:
                    cost_information_text = f"{key}: {value}"
                    cost_information_texts.append(cost_information_text)
            parts.append(f"cost_information: {', '.join(cost_information_texts)}")

        # Flatten all properties dynamically (exclude IDs, confidence, status, and already-added MSIO fields)
        # for key, value in props.items():
        #     if (
        #         value is not None
        #         and not key.lower().endswith("_id")
        #         and key != "confidence"
        #         and key != "status"
        #         and key not in msio_fields_added  # Skip MSIO fields already added above
        #     ):
        #         # Format key-value pairs
        #         parts.append(f"{key}: {value}")

        # Join all parts into a single text string
        text = ". ".join(parts)
        return text if text else "Unknown"

    def normalize_entity_for_vector_db(
        self, entity: Dict[str, Any], project_id: str, artifact_type: str
    ) -> Dict[str, Any]:
        """
        Normalize entity for vector database.

        Args:
            entity: Entity dictionary
            project_id: Project identifier
            artifact_type: Type of artifact (e.g., "base_case", "tabular_data")

        Returns:
            Normalized metadata dictionary with text_content for embedding
        """
        props = entity.get("properties", {})

        # Retain key attributes
        metadata = {
            "entity_id": entity.get("id"),
            "project_id": project_id,
            "artifact_type": artifact_type,
            "entity_type": entity.get("type", "unknown"),
            "name": props.get("name", "Unknown"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Add scenario_id if present (critical for filtering by scenario)
        # scenario_id is in props but gets excluded by the _id filter, so add it explicitly
        if "scenario_id" in props:
            metadata["scenario_id"] = props["scenario_id"]

        # Add MSIO hierarchy fields if present (for filtering)
        if "discipline" in props:
            metadata["discipline"] = props["discipline"]
        if "category" in props:
            metadata["category"] = props["category"]
        if "subcategory" in props:
            metadata["subcategory"] = props["subcategory"]
        if "entity" in props:
            metadata["entity"] = props["entity"]

        # Flatten properties, excluding IDs, confidence, status, and attributes
        # Attributes are handled specially in text_content, not as metadata
        # Note: scenario_id is already added above, so exclude it from flattening
        flattened_props = {
            k: v
            for k, v in props.items()
            if v is not None
            and not k.lower().endswith("_id")
            and k
            not in [
                "confidence",
                "status",
                "attributes",
                "scenario_id",
            ]  # Exclude attributes and scenario_id from metadata flattening
            and k
            not in [
                "discipline",
                "category",
                "subcategory",
                "entity",
            ]  # Already added above
        }

        # Merge flattened properties into metadata
        metadata.update(flattened_props)

        # Generate text content for embedding
        metadata["text_content"] = self.build_text_for_embedding(entity)

        return metadata

    def upsert_entities(
        self,
        entities: List[Dict[str, Any]],
        project_id: str,
        artifact_type: str = "base_case",
    ) -> int:
        """
        Vectorize and upsert entities to Pinecone.

        Args:
            entities: List of entity dictionaries
            project_id: Project identifier (used as Pinecone namespace)
            artifact_type: Type of artifact (e.g., "base_case", "tabular_data")

        Returns:
            Number of entities successfully upserted
        """
        if not entities:
            logger.warning("No entities provided for vectorization")
            return 0

        logger.info(f"Processing {len(entities)} entities for vector DB")

        # Normalize entities and build text content
        normalized_entities = []
        texts = []

        for entity in entities:
            try:
                normalized = self.normalize_entity_for_vector_db(
                    entity, project_id, artifact_type
                )
                normalized_entities.append(normalized)
                texts.append(normalized["text_content"])
            except Exception as e:
                logger.error(f"Failed to normalize entity {entity.get('id')}: {e}")
                continue

        if not normalized_entities:
            logger.warning("No entities to upsert after normalization")
            return 0

        # Generate embeddings in batches
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            try:
                batch_embeddings = generate_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")
                raise

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

        # Upsert to Pinecone
        return self.upsert_vectors(vectors, namespace=project_id)


def search_entities_by_embedding(
    embedding: List[float],
    project_id: str,
    scenario_id: Optional[str] = None,
    artifact_type: str = "base_case",
    entity_types: Optional[List[str]] = None,
    top_k: int = 5,
    cutoff: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Search Pinecone for entities by embedding similarity.
    Returns full entity data from MongoDB with relevance scores.

    Args:
        embedding: Query embedding vector (list of floats)
        project_id: Project identifier (used as Pinecone namespace)
        scenario_id: Optional scenario identifier for filtering
        artifact_type: Type of artifact (default: "base_case")
        entity_types: Optional list of entity types to filter (e.g., ["Equipment", "Material"])
        top_k: Maximum number of results to return (default: 5)
        cutoff: Minimum similarity score threshold (default: 0.7)

    Returns:
        List of entity dictionaries from MongoDB with relevance_score added
    """
    try:
        index = _get_pinecone_index()

        # Build filter for Pinecone
        pinecone_filter = {
            "project_id": {"$eq": project_id},
            "artifact_type": {"$eq": artifact_type},
        }

        # # Add scenario_id filter if provided AND artifact_type is not base_case
        # # Base case entities don't have scenario_id because they're shared across scenarios
        # if scenario_id and artifact_type != "base_case":
        #     pinecone_filter["scenario_id"] = {"$eq": scenario_id}

        # Add entity_type filter if provided
        if entity_types:
            pinecone_filter["entity_type"] = {"$in": entity_types}

        # Query Pinecone
        logger.debug(
            f"Querying Pinecone with filter: {pinecone_filter}, "
            f"namespace: {project_id}, top_k: {top_k}"
        )

        results = index.query(
            vector=embedding,
            top_k=top_k,
            filter=pinecone_filter,
            namespace=project_id,
            include_metadata=True,
        )

        # Log raw results before cutoff filtering
        logger.debug(
            f"Pinecone returned {len(results.matches)} raw matches "
            f"(before cutoff {cutoff} filtering)"
        )

        if results.matches:
            raw_scores = [f"{m.id}: {m.score:.3f}" for m in results.matches[:5]]
            logger.debug(f"Raw match scores (top 5): {', '.join(raw_scores)}")

            # Log metadata from first match to check structure
            first_match = results.matches[0]
            logger.debug(
                f"First match metadata keys: {list(first_match.metadata.keys()) if first_match.metadata else 'None'}"
            )
            if first_match.metadata:
                logger.debug(
                    f"First match metadata sample: "
                    f"project_id={first_match.metadata.get('project_id')}, "
                    f"artifact_type={first_match.metadata.get('artifact_type')}, "
                    f"scenario_id={first_match.metadata.get('scenario_id')}"
                )

        # Filter matches based on the cutoff score
        filtered_matches = [match for match in results.matches if match.score >= cutoff]

        if not filtered_matches:
            if results.matches:
                # Log that we had matches but they were below cutoff
                max_score = (
                    max(m.score for m in results.matches) if results.matches else 0
                )
                logger.info(
                    f"No entities found above cutoff {cutoff} for project {project_id}, "
                    f"artifact_type {artifact_type}. "
                    f"Max score was {max_score:.3f} (below cutoff)"
                )
            else:
                # No matches at all from Pinecone
                logger.info(
                    f"No entities found in Pinecone for project {project_id}, "
                    f"artifact_type {artifact_type}, filter: {pinecone_filter}"
                )
            return []

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

        logger.info(
            f"Semantic search found {len(entities)} entities above cutoff {cutoff} "
            f"for project {project_id}, artifact_type {artifact_type}"
        )

        return entities

    except Exception as e:
        logger.error(
            f"Error in semantic search for entities: {e}",
            exc_info=True,
        )
        return []


def delete_vectors_by_namespace(project_id: str) -> int:
    """
    Delete all vectors in a Pinecone namespace (project_id).

    Args:
        project_id: Project identifier (used as Pinecone namespace)

    Returns:
        Number of vectors deleted (0 if deletion failed or namespace doesn't exist)
    """
    try:
        index = _get_pinecone_index()

        # Get index stats to check if namespace exists and get vector count
        try:
            index_stats = index.describe_index_stats()
            namespaces = index_stats.get("namespaces", {})

            if project_id not in namespaces:
                logger.info(
                    f"Namespace '{project_id}' does not exist in Pinecone. "
                    f"No vectors to delete."
                )
                return 0

            # Get vector count before deletion
            vector_count = namespaces[project_id].get("vector_count", 0)

            if vector_count == 0:
                logger.info(
                    f"Namespace '{project_id}' exists but has no vectors. "
                    f"No deletion needed."
                )
                return 0

            # Delete all vectors in the namespace
            index.delete(delete_all=True, namespace=project_id)

            logger.info(
                f"Successfully deleted {vector_count} vectors from Pinecone "
                f"namespace '{project_id}'"
            )

            return vector_count

        except Exception as stats_error:
            logger.warning(
                f"Failed to get index stats for namespace '{project_id}': {stats_error}. "
                f"Attempting deletion anyway."
            )
            # Try deletion anyway
            index.delete(delete_all=True, namespace=project_id)
            logger.info(
                f"Deleted vectors from Pinecone namespace '{project_id}' "
                f"(count unknown due to stats error)"
            )
            return -1  # Indicates deletion attempted but count unknown

    except Exception as e:
        logger.error(
            f"Error deleting vectors from Pinecone namespace '{project_id}': {e}",
            exc_info=True,
        )
        return 0


def delete_vectors_by_filter(project_id: str, filter_dict: Dict[str, Any]) -> int:
    """
    Delete vectors from Pinecone by metadata filter.

    Args:
        project_id: Project identifier (used as Pinecone namespace)
        filter_dict: Pinecone metadata filter (e.g., {"scenario_id": {"$eq": "scenario_123"}})

    Returns:
        Number of vectors deleted (0 if deletion failed or no vectors matched)
    """
    try:
        index = _get_pinecone_index()

        # Get index stats to check if namespace exists
        try:
            index_stats = index.describe_index_stats()
            namespaces = index_stats.get("namespaces", {})

            if project_id not in namespaces:
                logger.info(
                    f"Namespace '{project_id}' does not exist in Pinecone. "
                    f"No vectors to delete."
                )
                return 0
        except Exception as stats_error:
            logger.warning(
                f"Failed to get index stats for namespace '{project_id}': {stats_error}. "
                f"Attempting deletion anyway."
            )

        # Delete vectors matching the filter
        index.delete(filter=filter_dict, namespace=project_id)

        logger.info(
            f"Deleted vectors from Pinecone namespace '{project_id}' "
            f"matching filter: {filter_dict}"
        )

        # Note: Pinecone delete() doesn't return count, so we return -1 to indicate success
        # but unknown count
        return -1

    except Exception as e:
        logger.error(
            f"Error deleting vectors from Pinecone namespace '{project_id}' "
            f"with filter {filter_dict}: {e}",
            exc_info=True,
        )
        return 0
