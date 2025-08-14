"""Pinecone vector store with optional hybrid sparse support."""
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from ..config_adapter import SETTINGS
from ..utils.logging import get_logger

log = get_logger(__name__)

class VectorStore:
    def __init__(self, index_name: Optional[str] = None, model_name: Optional[str] = None):
        self.index_name = index_name or SETTINGS.pinecone_index_name
        self.pc = Pinecone(api_key=SETTINGS.pinecone_api_key)
        self.model = SentenceTransformer(model_name or SETTINGS.embedding_model)
        # connect or create index (384-dim for all-MiniLM-L6-v2)
        try:
            self.index = self.pc.Index(self.index_name)
        except Exception:
            log.info("Creating Pinecone index %s", self.index_name)
            self.pc.create_index(
                name=self.index_name, dimension=384, metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=SETTINGS.pinecone_region),
            )
            self.index = self.pc.Index(self.index_name)

    # ---- Dense ----
    def embed_dense(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    # ---- Sparse (hash-trick) ----
    def embed_sparse(self, texts: List[str], dim: int = 65536) -> List[Dict[str, List[float]]]:
        # Simple hashed bag-of-words (placeholder). Replace with SPLADE/BM25 for production.
        outs: List[Dict[str, List[float]]] = []
        for t in texts:
            counts = {}
            for tok in t.lower().split():
                idx = hash(tok) % dim
                counts[idx] = counts.get(idx, 0) + 1.0
            indices = list(counts.keys())
            values = [counts[i] for i in indices]
            outs.append({"indices": indices, "values": values})
        return outs

    def upsert(self, items: List[Dict[str, Any]]):
        """items: [{id, text, metadata}] → embeds & upserts."""
        texts = [it["text"] for it in items]
        dense = self.embed_dense(texts)
        payloads = []
        if SETTINGS.enable_sparse:
            sparse_list = self.embed_sparse(texts)
            for it, d, sp in zip(items, dense, sparse_list):
                payloads.append({
                    "id": it["id"],
                    "values": d,
                    "sparse_values": sp,
                    "metadata": {k:v for k,v in it.items() if k not in {"id","text"}} | {"text": it["text"][:2000]}
                })
        else:
            for it, d in zip(items, dense):
                payloads.append({
                    "id": it["id"],
                    "values": d,
                    "metadata": {k:v for k,v in it.items() if k not in {"id","text"}} | {"text": it["text"][:2000]}
                })
        self.index.upsert(payloads)
        log.info("Upserted %d vectors", len(payloads))

    def query(self, q: str, top_k: int = 8) -> List[Dict[str, Any]]:
        qd = self.embed_dense([q])[0]
        res = self.index.query(vector=qd, top_k=top_k, include_metadata=True)
        hits = []
        for m in res["matches"]:
            md = m.get("metadata", {}) or {}
            hits.append({"id": m["id"], "score": m.get("score", 0.0), "metadata": md, "text": md.get("text","")})
        return hits
