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
    pinecone_metric: str = os.getenv("PINECONE_METRIC", "cosine")

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    embedding_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    enable_sparse: bool = os.environ.get("ENABLE_SPARSE", "0") == "1"
    
    enable_logs: bool = os.environ.get("ENABLE_LOGS", "1") == "1"
    enable_kg: bool = os.environ.get("ENABLE_KG", "1") == "1"
    enable_neo4j_write: bool = os.environ.get("ENABLE_NEO4J_WRITE", "1") == "1"
    enable_hybrid: bool = os.environ.get("ENABLE_HYBRID", "1") == "1"

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    max_chunk_text_preview: int = int(os.environ.get("MAX_CHUNK_TEXT_PREVIEW", "500"))

    # LangExtract Model parameters (e.g., gemini-2.5-flash)
    model_params_name: str = os.getenv("MODEL_PARAMS_NAME", "gemini-2.5-flash")
    model_params_max_char_buffer: int = int(os.getenv("MODEL_PARAMS_MAX_CHAR_BUFFER", "5000"))
    
    # Alpha-Val emphasis toggles
    prefer_costs: bool = True
    prefer_equipment: bool = True
    prefer_process: bool = True
    prefer_scenario: bool = True

    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

SETTINGS = Settings()

