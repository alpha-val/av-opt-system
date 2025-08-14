# ````python // filepath: /Users/test/Documents/Projects/Optionality_Mining/av-opt-system/backend/app/alpha_val_simple_ingest/query/service.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

from .embedding import embed_query
from .pinecone_search import pinecone_hybrid_query
from .neo4j_search import query_neo4j_for_docs
from ..config import SETTINGS


def run_query_pipeline(
    question: str,
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    End-to-end:
      1. Embed user question
      2. Vector search Pinecone (retrieve relevant chunk metadata)
      3. Use retrieved doc_ids to fetch related Neo4j subgraph
      4. Return aggregated result
    """
    question = (question or "").strip()
    if not question:
        return {"error": "Empty question."}
    print(f"[DEBUG] Running query pipeline for question: {question}")

    # 1) Embed user question
    dense_vec, dim = embed_query(question)

    # 2) Vector search Pinecone
    pc_matches = pinecone_hybrid_query(
        dense_vector=dense_vec,
        top_k=top_k,
        namespace=SETTINGS.pinecone_namespace,
    )

    # 3) pretty-print
    for i, m in enumerate(pc_matches, 1):
        md = m.get("metadata", {}) or {}
        print(f"{i:02d}. score={m.get('score'):.4f}  id={m.get('id')}")
        print("    doc_id:", md.get("doc_id"))
        print("    page:", md.get("page"))
        print("    is_table:", md.get("is_table"))
        preview = (md.get("text") or "")[:160].replace("\n"," ")
        print("    text:", preview, "\n")

    # 4) Collect doc_ids from metadata if present
    doc_ids = list(
        {
            m["metadata"].get("doc_id")
            for m in pc_matches
            if m.get("metadata", {}).get("doc_id")
        }
    )
    print("Doc IDs from Pinecone:", doc_ids)
    graph_data = query_neo4j_for_docs(doc_ids)

    # Basic formatting
    formatted_nodes = [
        {
            "id": n["id"],
            "labels": n["labels"],
            **(n.get("properties", {})),
        }
        for n in graph_data.get("nodes", [])
    ]
    formatted_rels = [
        {
            "id": r["id"],
            "source": r["source"],
            "target": r["target"],
            "type": r["type"],
            **(r.get("properties", {})),
        }
        for r in graph_data.get("relationships", [])
    ]

    return {
        "question": question,
        "retrieval": {
            "matches": pc_matches,
            "doc_ids": doc_ids,
        },
        "graph": {
            "nodes": formatted_nodes,
            "relationships": formatted_rels,
        },
    }