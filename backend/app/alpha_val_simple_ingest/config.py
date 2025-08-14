"""
App configuration: loads from .env and exposes simple constants.
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "av-opt-idx")
    pinecone_cloud: str = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")
    pinecone_namespace: str = os.getenv("PINECONE_NAMESPACE", "default")

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    embed_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # Alpha-Val emphasis toggles
    prefer_costs: bool = True
    prefer_equipment: bool = True
    prefer_process: bool = True
    prefer_scenario: bool = True


SETTINGS = Settings()
