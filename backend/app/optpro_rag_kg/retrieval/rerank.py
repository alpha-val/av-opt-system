"""Reranking stub (swap with cross-encoder)."""
from typing import List, Dict, Any

def simple_rerank(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(hits, key=lambda x: x.get("score", 0), reverse=True)
