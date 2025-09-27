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
from flask import jsonify
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
import json
from .utils.logging import get_logger
from uuid import uuid5

log = get_logger(__name__)

# Make sure uploaded user modules are reachable
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

from .textio import (
    extract_text_from_pdf_stream,
    extract_text_from_pdf_path,
    chunk_text,
    normalize_chunks_for_ingest,
    clean_extracted_text,
)
from .storage import (
    embed_and_upsert_to_pinecone,
    Neo4jWriter,
    GNode,
    GRel,
    GDoc,
    canonical_key,
    deterministic_uuid5,
    EMBED_MODEL,
    PINECONE_INDEX,
    # PINECONE_NAMESPACE,
)
from .storage import make_namespace_from_filename, make_safe_ascii

# --- Try to use user's OpenAI extractor if present ---
# The user uploaded /mnt/data/extract_with_openai.py with openai_extract(chunks)-> Graph-like dict
try:
    from .kg.extract_with_openai import openai_extract_nodes_rels
except Exception:
    openai_extract_nodes_rels = None
    print(
        f"[ ! ERROR ! ] User OpenAI extractor found: {openai_extract_nodes_rels is not None}"
    )

try:
    from .kg.extract_with_openai import openai_extract_nodes_rels_mentions
except Exception:
    openai_extract_nodes_rels_mentions = None
    print(
        f"[ ! ERROR ! ] User OpenAI extractor found: {openai_extract_nodes_rels_mentions is not None}"
    )

try:
    from .kg.extract_with_openai_with_mentions import (
        openai_extract_nodes_rels_and_ingest_mentions,
    )
except Exception:
    openai_extract_nodes_rels_and_ingest_mentions = None
    print(
        f"[ ! ERROR ! ] User OpenAI extractor found: {openai_extract_nodes_rels_and_ingest_mentions is not None}"
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
    # Trust extractor IDs; only backfill if missing.
    id_map = {}
    for n in nodes:
        old_id = n.get("id")  # may be None if extractor forgot it

        # Ensure canonical_key exists (use existing if already set)
        props = n.setdefault("properties", {})
        key = props.get("canonical_key") or canonical_key(n)
        props["canonical_key"] = key

        # Only create a UUID5 if the node has no id yet
        if not old_id:
            new_id = deterministic_uuid5(key)
            n["id"] = new_id
            print(f"[W A R N I N G] Backfilled missing node ID: {new_id} for key: {key}")
        else:
            new_id = old_id

        # Normalize/validate label
        n["type"] = _ensure_ontology_label(n.get("type") or "Unknown")

        # Critical: make id_map a pass-through so edge remap works for both cases.
        # If old_id is None (we backfilled), map new_id->new_id to be safe.
        id_map[old_id if old_id is not None else new_id] = new_id
        
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
        src = id_map.get(e.get("source"), e.get("source"))
        tgt = id_map.get(e.get("target"), e.get("target"))
        if not src or not tgt or src == tgt:
            continue
        s = id2node.get(src)
        t = id2node.get(tgt)
        if not s or not t:
            continue
        rtype = _ensure_edge_type(e.get("type") or "RELATED_TO")
        grels.append(GRel(source=s, target=t, type=rtype, properties=e.get("properties", {})))

    return GDoc(nodes=gnodes, relationships=grels, source=None)


# ---------------------- Public runners -------------------------------------------


def _extract_graph_from_chunks(chunks: List[Dict[str, Any]]) -> GDoc:
    """
    Calls OpenAI function-calling extractor (user's module) and normalizes the result.
    """
    result = openai_extract_nodes_rels_mentions(chunks=chunks)
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
    print(f"[INGEST 1] - Extracted {len(text)} characters of text from PDF.")

    # 2) Clean text
    text = clean_extracted_text(text)

    # 3) Chunk
    raw_chunks = chunk_text(text, chunk_size=1200, chunk_overlap=200)
    print(f"[INGEST 2] - Chunked PDF into {len(raw_chunks)} chunks.")

    print(f"[INGEST 3] - setting doc_id to {filename}")
    doc_id = f"doc|{filename}"

    chunks = normalize_chunks_for_ingest(raw_chunks, doc_id=doc_id, namespace="default")
    # print(f"[INGEST 4.A] - Extracted chunks: {chunks}")
    print(f"[INGEST 4] - Extracted chunks: {len(chunks)}")

    # 4) Embed + upsert to Pinecone
    pinecone_stats = embed_and_upsert_to_pinecone(file_id, chunks)
    print(f"[DEBUG] stats: {pinecone_stats}")
    
    # 5) Extract KG with OpenAI function-calls
    print("[INGEST] - Extracting knowledge graph...")
    gdoc = _extract_graph_from_chunks(chunks)
    print(
        f"[INGEST] - Done extracting knowledge graph with: {len(gdoc.nodes)} nodes and {len(gdoc.relationships)} relationships"
    )
    # print(f"GDoc: {gdoc}")

    # 6) Save to Neo4j
    writer = Neo4jWriter()
    neo_stats = writer.save(gdoc, full_wipe=True)
    writer.close()

    print("[DEBUG] - - - DONE - - -")
    # return {
    #     "file": filename,
    #     "num_chunks": len(chunks),
    #     "pinecone": pinecone_stats,
    #     "neo4j": neo_stats,
    #     "nodes": len(gdoc.nodes),
    #     "edges": len(gdoc.relationships),
    # }
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

    pinecone_stats = embed_and_upsert_to_pinecone(file_id, chunks)
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
