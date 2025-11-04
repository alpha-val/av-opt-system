"""
MongoDB storage operations for document processing pipeline.

Handles storage of entities, edges, chunks, and document metadata in MongoDB.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pymongo import UpdateOne
from app.bronze_store import db
import uuid
import logging

logger = logging.getLogger(__name__)


class DocumentStore:
    """Storage operations for documents, chunks, entities, and relations."""
    
    def __init__(self):
        self._db = db()
    
    def upsert_document(
        self,
        doc_id: str,
        filename: str,
        file_sha256: str,
        project_id: str,
        user_id: str,
        artifact_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upsert document metadata to MongoDB.
        
        Args:
            doc_id: Document identifier
            filename: Original filename
            file_sha256: SHA256 hash of file content
            project_id: Project identifier
            user_id: User identifier
            artifact_type: Type of artifact (e.g., "base_case", "tabular_data")
            metadata: Additional metadata
            
        Returns:
            Stored document dictionary
        """
        document = {
            "_id": doc_id,
            "id": doc_id,
            "filename": filename,
            "sha256": file_sha256,
            "project_id": project_id,
            "user_id": user_id,
            "artifact_type": artifact_type,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if metadata:
            document.update(metadata)
        
        self._db.documents.replace_one({"_id": doc_id}, document, upsert=True)
        logger.info(f"Upserted document {doc_id} to MongoDB")
        
        return document
    
    def bulk_upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Bulk upsert chunks to MongoDB.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Number of chunks processed
        """
        if not chunks:
            return 0
        
        # Ensure each chunk has required fields
        for chunk in chunks:
            if "_id" not in chunk:
                if "id" in chunk:
                    chunk["_id"] = chunk["id"]
                elif "chunk_id" in chunk:
                    chunk["_id"] = chunk["chunk_id"]
                    chunk["id"] = chunk["chunk_id"]
                else:
                    chunk["_id"] = str(uuid.uuid4())
                    chunk["id"] = chunk["_id"]
            
            # Ensure id matches _id
            if "id" not in chunk:
                chunk["id"] = chunk["_id"]
            
            # Ensure timestamps
            if "created_at" not in chunk:
                chunk["created_at"] = datetime.now(timezone.utc)
            if "updated_at" not in chunk:
                chunk["updated_at"] = datetime.now(timezone.utc)
        
        # Prepare bulk operations
        ops = [
            UpdateOne(
                {"_id": chunk["_id"]},
                {"$set": chunk},
                upsert=True
            )
            for chunk in chunks
        ]
        
        if ops:
            result = self._db.chunks.bulk_write(ops, ordered=False)
            logger.info(
                f"Bulk upserted chunks - Matched: {result.matched_count}, "
                f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
            )
            return result.upserted_count + result.modified_count
        
        return 0
    
    def bulk_upsert_entities(self, entities: List[Dict[str, Any]]) -> int:
        """
        Bulk upsert entities to MongoDB.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Number of entities processed
        """
        if not entities:
            return 0
        
        # Ensure each entity has required fields
        for entity in entities:
            if "_id" not in entity:
                if "id" in entity:
                    entity["_id"] = entity["id"]
                else:
                    entity["_id"] = str(uuid.uuid4())
                    entity["id"] = entity["_id"]
            
            # Ensure id matches _id
            if "id" not in entity:
                entity["id"] = entity["_id"]
            
            # Ensure timestamps
            if "created_at" not in entity:
                entity["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in entity:
                entity["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Prepare bulk operations
        ops = [
            UpdateOne(
                {"_id": entity["_id"]},
                {"$set": entity},
                upsert=True
            )
            for entity in entities
        ]
        
        if ops:
            result = self._db.entities.bulk_write(ops, ordered=False)
            logger.info(
                f"Bulk upserted entities - Matched: {result.matched_count}, "
                f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
            )
            return result.upserted_count + result.modified_count
        
        return 0
    
    def bulk_upsert_relations(self, relations: List[Dict[str, Any]]) -> int:
        """
        Bulk upsert relations (edges) to MongoDB.
        
        Args:
            relations: List of relation/edge dictionaries
            
        Returns:
            Number of relations processed
        """
        if not relations:
            return 0
        
        # Ensure each relation has required fields
        for relation in relations:
            if "_id" not in relation:
                if "id" in relation:
                    relation["_id"] = relation["id"]
                else:
                    relation["_id"] = str(uuid.uuid4())
                    relation["id"] = relation["_id"]
            
            # Ensure id matches _id
            if "id" not in relation:
                relation["id"] = relation["_id"]
            
            # Ensure timestamps
            if "created_at" not in relation:
                relation["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in relation:
                relation["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Prepare bulk operations
        ops = [
            UpdateOne(
                {
                    "source": relation.get("source"),
                    "target": relation.get("target"),
                    "type": relation.get("type")
                },
                {"$set": relation},
                upsert=True
            )
            for relation in relations
        ]
        
        if ops:
            result = self._db.relations.bulk_write(ops, ordered=False)
            logger.info(
                f"Bulk upserted relations - Matched: {result.matched_count}, "
                f"Modified: {result.modified_count}, Upserted: {result.upserted_count}"
            )
            return result.upserted_count + result.modified_count
        
        return 0
    
    def upsert_table(
        self,
        doc_id: str,
        table_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upsert table metadata to MongoDB.
        
        Args:
            doc_id: Document identifier
            table_id: Table identifier
            metadata: Table metadata
            
        Returns:
            Stored table dictionary
        """
        table_doc = {
            "_id": table_id,
            "id": table_id,
            "doc_id": doc_id,
            "table_id": table_id,
            **metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self._db.tables.replace_one({"_id": table_id}, table_doc, upsert=True)
        logger.info(f"Upserted table {table_id} to MongoDB")
        
        return table_doc

