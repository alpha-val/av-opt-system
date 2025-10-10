"""
Database connection and management.

This module provides a singleton database connection and helper functions
for database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    Singleton database connection manager.

    Usage:
        db = await Database.get_database()
        collection = db.scenarios
        result = await collection.find_one({"_id": scenario_id})
    """

    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB.

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        try:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,
                minPoolSize=10,
            )

            # Test connection
            await cls._client.admin.command("ping")

            cls._database = cls._client[settings.MONGODB_DB_NAME]

            logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")

            # Create indexes
            await cls._create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            logger.info("✅ MongoDB connection closed")

    @classmethod
    async def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.

        Returns:
            AsyncIOMotorDatabase instance

        Raises:
            RuntimeError: If database not initialized
        """
        if cls._database is None:
            raise RuntimeError(
                "Database not initialized. Call Database.connect() first."
            )
        return cls._database

    @classmethod
    async def _create_indexes(cls) -> None:
        """
        Create database indexes for performance.

        Indexes are critical for query performance. We create indexes on:
        - Foreign key relationships (project_id, scenario_id)
        - Frequently queried fields (status, entity_type)
        - Sort fields (created_at, updated_at)
        """
        if cls._database is None:
            return

        logger.info("Creating database indexes...")

        # Scenarios indexes
        await cls._database.scenarios.create_index(
            [("project_id", 1), ("created_at", -1)]
        )
        await cls._database.scenarios.create_index([("status", 1)])
        await cls._database.scenarios.create_index([("goal.parameter", 1)])

        # Options indexes
        await cls._database.options.create_index(
            [("scenario_id", 1), ("created_at", -1)]
        )
        await cls._database.options.create_index([("project_id", 1)])
        await cls._database.options.create_index([("model", 1)])
        await cls._database.options.create_index([("selected", 1)])

        # Entities indexes
        await cls._database.entities.create_index(
            [("project_id", 1), ("entity_type", 1)]
        )
        await cls._database.entities.create_index([("entity_type", 1)])
        await cls._database.entities.create_index([("specifications.capacity", 1)])

        # Tables indexes
        await cls._database.tables.create_index([("project_id", 1), ("table_type", 1)])
        await cls._database.tables.create_index([("table_type", 1)])
        await cls._database.tables.create_index([("metadata.equipment_type", 1)])

        logger.info("✅ Database indexes created")


# Dependency for FastAPI routes
async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get database instance.

    Usage in routes:
        @router.get("/scenarios")
        async def list_scenarios(db: AsyncIOMotorDatabase = Depends(get_db)):
            scenarios = await db.scenarios.find().to_list(100)
            return scenarios
    """
    return await Database.get_database()
