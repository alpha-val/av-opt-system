"""
Base repository with common database operations.

Provides reusable CRUD operations with error handling and logging.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from typing import Dict, Any, List, Optional, TypeVar, Generic
from fastapi import HTTPException
import logging

from ..models.base import BaseDBModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseDBModel)


class BaseRepository(Generic[T]):
    """
    Base repository providing common database operations.

    All specific repositories (ScenarioRepository, OptionRepository, etc.)
    inherit from this and add domain-specific methods.

    Usage:
        class ScenarioRepository(BaseRepository[Scenario]):
            def __init__(self, db: AsyncIOMotorDatabase):
                super().__init__(db, "scenarios")
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection_name = collection_name
        self.collection = db[collection_name]

    async def create(self, document: Dict[str, Any]) -> str:
        """
        Create a new document.

        Args:
            document: Document data

        Returns:
            str: ID of created document

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Remove _id if present (MongoDB will generate)
            document.pop("_id", None)

            result = await self.collection.insert_one(document)
            logger.info(
                f"Created {self.collection_name} document",
                extra={"document_id": str(result.inserted_id)},
            )
            return str(result.inserted_id)

        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error: {e}")
            raise HTTPException(status_code=409, detail="Document already exists")

        except PyMongoError as e:
            logger.error(f"Database error creating document: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def find_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Find document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            if not ObjectId.is_valid(document_id):
                return None

            document = await self.collection.find_one({"_id": ObjectId(document_id)})
            return document

        except PyMongoError as e:
            logger.error(f"Database error finding document: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find one document matching query.

        Args:
            query: MongoDB query

        Returns:
            Document data or None
        """
        try:
            document = await self.collection.find_one(query)
            return document

        except PyMongoError as e:
            logger.error(f"Database error finding document: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def find_many(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents.

        Args:
            query: MongoDB query
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples

        Returns:
            List of documents
        """
        try:
            cursor = self.collection.find(query)

            if sort:
                cursor = cursor.sort(sort)
            else:
                # Default: sort by creation date descending
                cursor = cursor.sort([("created_at", -1)])

            cursor = cursor.skip(skip).limit(limit)

            documents = await cursor.to_list(length=limit)
            return documents

        except PyMongoError as e:
            logger.error(f"Database error finding documents: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def count(self, query: Dict[str, Any]) -> int:
        """
        Count documents matching query.

        Args:
            query: MongoDB query

        Returns:
            Count of matching documents
        """
        try:
            count = await self.collection.count_documents(query)
            return count

        except PyMongoError as e:
            logger.error(f"Database error counting documents: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update(self, document_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update document by ID.

        Args:
            document_id: Document ID
            update_data: Fields to update

        Returns:
            True if updated, False if not found
        """
        try:
            if not ObjectId.is_valid(document_id):
                return False

            # Always update the updated_at timestamp
            from datetime import datetime

            update_data["updated_at"] = datetime.utcnow()

            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    f"Updated {self.collection_name} document",
                    extra={"document_id": document_id},
                )

            return result.matched_count > 0

        except PyMongoError as e:
            logger.error(f"Database error updating document: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete(self, document_id: str) -> bool:
        """
        Delete document by ID.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            if not ObjectId.is_valid(document_id):
                return False

            result = await self.collection.delete_one({"_id": ObjectId(document_id)})

            if result.deleted_count > 0:
                logger.info(
                    f"Deleted {self.collection_name} document",
                    extra={"document_id": document_id},
                )

            return result.deleted_count > 0

        except PyMongoError as e:
            logger.error(f"Database error deleting document: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run aggregation pipeline.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            Aggregation results
        """
        try:
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            return results

        except PyMongoError as e:
            logger.error(f"Database error in aggregation: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
