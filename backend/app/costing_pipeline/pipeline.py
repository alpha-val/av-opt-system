"""
End-to-end pipeline plumbing:
1) Extract PDF text
2) Chunk text
3) Dense & sparse embed, upsert to Pinecone
4) Call OpenAI function-calls extractor (TOOLS + ontology)
5) Normalize nodes/edges, deterministic IDs
6) Write to Neo4j
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
import json
from .utils.logging import get_logger

log = get_logger(__name__)

# Make sure uploaded user modules are reachable
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

from .textio import extract_text_from_pdf_stream, extract_text_from_pdf_path, chunk_text
from .storage import (
    PineconeStore,
    embed_texts_dense,
    build_sparse_hybrid_vectors,
    Neo4jWriter,
    GNode,
    GRel,
    GDoc,
    canonical_key,
    deterministic_uuid5,
    EMBED_MODEL,
    PINECONE_INDEX,
)
from .storage import make_namespace_from_filename, make_safe_ascii


# --- Try to use user's OpenAI extractor if present ---
# The user uploaded /mnt/data/extract_with_openai.py with openai_extract(chunks)-> Graph-like dict
try:
    from .kg.extract_with_openai import openai_extract_nodes_rels as user_openai_extract

    print("[DEBUG] Successfully imported openai_extract_nodes_rels.")

except Exception:
    user_openai_extract = None
    print(
        f"[ ! ERROR ! ] User OpenAI extractor found: {user_openai_extract is not None}"
    )
# --- Load ontology (NODE_TYPES, EDGE_TYPES) if available ---
try:
    from .kg import (
        ontology as ontology_factory,
    )  # must define NODE_TYPES and EDGE_TYPES, or DEFAULT_ONTOLOGY

    # Load user-defined ontology
    user_ontology = ontology_factory.load_ontology()

    if hasattr(user_ontology, "NODE_TYPES") and hasattr(user_ontology, "EDGE_TYPES"):
        ONT_NODE_TYPES = set(user_ontology.NODE_TYPES)
        ONT_EDGE_TYPES = set(user_ontology.EDGE_TYPES)
    elif hasattr(user_ontology, "DEFAULT_ONTOLOGY"):
        ONT_NODE_TYPES = set(user_ontology.DEFAULT_ONTOLOGY.get("NODE_TYPES", []))
        ONT_EDGE_TYPES = set(user_ontology.DEFAULT_ONTOLOGY.get("EDGE_TYPES", []))
    else:
        ONT_NODE_TYPES, ONT_EDGE_TYPES = set(), set()
except Exception:
    ONT_NODE_TYPES, ONT_EDGE_TYPES = set(), set()


# ---------------------- Fallback extractor (if user module unavailable) ------------
def _fallback_openai_extract(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Minimal stub if the user's `extract_with_openai.openai_extract` isn't found.
    Returns an empty extraction but keeps the pipeline running.
    """
    return {"nodes": [], "edges": []}


def call_openai_extract(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Delegate to user's extractor if available; otherwise stub.
    Your uploaded `extract_with_openai.py` should implement:
        openai_extract(chunks) -> {"nodes":[...], "edges":[...]}
    where nodes: { "id","type","properties":{...} }
          edges: { "source","target","type","properties":{...} }
    """

    if user_openai_extract is not None:
        return user_openai_extract(chunks)
    log.info("[ERROR] User-defined OpenAI extractor not found; using fallback.")
    return _fallback_openai_extract(chunks)


# ---------------------- Helpers ----------------------------------------------------


def _ensure_ontology_label(lbl: str) -> str:
    """Return lbl if it's in ontology; else return 'Unknown' to avoid bad labels."""
    if not ONT_NODE_TYPES:
        return (lbl or "Unknown") or "Unknown"
    return lbl if lbl in ONT_NODE_TYPES else "Unknown"


def _ensure_edge_type(et: str) -> str:
    if not ONT_EDGE_TYPES:
        return et
    return et if et in ONT_EDGE_TYPES else "RELATED_TO"


def _normalize_nodes_edges(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> GDoc:
    """
    - Deterministic UUID5 IDs per node based on (type|name|original_id)
    - Drop edges whose endpoints aren't found
    - Ensure labels/edge types align to ontology
    """
    # 1) assign deterministic IDs
    id_map = {}
    for n in nodes:
        key = canonical_key(n)
        new_id = deterministic_uuid5(key)
        id_map[n["id"]] = new_id
        n["id"] = new_id
        n.setdefault("properties", {})["canonical_key"] = key
        n["type"] = _ensure_ontology_label(n.get("type") or "Unknown")

    # 2) convert to GNodes
    gnodes = [
        GNode(id=n["id"], type=n["type"], properties=n.get("properties", {}))
        for n in nodes
    ]

    # 3) index for lookup
    id2node = {n.id: n for n in gnodes}

    # 4) fix edges using id_map, drop invalid
    grels: List[GRel] = []
    for e in edges:
        src = id_map.get(e.get("source"))
        tgt = id_map.get(e.get("target"))
        if not src or not tgt or src == tgt:
            continue
        s = id2node.get(src)
        t = id2node.get(tgt)
        if not s or not t:
            continue
        rtype = _ensure_edge_type(e.get("type") or "RELATED_TO")
        grels.append(
            GRel(source=s, target=t, type=rtype, properties=e.get("properties", {}))
        )

    return GDoc(nodes=gnodes, relationships=grels, source=None)


# ---------------------- Public runners -------------------------------------------


def _embed_and_upsert_to_pinecone(file_id: str, chunks):
    chunk_texts = [c["text"] for c in chunks]
    metas = [{"file_id": file_id, **(c.get("meta") or {})} for c in chunks]

    dense = embed_texts_dense(chunk_texts)
    sparse = build_sparse_hybrid_vectors(chunk_texts)

    store = PineconeStore(index_name=PINECONE_INDEX)

    # Build a safe namespace from the original filename (or file_id)
    safe_ns = make_namespace_from_filename(file_id)

    upserted = store.upsert_chunks(
        chunk_texts=chunk_texts,
        dense_vecs=dense,
        sparse_vecs=sparse,
        metas=metas,
        namespace=safe_ns,  # <-- sanitized
        id_prefix=f"{make_safe_ascii(file_id)}_",  # <-- sanitized
    )
    return {
        "chunks": len(chunks),
        "pinecone_upserted": upserted,
        "embed_model": EMBED_MODEL,
        "namespace": safe_ns,
    }


def _extract_graph_from_chunks(chunks: List[Dict[str, Any]]) -> GDoc:
    """
    Calls OpenAI function-calling extractor (user's module) and normalizes the result.
    """
    result = call_openai_extract(chunks)  # {"nodes":[...], "edges":[...]}
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    return _normalize_nodes_edges(nodes, edges)


def run_ingestion_for_pdf_stream(stream) -> Dict[str, Any]:
    """
    End-to-end for an uploaded file-like PDF stream.
    """
    filename = getattr(stream, "name", "uploaded.pdf")
    # file_id = os.path.splitext(os.path.basename(filename))[0]
    file_id = filename

    # 1) Extract text
    text = extract_text_from_pdf_stream(stream)

    # 2) Chunk
    chunks = chunk_text(text, chunk_size=1200, chunk_overlap=200)

    # 3) Embed + upsert to Pinecone
    pinecone_stats = _embed_and_upsert_to_pinecone(file_id, chunks)
    log.info(
        f"[INGEST:PINECONE] upserted {pinecone_stats['pinecone_upserted']} chunks to Pinecone"
    )

    # 4) Extract KG with OpenAI function-calls

    gdoc = _extract_graph_from_chunks(chunks)
    log.info(
        f"[INGEST:GRAPH] extracted {len(gdoc.nodes)} nodes and {len(gdoc.relationships)} relationships"
    )

    # 5) Save to Neo4j
    writer = Neo4jWriter()
    neo_stats = writer.save(gdoc, full_wipe=True)
    writer.close()

    return {
        "file": filename,
        "num_chunks": len(chunks),
        "pinecone": pinecone_stats,
        "neo4j": neo_stats,
        "nodes": len(gdoc.nodes),
        "edges": len(gdoc.relationships),
    }


def run_ingestion_for_pdf_path(path: str) -> Dict[str, Any]:
    """
    Same pipeline, but reading from an absolute path on server.
    """
    filename = os.path.basename(path)
    # file_id = os.path.splitext(filename)[0]
    file_id = filename

    text = extract_text_from_pdf_path(path)
    chunks = chunk_text(text, chunk_size=1200, chunk_overlap=200)

    pinecone_stats = _embed_and_upsert_to_pinecone(file_id, chunks)
    gdoc = _extract_graph_from_chunks(chunks)

    writer = Neo4jWriter()
    neo_stats = writer.save(gdoc, full_wipe=False)
    writer.close()

    return {
        "file": filename,
        "num_chunks": len(chunks),
        "pinecone": pinecone_stats,
        "neo4j": neo_stats,
        "nodes": len(gdoc.nodes),
        "edges": len(gdoc.relationships),
    }
