from __future__ import annotations
from typing import List, Dict, Any
from app.alpha_val_simple_ingest.config import SETTINGS

from pinecone import Pinecone, ServerlessSpec
from .models import Chunk


class PineconeHybridStore:
    def __init__(self, settings):
        self.settings = settings
        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY is empty. Set it in .env")
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.namespace = settings.pinecone_namespace
        print(f"! ! ! [DEBUG] Pinecone namespace: {self.namespace}")
        self._index = None

    def ensure_index(self, dense_dim: int):
        # Create if not exists (Serverless)
        existing = [i.name for i in self.pc.list_indexes()]
        if self.index_name not in existing:
            print(f"[DEBUG] creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=dense_dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.settings.pinecone_cloud,
                    region=self.settings.pinecone_region,
                ),
            )
        self._index = self.pc.Index(self.index_name)
        print(f"\t[DEBUG] Ensured index exists: {self.index_name}")

    def upsert_chunks(
        self,
        doc_id: str,
        chunks: List[Chunk],
        dense_vectors: List[List[float]],
        sparse_vectors: List[Dict[str, Any]],
    ):
        if self._index is None:
            raise RuntimeError("Index is not initialized. Call ensure_index() first.")

        def _safe_metadata(c: Chunk) -> Dict[str, Any]:
            md = {
                "doc_id": str(c.doc_id),
                "chunk_id": str(c.chunk_id),
                "filename": str(c.filename),
                "page_start": int(c.page_start),
                "page_end": int(c.page_end),
                # NOTE: Only include section_path if present; Pinecone disallows null.
                # Alternatively: md["section_path"] = str(c.section_path or "")
            }
            if c.section_path:
                md["section_path"] = str(c.section_path)
            # strip any accidental None values
            return {k: v for k, v in md.items() if v is not None}

        vectors = []

        # inside upsert_chunks(...)
        for i, ch in enumerate(chunks):
            vec_id = f"{doc_id}:{i}"  # ← predictable, not a uuid
            meta = {
                "doc_id": doc_id,
                "chunk_idx": i,
                "filename": ch.filename or "",
                "page_start": int(ch.page_start or 1),
                "page_end": int(ch.page_end or 1),
                # optionally: "text": ch.text[:1000]
            }
            vectors.append(
                {
                    "id": vec_id,
                    "values": dense_vectors[i],
                    "metadata": meta,
                    **({"sparse_values": sparse_vectors[i]} if sparse_vectors else {}),
                }
            )

        B = 100
        for i in range(0, len(vectors), B):
            self._index.upsert(
                vectors=vectors[i : i + B], namespace=self.namespace
            )

        print("\t[UPSERT NS]", self.namespace)
        print("\t[UPSERT #]", len(vectors))
        print(
            "\t[UPSERT EXAMPLE]",
            {
                "id": vectors[0]["id"],
                "dim": len(vectors[0]["values"]),
                "has_sparse": "sparse_values" in vectors[0],
                "metadata_keys": list((vectors[0].get("metadata") or {}).keys()),
            },
        )

    def fetch_stats(self, doc_id: str, dense: List[List[float]]):
        ### Fetch stats
        idx = self.pc.Index(self.index_name)
        ns = self.namespace
        print("self.index_name >> ", self.index_name)
        print("self.namespace >> ", ns)
        # 1) Stats: confirm the namespace where vectors actually are
        print(f"[DEBUG] Stats: {idx.describe_index_stats()}")

        first_id = f"{doc_id}:0"
        f = idx.fetch(ids=[first_id], namespace=ns)
        print("\t[FETCH]", f.vectors.get(first_id) and f.vectors[first_id].metadata)

        from app.alpha_val_simple_ingest.ingest.embeddings import build_dense_embeddings

        qvec, _ = build_dense_embeddings(["jaw crusher capacity"], SETTINGS.embed_model)
        print("\t[DIM] query dim (jaw crusher capacity):", len(qvec[0]))
        # use the same dense embedding used for chunk 0 at upsert time
        dense_vec0 = dense[0] if isinstance(dense, list) else dense[0].tolist()
        res = idx.query(
            vector=dense_vec0,
            top_k=3,
            namespace=ns,
            include_metadata=True,
        )
        print("[SELF-QUERY]", [(m.id, round(m.score, 4)) for m in res.matches])

    # def upsert_chunks(self, doc_id: str, chunks: List[Chunk], dense_vectors: List[List[float]], sparse_vectors: List[Dict[str, Any]]):
    #     if self._index is None:
    #         raise RuntimeError("Index is not initialized. Call ensure_index() first.")
    #     # build Pinecone vectors
    #     vectors = []
    #     for c, d, s in zip(chunks, dense_vectors, sparse_vectors):
    #         vectors.append({
    #             "id": f"{doc_id}:{c.chunk_id}",
    #             "values": d,
    #             "sparse_values": s,
    #             "metadata": {
    #                 "doc_id": c.doc_id,
    #                 "chunk_id": c.chunk_id,
    #                 "filename": c.filename,
    #                 "page_start": c.page_start,
    #                 "page_end": c.page_end,
    #                 # "section_path": c.section_path,
    #             }
    #         })
    #     # upsert in batches
    #     B = 100
    #     for i in range(0, len(vectors), B):
    #         self._index.upsert(vectors=vectors[i:i+B])
