from typing import List, Dict, Any
from ..stores.vector_store import VectorStore

class VectorRetriever:
    def __init__(self, vs: VectorStore): self.vs = vs
    def search(self, q: str, top_k: int = 8) -> List[Dict[str, Any]]:
        return self.vs.query(q, top_k=top_k)
