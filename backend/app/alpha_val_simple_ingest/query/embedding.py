#````python // filepath: /Users/test/Documents/Projects/Optionality_Mining/av-opt-system/backend/app/alpha_val_simple_ingest/query/embedding.py
from __future__ import annotations
from typing import List, Tuple

from ..config import SETTINGS

# Optional OpenAI import (only used if an OpenAI embedding model is selected)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Lazy import for sentence-transformers done inside function to avoid startup cost


def embed_query(text: str) -> Tuple[List[float], int]:
    """
    Embed a query using the model defined in SETTINGS.embed_model.
    Supports:
      - Local / HF sentence-transformers models (e.g. 'sentence-transformers/all-MiniLM-L6-v2')
      - OpenAI embedding models (names starting with 'text-embedding-' or 'text-search-')
    Returns (embedding_vector, dimension).
    """
    model_name = SETTINGS.embed_model

    if not text or not text.strip():
        raise ValueError("Query text is empty.")

    # Heuristic: treat as OpenAI model if it matches known prefixes
    is_openai = model_name.startswith(("text-embedding-", "text-search-"))

    if is_openai:
        if OpenAI is None:
            raise RuntimeError("openai package not installed but OpenAI embedding model selected.")
        client = OpenAI()
        resp = client.embeddings.create(model=model_name, input=[text])
        vec = resp.data[0].embedding
        return vec, len(vec)

    # Default: sentence-transformers local / HF model
    try:
        print("[DEBUG] QUERY > using sentence-transformers for embedding")
        from sentence_transformers import SentenceTransformer  # local import
    except ImportError as e:
        raise RuntimeError("sentence-transformers not installed; cannot load local embedding model.") from e

    model = SentenceTransformer(model_name)
    vec = model.encode([text], show_progress_bar=False)[0]
    # Ensure list[float]
    if hasattr(vec, "tolist"):
        vec = vec.tolist()
    else:
        vec = list(vec)
    return vec, len(vec)