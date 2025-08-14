from __future__ import annotations
from typing import List, Tuple, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def build_dense_embeddings(
    texts: List[str], model_name: str
) -> Tuple[List[List[float]], int]:
    model = SentenceTransformer(model_name)
    preview = [
        t[:120].replace("\n", " ") + ("…" if len(t) > 120 else "") for t in texts[:3]
    ]
    print(f"[DEBUG] embedding batch: {len(texts)} chunks; samples: {preview}")
    # Important: convert to list of lists (float) for Pinecone
    embs = model.encode(
        texts, normalize_embeddings=True, convert_to_numpy=True
    )
    return embs.astype(float).tolist(), embs.shape[1]


# def build_sparse_vectors(texts: List[str]) -> List[Dict[str, Any]]:
#     """
#     Returns a list of dicts with 'indices' and 'values' for Pinecone sparse vectors.
#     We fit TF-IDF per batch (simple). For stability across batches, persist vectorizer yourself.
#     """
#     vectorizer = TfidfVectorizer(max_features=30000)
#     X = vectorizer.fit_transform(texts)  # csr matrix
#     sparse_list = []
#     for i in range(X.shape[0]):
#         row = X.getrow(i)
#         idx = row.indices.astype(int).tolist()
#         vals = row.data.astype(float).tolist()
#         sparse_list.append({"indices": idx, "values": vals})
#     return sparse_list


def build_sparse_vectors(texts: List[str], vectorizer: TfidfVectorizer | None = None):
    if vectorizer is None:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            max_features=30000,
            token_pattern=r"(?u)\b[\w\-./%°]+?\b",  # keep units like 10-mm, 3/4", 90%
        )
        X = vectorizer.fit_transform(texts)
    else:
        X = vectorizer.transform(texts)
    sparse_list = []
    for i in range(X.shape[0]):
        row = X.getrow(i)
        sparse_list.append(
            {
                "indices": row.indices.astype(int).tolist(),
                "values": row.data.astype(float).tolist(),
            }
        )
    return sparse_list, vectorizer
