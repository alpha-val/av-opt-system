# ````python // filepath: /Users/test/Documents/Projects/Optionality_Mining/av-opt-system/backend/app/alpha_val_simple_ingest/query/pinecone_search.py
from __future__ import annotations
from typing import List, Dict, Any
from pinecone import Pinecone
from ..config import SETTINGS


def pinecone_hybrid_query(
    dense_vector: List[float],
    top_k: int = 8,
    include_metadata: bool = True,
    namespace: str = SETTINGS.pinecone_namespace,
) -> List[Dict[str, Any]]:
    """
    Query Pinecone index using a dense vector. Returns list of {id, score, metadata}.
    """
    pc = Pinecone(api_key=SETTINGS.pinecone_api_key)
    index = pc.Index(SETTINGS.pinecone_index_name)
    query_kwargs = {
        "vector": dense_vector,
        "top_k": top_k,
        "include_values": False,
        "include_metadata": include_metadata,
    }

    if namespace or SETTINGS.pinecone_namespace:
        query_kwargs["namespace"] = namespace or SETTINGS.pinecone_namespace
    try:
        res = index.query(**query_kwargs)
    except Exception as e:
        return [{"error": "query_failed", "detail": str(e)}]

    print("[DEBUG] namespace:", query_kwargs.get("namespace"))
    matches = getattr(res, "matches", []) or []
    out: List[Dict[str, Any]] = []
    for m in matches:
        out.append(
            {
                "id": getattr(m, "id", None),
                "score": getattr(m, "score", None),
                "metadata": dict(getattr(m, "metadata", {}) or {}),
            }
        )
    return out


# Optional helper for ad-hoc testing (uses the same embed path as the service)
from .embedding import embed_query


def pinecone_semantic_search(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    vec, _ = embed_query(query)
    return pinecone_hybrid_query(
        dense_vector=vec,
        top_k=top_k,
        include_metadata=True,
        namespace=SETTINGS.pinecone_namespace,
    )
