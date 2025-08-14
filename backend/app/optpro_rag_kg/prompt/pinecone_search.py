"""Embed query, search Pinecone, return matches + stats."""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from ..vectors.vector_store import VectorStore
from ..utils.config_adapter import SETTINGS
from ..utils.logging_utils import logger

try:
    from embeddings import build_dense_embeddings, build_sparse_vectors  # type: ignore
except Exception:
    def build_dense_embeddings(texts: List[str], model_name: str):
        import numpy as np
        return [np.ones(384, dtype=float).tolist() for _ in texts], 384
    def build_sparse_vectors(texts: List[str]):
        return None, None

def semantic_search(query: str, top_k: int = 8, use_hybrid: bool = True) -> Dict[str, Any]:
    logger.log("[Query] semantic_search:", query)
    dense, dim = build_dense_embeddings([query], SETTINGS.embed_model)
    dense_vec = dense[0]

    vs = VectorStore()
    vs.ensure_index(dim)

    sparse_vec = None
    if use_hybrid and SETTINGS.enable_hybrid:
        try:
            slist, _ = build_sparse_vectors([query])
            sparse_vec = slist[0] if slist else None
        except Exception:
            sparse_vec = None

    matches = vs.query(
        dense_vector=dense_vec,
        top_k=top_k,
        include_metadata=True,
        sparse_vector=sparse_vec,
        namespace=SETTINGS.pinecone_namespace or None,
    )
    stats = vs.stats()
    return {"matches": matches, "stats": stats}
