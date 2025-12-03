"""
Vectorization and Pinecone storage operations.

Handles vectorization of text chunks and entities for similarity search in Pinecone.
"""

from typing import List, Dict, Any, Optional
import os
import openai
from datetime import datetime
from app_v2.adapters.config import SETTINGS
from app_v2.domain.parsing.utils.text_utils import sanitize_metadata
from pinecone import Pinecone
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

    def build_text_for_embedding(self, entity: Dict[str, Any]) -> str:
        """
        Build text representation of entity for embedding.

        Dynamically flattens all properties and concatenates key fields.

        Args:
            entity: Entity dictionary

        Returns:
            Text string suitable for embedding
        """
        parts = []

        # Core fields
        name = entity.get("name") or entity.get("id", "Unknown")
        parts.append(f"Name: {name}")

        entity_type = entity.get("type", "unknown")
        parts.append(f"Type: {entity_type}")

        # MSIO hierarchy fields (critical for ontology alignment)
        props = entity.get("properties", {})
        if "discipline" in props:
            parts.append(f"Discipline: {props['discipline']}")
        if "category" in props:
            parts.append(f"Category: {props['category']}")
        if "subcategory" in props:
            parts.append(f"Subcategory: {props['subcategory']}")
        if "entity" in props:
            parts.append(f"Entity: {props['entity']}")

        # Flatten all properties dynamically (exclude IDs and confidence)
        for key, value in props.items():
            if (
                value is not None
                and not key.lower().endswith("_id")
                and key != "confidence"
                and key != "status"
            ):
                # Format key-value pairs
                parts.append(f"{key.replace('_', ' ').capitalize()}: {value}")

        # Join all parts into a single text string
        text = ". ".join(parts)
        return text if text else name

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
            "name": entity.get("name", entity.get("id", "Unknown")),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Add MSIO hierarchy fields if present (for filtering)
        if "discipline" in props:
            metadata["discipline"] = props["discipline"]
        if "category" in props:
            metadata["category"] = props["category"]
        if "subcategory" in props:
            metadata["subcategory"] = props["subcategory"]
        if "entity" in props:
            metadata["entity"] = props["entity"]

        # Flatten properties, excluding IDs, confidence, and status
        flattened_props = {
            k: v
            for k, v in props.items()
            if v is not None
            and not k.lower().endswith("_id")
            and k not in ["confidence", "status"]
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
