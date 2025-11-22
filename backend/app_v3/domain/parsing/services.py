"""
Document processing pipeline service.

Orchestrates the complete ETL pipeline for base case and tabular data documents.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import uuid
import logging

from .extractors.text_extractor import TextExtractor
from .extractors.table_extractor import TableExtractor
from .extractors.entity_extractor import EntityExtractor
from .chunkers import (
    ChunkingStrategy,
    CharacterChunker,
    PageChunker,
    ByteChunker,
)
from .validators.msio_validator import MSIOValidator
from .normalizers.entity_normalizer import EntityNormalizer
from .storage.vector_store import ChunkVectorStore, EntityVectorStore
from .storage.document_store import DocumentStore

logger = logging.getLogger(__name__)

# Fixed namespace for chunk ID generation
CHUNK_NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")


class DocumentProcessingService:
    """
    Main service for processing documents through the ETL pipeline.

    Handles both base_case and tabular_data artifact types with appropriate
    processing flows for each.
    """

    def __init__(self):
        """Initialize service with all required components."""
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.entity_extractor = EntityExtractor()
        self.validator = MSIOValidator()
        self.normalizer = EntityNormalizer()
        self.chunk_vector_store = ChunkVectorStore()
        self.entity_vector_store = EntityVectorStore()
        self.document_store = DocumentStore()

    def process_base_case_document(
        self,
        pdf_bytes: bytes,
        filename: str,
        doc_id: str,
        project_id: str,
        user_id: str,
        chunking_strategy: str = "character",
        char_limit: int = 5000,
        pages: Optional[str] = None,
        validate_msio: bool = True,
        strict_validation: bool = False,
        store_in_pinecone: bool = False,
        objective_type: Optional[str] = None,
        objective_target: Optional[str] = None,
        objective_unit: Optional[str] = None,
        objective_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a base case document through the complete pipeline.

        Pipeline flow:
        1. Extract and clean text from PDF
        2. Chunk text (character/page/byte strategy)
        3. Extract entities and edges using LLM
        4. Validate entities against MSIO ontology
        5. Normalize and deduplicate entities
        6. Store chunks in MongoDB
        7. Optionally store chunks and entities in Pinecone (vectorized) if store_in_pinecone=True
        8. Store entities and edges in MongoDB

        Args:
            pdf_bytes: PDF file content
            filename: Original filename
            doc_id: Document identifier
            project_id: Project identifier
            user_id: User identifier
            chunking_strategy: "character", "page", or "byte" (default: "character")
            char_limit: Character limit for character-based chunking (default: 5000)
            pages: Optional page range filter (e.g., "1-5,10")
            validate_msio: Whether to validate entities against MSIO ontology
            strict_validation: If True, invalid entities are excluded (default: False)
            store_in_pinecone: Whether to store chunks and entities in Pinecone (default: False)

        Returns:
            Dictionary with processing results and statistics
        """
        logger.info(f"Processing base case document: {filename} (doc_id: {doc_id})")

        try:
            # Stage 1: Text extraction
            doc_id_actual, file_sha, pages_raw, pages_clean = (
                self.text_extractor.extract(pdf_bytes, filename, pages)
            )

            # Use provided doc_id if available, otherwise use generated one
            if doc_id:
                doc_id_actual = doc_id

            # Stage 2: Chunking
            chunk_metadata = {
                "artifact_type": "base_case",
                "project_id": project_id,
                "user_id": user_id,
                "doc_id": doc_id_actual,
            }

            if chunking_strategy == "character":
                full_text = self.text_extractor.extract_full_text(pages_clean)
                chunker = CharacterChunker(
                    doc_id_actual, CHUNK_NAMESPACE, char_limit=char_limit
                )
                chunks = chunker.chunk(full_text, chunk_metadata)
            elif chunking_strategy == "page":
                chunker = PageChunker(doc_id_actual, CHUNK_NAMESPACE)
                chunks = chunker.chunk(pages_clean, chunk_metadata)
            elif chunking_strategy == "byte":
                full_text = self.text_extractor.extract_full_text(pages_clean)
                chunker = ByteChunker(
                    doc_id_actual, CHUNK_NAMESPACE, byte_limit=char_limit
                )
                chunks = chunker.chunk(full_text.encode("utf-8"), chunk_metadata)
            else:
                raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")

            logger.info(
                f"Created {len(chunks)} chunks using {chunking_strategy} strategy"
            )

            # Stage 3: Entity extraction
            extraction_result = self.entity_extractor.extract(chunks)
            nodes = extraction_result.get("nodes", [])
            edges = extraction_result.get("edges", [])

            # Add source metadata to entities
            for node in nodes:
                node.setdefault("properties", {})
                node["properties"].update(chunk_metadata)

            for edge in edges:
                edge.setdefault("properties", {})
                edge["properties"].update(chunk_metadata)

            # Stage 4: Mining System Integration Ontology (MSIO) validation
            validation_warnings = []
            # if validate_msio:
            #     validation_result = self.validator.validate_batch(
            #         nodes, strict=strict_validation
            #     )
            #     nodes = validation_result["valid_entities"]
            #     validation_warnings = validation_result["warnings"]

            #     logger.info(
            #         f"Validated entities: {validation_result['stats']['valid']}/"
            #         f"{validation_result['stats']['total']} valid"
            #     )

            # # Create hierarchy edges
            # hierarchy_edges = self.entity_extractor.create_hierarchy_edges(nodes)
            # edges.extend(hierarchy_edges)

            # Stage 5: Normalization and deduplication
            # Store original IDs before normalization for edge remapping
            original_to_new = {}
            for node in nodes:
                original_id = node.get("id", "")
                # Normalize entity
                normalized = self.normalizer.normalize_entity(node.copy())
                new_id = normalized.get("id")
                original_to_new[original_id] = new_id

            # Normalize and deduplicate
            nodes = self.normalizer.normalize_and_deduplicate(nodes)

            # Remap edges after normalization (IDs may have changed)
            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                if source in original_to_new:
                    edge["source"] = original_to_new[source]
                if target in original_to_new:
                    edge["target"] = original_to_new[target]
                edge.get("properties", {}).setdefault("project_id", project_id)
                edge.get("properties", {}).setdefault("user_id", user_id)
                edge.get("properties", {}).setdefault("doc_id", doc_id_actual)
                edge.get("properties", {}).setdefault("artifact_type", "base_case")

            # Store chunks in MongoDB
            chunks_stored = self.document_store.bulk_upsert_chunks(chunks)

            # Store entities and edges in MongoDB
            entities_stored = self.document_store.bulk_upsert_entities(nodes)
            edges_stored = self.document_store.bulk_upsert_relations(edges)

            # Optionally vectorize and store chunks and entities in Pinecone
            chunks_vectorized = 0
            entities_vectorized = 0
            if store_in_pinecone:
                chunks_vectorized = self.chunk_vector_store.upsert_chunks(
                    chunks, project_id=project_id, artifact_type="base_case"
                )
                entities_vectorized = self.entity_vector_store.upsert_entities(
                    nodes, project_id=project_id, artifact_type="base_case"
                )
                logger.info(
                    f"Vectorized and stored {chunks_vectorized} chunks and {entities_vectorized} entities in Pinecone"
                )
            else:
                logger.info("Pinecone storage skipped (store_in_pinecone=False)")

            logger.info(
                f"Completed processing base case document: "
                f"{entities_stored} entities, {edges_stored} edges"
                + (
                    f", {chunks_vectorized} chunks vectorized, {entities_vectorized} entities vectorized"
                    if store_in_pinecone
                    else ""
                )
            )

            return {
                "doc_id": doc_id_actual,
                "filename": filename,
                "file_sha256": file_sha,
                "pages": len(pages_clean),
                "chunks_created": len(chunks),
                "chunks_stored": chunks_stored,
                "chunks_vectorized": chunks_vectorized,
                "entities_extracted": len(nodes),
                "entities_stored": entities_stored,
                "entities_vectorized": entities_vectorized,
                "edges_extracted": len(edges),
                "edges_stored": edges_stored,
                "validation_warnings": validation_warnings,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error processing base case document: {e}", exc_info=True)
            return {
                "doc_id": doc_id,
                "filename": filename,
                "status": "error",
                "error": str(e),
            }

    def process_tabular_data_document(
        self,
        pdf_bytes: bytes,
        filename: str,
        doc_id: str,
        project_id: str,
        user_id: str,
        pages: Optional[str] = None,
        max_rows_per_chunk: int = 50,
        validate_msio: bool = True,
        strict_validation: bool = False,
        store_in_pinecone: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a tabular data document through the complete pipeline.

        Pipeline flow:
        1. Extract and clean text from PDF
        2. Extract tables (lattice and stream)
        3. Create table chunks for LLM processing
        4. Extract entities from tables using LLM
        5. Validate entities against MSIO ontology
        6. Normalize and deduplicate entities
        7. Store entities in MongoDB
        8. Optionally store entities in Pinecone (vectorized) if store_in_pinecone=True
        9. Store table metadata in MongoDB

        Args:
            pdf_bytes: PDF file content
            filename: Original filename
            doc_id: Document identifier
            project_id: Project identifier
            user_id: User identifier
            pages: Optional page range filter (e.g., "1-5,10")
            max_rows_per_chunk: Maximum rows per table chunk (default: 50)
            validate_msio: Whether to validate entities against MSIO ontology
            strict_validation: If True, invalid entities are excluded (default: False)
            store_in_pinecone: Whether to store entities in Pinecone (default: False)

        Returns:
            Dictionary with processing results and statistics
        """
        logger.info(f"Processing tabular data document: {filename} (doc_id: {doc_id})")

        try:
            # Stage 1: Text extraction (for metadata and file hash)
            doc_id_actual, file_sha, pages_raw, pages_clean = (
                self.text_extractor.extract(pdf_bytes, filename, pages)
            )

            # Use provided doc_id if available
            if doc_id:
                doc_id_actual = doc_id

            # Stage 2: Table extraction
            tables = self.table_extractor.extract_tables(pdf_bytes, pages=pages)

            logger.info(f"Extracted {len(tables)} tables from PDF")

            if not tables:
                logger.warning(
                    "No tables found in PDF, falling back to text extraction"
                )
                # Fallback to text-based extraction if no tables found
                return self.process_base_case_document(
                    pdf_bytes=pdf_bytes,
                    filename=filename,
                    doc_id=doc_id_actual,
                    project_id=project_id,
                    user_id=user_id,
                    pages=pages,
                    validate_msio=validate_msio,
                    strict_validation=strict_validation,
                    chunking_strategy="byte",
                )

            # Stage 3: Create table chunks for LLM processing
            table_chunks = self.table_extractor.create_table_chunks(
                tables, doc_id_actual, max_rows_per_chunk=max_rows_per_chunk
            )

            # Add metadata to table chunks
            chunk_metadata = {
                "artifact_type": "tabular_data",
                "project_id": project_id,
                "user_id": user_id,
                "doc_id": doc_id_actual,
            }
            for chunk in table_chunks:
                chunk.setdefault("properties", {})
                chunk["properties"].update(chunk_metadata)

            logger.info(f"Created {len(table_chunks)} table chunks")

            # Stage 4: Entity extraction from tables
            extraction_result = self.entity_extractor.extract(artifact_type="tabular_data", chunks=table_chunks)
            nodes = extraction_result.get("nodes", [])
            edges = extraction_result.get("edges", [])

            # Add source metadata to entities and ensure node IDs are UUIDs
            # Create mapping of old IDs to new UUIDs for edge reference updates
            node_id_mapping = {}
            
            for node in nodes:
                # Ensure node has a unique UUID as ID
                old_id = node.get("id")
                if not old_id:
                    # Generate new UUID if node doesn't have an ID
                    new_id = str(uuid.uuid4())
                    node["id"] = new_id
                else:
                    # Check if existing ID is a valid UUID format
                    try:
                        # Validate UUID format
                        uuid.UUID(old_id)
                        new_id = old_id  # Keep existing UUID
                    except (ValueError, TypeError):
                        # Generate new UUID if existing ID is not valid UUID format
                        new_id = str(uuid.uuid4())
                        node["id"] = new_id
                        node_id_mapping[old_id] = new_id
                
                node.setdefault("properties", {})
                node["properties"].update(chunk_metadata)

            for edge in edges:
                # Update edge source and target to use new UUIDs if mapping exists
                if "source" in edge and edge["source"] in node_id_mapping:
                    edge["source"] = node_id_mapping[edge["source"]]
                if "target" in edge and edge["target"] in node_id_mapping:
                    edge["target"] = node_id_mapping[edge["target"]]
                
                # Ensure edge has a unique UUID as ID
                if "id" not in edge:
                    edge["id"] = str(uuid.uuid4())
                else:
                    # Validate edge ID is a valid UUID format
                    try:
                        uuid.UUID(edge["id"])
                    except (ValueError, TypeError):
                        # Generate new UUID if existing ID is not valid UUID format
                        edge["id"] = str(uuid.uuid4())
                
                edge.setdefault("properties", {})
                edge["properties"].update(chunk_metadata)

            # Stage 5: MSIO validation
            validation_warnings = []
            # if validate_msio:
            #     validation_result = self.validator.validate_batch(
            #         nodes, strict=strict_validation
            #     )
            #     nodes = validation_result["valid_entities"]
            #     validation_warnings = validation_result["warnings"]

            #     logger.info(
            #         f"Validated entities: {validation_result['stats']['valid']}/"
            #         f"{validation_result['stats']['total']} valid"
            #     )

            # # Create hierarchy edges
            # hierarchy_edges = self.entity_extractor.create_hierarchy_edges(nodes)
            # edges.extend(hierarchy_edges)

            # Stage 6: Normalization and deduplication
            # Store original IDs before normalization for edge remapping
            original_to_new = {}
            for node in nodes:
                original_id = node.get("id", "")
                # Normalize entity
                normalized = self.normalizer.normalize_entity(node.copy())
                new_id = normalized.get("id")
                original_to_new[original_id] = new_id

            # Normalize and deduplicate
            nodes = self.normalizer.normalize_and_deduplicate(nodes)

            # Remap edges after normalization
            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                if source in original_to_new:
                    edge["source"] = original_to_new[source]
                if target in original_to_new:
                    edge["target"] = original_to_new[target]

            # Stage 7: Storage
            # Store document metadata
            self.document_store.upsert_document(
                doc_id=doc_id_actual,
                filename=filename,
                file_sha256=file_sha,
                project_id=project_id,
                user_id=user_id,
                artifact_type="tabular_data",
                metadata={
                    "pages": len(pages_clean),
                    "tables_count": len(tables),
                },
            )

            # Store table metadata
            for table in tables:
                self.document_store.upsert_table(
                    doc_id=doc_id_actual,
                    table_id=table["table_id"],
                    metadata=table,
                    project_id=project_id,
                    user_id=user_id,
                )

            # Store entities and edges in MongoDB
            entities_stored = self.document_store.bulk_upsert_entities(nodes)
            edges_stored = self.document_store.bulk_upsert_relations(edges)

            # Optionally vectorize and store entities in Pinecone (NOT chunks for tabular data)
            entities_vectorized = 0
            if store_in_pinecone:
                entities_vectorized = self.entity_vector_store.upsert_entities(
                    nodes, project_id=project_id, artifact_type="tabular_data"
                )
                logger.info(
                    f"Vectorized and stored {entities_vectorized} entities in Pinecone"
                )
            else:
                logger.info("Pinecone storage skipped (store_in_pinecone=False)")

            logger.info(
                f"Completed processing tabular data document: "
                f"{entities_stored} entities, {edges_stored} edges"
                + (
                    f", {entities_vectorized} entities vectorized"
                    if store_in_pinecone
                    else ""
                )
            )

            return {
                "doc_id": doc_id_actual,
                "filename": filename,
                "file_sha256": file_sha,
                "pages": len(pages_clean),
                "tables_extracted": len(tables),
                "table_chunks_created": len(table_chunks),
                "entities_extracted": len(nodes),
                "entities_stored": entities_stored,
                "entities_vectorized": entities_vectorized,
                "edges_extracted": len(edges),
                "edges_stored": edges_stored,
                "validation_warnings": validation_warnings,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error processing tabular data document: {e}", exc_info=True)
            return {
                "doc_id": doc_id,
                "filename": filename,
                "status": "error",
                "error": str(e),
            }
