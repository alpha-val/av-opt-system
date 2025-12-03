from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid


class VectorMetadata(BaseModel):
    """
    Optimized for Pinecone filtering + cost estimation.
    Only flatten fields you'll filter on frequently.
    """

    # === ALWAYS FILTER ON THESE ===
    entity_id: str
    project_id: str
    user_id: str
    artifact_id: str
    artifact_type: str  # "base_case" | "tabular_data"
    entity_type: str  # "equipment" | "process" | "material" | "scenario" | "process" etc.

    # === FREQUENTLY FILTERED ===
    category: Optional[str] = None  # "crusher" | "conveyor" | "mill"
    name: str
    status: Optional[str] = "active"

    # === COST FILTERING (critical for scenarios) ===
    capital_cost: Optional[float] = None
    installation_cost: Optional[float] = None
    operating_cost_annual: Optional[float] = None
    currency: str = "USD"

    # === CAPACITY FILTERING (critical for matching) ===
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    power_rating: Optional[float] = None

    # === LOCATION FILTERING ===
    location: Optional[str] = None
    process_area: Optional[str] = None

    # === TIMESTAMPS ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # === EVERYTHING ELSE (not filtered, just retrieved) ===
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Manufacturer, model, specs, dimensions, etc.",
    )

    # === TEXT FOR EMBEDDING ===
    text_content: str

    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ent_crusher_001",
                "project_id": "proj_123",
                "user_id": "user_456",
                "artifact_id": "doc_789",
                "artifact_type": "base_case",
                "entity_type": "equipment",
                "category": "crusher",
                "name": "Primary Jaw Crusher C160",
                "status": "active",
                "capital_cost": 1500000.0,
                "installation_cost": 300000.0,
                "operating_cost_annual": 120000.0,
                "currency": "USD",
                "capacity": 800.0,
                "capacity_unit": "tph",
                "power_rating": 250.0,
                "location": "Primary Crushing Station",
                "process_area": "crushing",
                "created_at": "2024-10-13T10:00:00Z",
                "updated_at": "2024-10-13T10:00:00Z",
                "properties": {
                    "manufacturer": "Metso",
                    "model": "C160",
                    "description": "Heavy-duty jaw crusher for primary crushing",
                    "weight": 85000.0,
                    "dimensions": {"length": 4.5, "width": 3.2, "height": 3.8},
                },
                "text_content": "Primary Jaw Crusher C160, Metso, 800 tph capacity, 250 kW power rating...",
            }
        }


class VectorUpsertItem(BaseModel):
    """Single vector item to upsert into Pinecone"""

    id: str = Field(..., description="Unique vector ID (usually entity_id)")
    values: List[float] = Field(
        ..., description="Vector embedding (1536-dim for text-embedding-3-small)"
    )
    metadata: VectorMetadata = Field(..., description="Associated metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ent_crusher_001",
                "values": [0.1, 0.2, 0.3],  # Truncated for example
                "metadata": {
                    "entity_id": "ent_crusher_001",
                    "project_id": "proj_123",
                    "entity_type": "equipment",
                    "name": "Primary Crusher",
                },
            }
        }


class VectorUpsertRequest(BaseModel):
    """Request to upsert vectors into Pinecone"""

    vectors: List[Dict[str, Any]] = Field(
        ..., description="List of vector objects to upsert (raw dict format)"
    )
    namespace: Optional[str] = Field(
        None, description="Pinecone namespace (typically project_id)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vectors": [
                    {
                        "id": "ent_crusher_001",
                        "values": [0.1, 0.2, 0.3],  # 1536-dim vector
                        "metadata": {
                            "entity_id": "ent_crusher_001",
                            "project_id": "proj_123",
                            "entity_type": "equipment",
                            "name": "Primary Crusher",
                            "capital_cost": 1500000.0,
                        },
                    }
                ],
                "namespace": "proj_123",
            }
        }


class VectorQueryRequest(BaseModel):
    """Request to query vectors from Pinecone"""

    query_text: Optional[str] = Field(
        None, description="Text to embed and search (if not providing query_vector)"
    )
    query_vector: Optional[List[float]] = Field(
        None, description="Pre-computed vector to search with"
    )
    top_k: int = Field(
        default=20, ge=1, le=1000, description="Number of results to return"
    )
    namespace: Optional[str] = Field(
        None, description="Pinecone namespace to search in (typically project_id)"
    )
    filter: Optional[Dict[str, Any]] = Field(
        None, description="Metadata filters for the query"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata in results"
    )
    include_values: bool = Field(
        default=False, description="Whether to include vector values in results"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "jaw crusher 800 tph capacity",
                "top_k": 10,
                "namespace": "proj_123",
                "filter": {
                    "project_id": {"$eq": "proj_123"},
                    "artifact_type": {"$eq": "base_case"},
                    "entity_type": {"$eq": "equipment"},
                    "capacity": {"$gte": 500, "$lte": 1000},
                },
                "include_metadata": True,
                "include_values": False,
            }
        }


class VectorMatch(BaseModel):
    """Single match result from Pinecone query"""

    id: str = Field(..., description="Vector ID")
    score: float = Field(
        ..., description="Similarity score (0-1, higher is more similar)"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Associated metadata")
    values: Optional[List[float]] = Field(
        None, description="Vector values if requested"
    )


class VectorQueryResponse(BaseModel):
    """Response from vector query"""

    matches: List[VectorMatch] = Field(..., description="Matching vectors")
    namespace: Optional[str] = Field(None, description="Namespace queried")

    class Config:
        json_schema_extra = {
            "example": {
                "matches": [
                    {
                        "id": "ent_crusher_001",
                        "score": 0.92,
                        "metadata": {
                            "entity_id": "ent_crusher_001",
                            "name": "Primary Jaw Crusher C160",
                            "capacity": 800.0,
                            "capital_cost": 1500000.0,
                            "entity_type": "equipment",
                        },
                        "values": None,
                    }
                ],
                "namespace": "proj_123",
            }
        }


class ScenarioQueryExtraction(BaseModel):
    """
    Extracted concepts from scenario for RAG queries.
    Generated programmatically or via LLM from scenario description.
    """

    scenario_id: str = Field(..., description="Scenario being analyzed")
    project_id: str = Field(..., description="Project ID")

    # Extracted concepts
    equipment_types: List[str] = Field(
        default_factory=list,
        description="Equipment types mentioned: crusher, conveyor, mill",
    )
    capacity_requirements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Capacity requirements: [{'value': 800, 'unit': 'tph', 'context': 'crushing'}]",
    )
    cost_types: List[str] = Field(
        default_factory=list,
        description="Cost types of interest: capital, operating, maintenance",
    )
    process_areas: List[str] = Field(
        default_factory=list,
        description="Process areas: crushing, grinding, flotation",
    )
    locations: List[str] = Field(
        default_factory=list, description="Locations mentioned in scenario"
    )
    keywords: List[str] = Field(
        default_factory=list, description="Other relevant keywords and phrases"
    )

    # Generated search queries
    search_queries: List[str] = Field(
        ..., description="Generated semantic search queries for vector DB"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "scen_001",
                "project_id": "proj_123",
                "equipment_types": ["crusher", "conveyor"],
                "capacity_requirements": [
                    {"value": 800, "unit": "tph", "context": "primary crushing"}
                ],
                "cost_types": ["capital_cost", "installation_cost"],
                "process_areas": ["crushing"],
                "locations": ["primary crushing station"],
                "keywords": ["jaw", "primary", "metso", "replacement"],
                "search_queries": [
                    "jaw crusher 800 tph capacity primary crushing",
                    "conveyor belt crushing station capital cost",
                    "metso crusher equipment specifications cost",
                ],
            }
        }


class RAGRetrievalResult(BaseModel):
    """Results from RAG retrieval for cost estimation"""

    scenario_id: str = Field(..., description="Scenario ID")
    project_id: str = Field(..., description="Project ID")

    # Retrieved entities
    base_case_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved base case entities with relevance scores",
    )
    tabular_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved tabular/catalog entities with relevance scores",
    )

    # Retrieval metadata
    queries_executed: List[str] = Field(
        default_factory=list, description="Queries that were executed"
    )
    total_retrieved: int = Field(
        default=0, description="Total entities retrieved before deduplication"
    )
    entities_after_dedup: int = Field(
        default=0, description="Entities after deduplication"
    )
    avg_relevance_score: float = Field(
        default=0.0, description="Average relevance score across all matches"
    )
    min_relevance_score: float = Field(
        default=0.0, description="Minimum relevance score in results"
    )

    # Timestamp
    retrieved_at: datetime = Field(
        default_factory=datetime.utcnow, description="Retrieval timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "scen_001",
                "project_id": "proj_123",
                "base_case_entities": [
                    {
                        "entity_id": "ent_001",
                        "name": "Primary Crusher",
                        "score": 0.92,
                        "capital_cost": 1500000.0,
                    }
                ],
                "tabular_entities": [
                    {
                        "entity_id": "cat_001",
                        "name": "Metso C160 Crusher",
                        "score": 0.89,
                        "capital_cost": 1600000.0,
                    }
                ],
                "queries_executed": [
                    "jaw crusher 800 tph",
                    "primary crushing equipment",
                ],
                "total_retrieved": 45,
                "entities_after_dedup": 32,
                "avg_relevance_score": 0.85,
                "min_relevance_score": 0.72,
                "retrieved_at": "2024-10-13T10:30:00Z",
            }
        }


class VectorDeleteRequest(BaseModel):
    """Request to delete vectors from Pinecone"""

    ids: Optional[List[str]] = Field(None, description="List of vector IDs to delete")
    delete_all: bool = Field(
        default=False, description="Delete all vectors in namespace"
    )
    filter: Optional[Dict[str, Any]] = Field(
        None, description="Delete vectors matching filter"
    )
    namespace: Optional[str] = Field(None, description="Namespace to delete from")

    class Config:
        json_schema_extra = {
            "example": {
                "filter": {
                    "project_id": {"$eq": "proj_123"},
                    "artifact_id": {"$eq": "doc_789"},
                },
                "namespace": "proj_123",
            }
        }


class VectorStatsResponse(BaseModel):
    """Statistics about vectors in Pinecone index"""

    dimension: int = Field(..., description="Dimension of vectors")
    index_fullness: float = Field(..., description="Index fullness (0-1)")
    total_vector_count: int = Field(..., description="Total vectors in index")
    namespaces: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, description="Vector count per namespace"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dimension": 1536,
                "index_fullness": 0.15,
                "total_vector_count": 15420,
                "namespaces": {
                    "proj_123": {"vector_count": 8234},
                    "proj_456": {"vector_count": 7186},
                },
            }
        }


class EmbeddingRequest(BaseModel):
    """Request to generate embeddings"""

    texts: List[str] = Field(..., description="Texts to embed", min_length=1)
    model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "Primary jaw crusher 800 tph capacity",
                    "Conveyor belt system for ore transport",
                ],
                "model": "text-embedding-3-small",
            }
        }


class EmbeddingResponse(BaseModel):
    """Response containing embeddings"""

    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used")
    total_tokens: int = Field(..., description="Total tokens processed")

    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": [
                    [0.1, 0.2, 0.3],  # Truncated for example
                    [0.4, 0.5, 0.6],
                ],
                "model": "text-embedding-3-small",
                "total_tokens": 24,
            }
        }


class BulkEntityUpsertRequest(BaseModel):
    """Request to bulk upsert entities from artifacts"""

    project_id: str = Field(..., description="Project ID")
    artifact_ids: List[str] = Field(
        ..., description="List of artifact IDs to process", min_length=1
    )
    artifact_type: Literal["base_case", "tabular_data"] = Field(
        ..., description="Type of artifacts being processed"
    )
    namespace: Optional[str] = Field(
        None, description="Pinecone namespace (defaults to project_id)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_123",
                "artifact_ids": ["doc_789", "doc_790"],
                "artifact_type": "base_case",
                "namespace": "proj_123",
            }
        }


class BulkEntityUpsertResponse(BaseModel):
    """Response from bulk entity upsert"""

    project_id: str
    artifact_ids: List[str]
    total_entities_processed: int
    total_vectors_upserted: int
    failed_entities: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_seconds: float
    namespace: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_123",
                "artifact_ids": ["doc_789", "doc_790"],
                "total_entities_processed": 156,
                "total_vectors_upserted": 156,
                "failed_entities": [],
                "processing_time_seconds": 12.5,
                "namespace": "proj_123",
            }
        }
