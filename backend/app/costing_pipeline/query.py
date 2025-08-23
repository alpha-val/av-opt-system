"""
RAG query endpoint:
- POST /costing_pipeline/query
Body:
{
  "query": "What's the installed cost of a jaw crusher for 1000 tph?",
  "top_k": 8,                # optional, default 8
  "namespace": null,         # optional; if omitted, we search across all namespaces
  "graph_nodes": 25,         # optional, cap on graph nodes returned
  "graph_hops": 1            # optional, number of hops (0,1,2)
}

Response:
{
  "matches": [... pinecone hits ...],
  "graph": {
     "nodes": [{id, labels, properties}],
     "relationships": [{type, start, end, properties}]
  }
}
"""

from __future__ import annotations
from flask import Blueprint, request, jsonify
from typing import List, Dict, Any, Optional
import re
import sys
from .costing import estimate_cost

# Reuse helpers from the ingestion code
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

from .storage import (
    embed_texts_dense,
    build_sparse_hybrid_vectors,
    PINECONE_INDEX,
    _pc,
    GraphDatabase,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
)
from .storage import make_safe_ascii

# ---------- Blueprint ----------
costing_query_pipeline_bp = Blueprint(
    "costing_pipeline", __name__, url_prefix="/costing_pipeline"
)


# ---------- Simple keywordizer for graph search ----------
WORD_RE = re.compile(r"[A-Za-z0-9_]{3,}")
STOP = set(
    [
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "into",
        "then",
        "over",
        "onto",
        "near",
        "rate",
        "size",
        "unit",
        "value",
        "kwh",
        "kw",
        "mw",
        "tph",
        "tpd",
        "gpm",
        "hp",
    ]
)


def _keywords(s: str, limit: int = 8) -> List[str]:
    words = [w.lower() for w in WORD_RE.findall(s or "")]
    words = [w for w in words if w not in STOP]
    # keep unique order
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:limit]


def _dedupe_graph_payload(graph: dict) -> dict:
    # de-dupe nodes by their returned id (your code returns elementId(n))
    uniq_nodes = {}
    for n in graph.get("nodes", []):
        nid = n.get("id")
        if nid:  # last one wins; or merge here if you want
            uniq_nodes[nid] = n

    # de-dupe relationships by (start, end, type)
    seen = set()
    uniq_rels = []
    for r in graph.get("relationships", []):
        key = (r.get("start"), r.get("end"), r.get("type"))
        if None in key:
            continue
        if key in seen:
            continue
        seen.add(key)
        uniq_rels.append(r)

    graph["nodes"] = list(uniq_nodes.values())
    graph["relationships"] = uniq_rels
    return graph


# ---------- Pinecone retrieval ----------
def pinecone_query(query_text: str, top_k: int = 8, namespace: Optional[str] = None):
    """
    Returns:
      {
        "matches": [ {id, score, metadata}, ... ],
        "chunk_ids": ["<chunk_id_1>", "<chunk_id_2>", ...]   # from match.metadata.chunk_id
      }
    """
    if _pc is None:
        raise RuntimeError("Pinecone client not initialized.")

    # Dense embedding
    q_dense = embed_texts_dense([query_text])[0]

    # Sparse hybrid vector
    q_sparse = build_sparse_hybrid_vectors([query_text])[0]

    idx = _pc.Index(PINECONE_INDEX)
    resp = idx.query(
        vector=q_dense,
        sparse_vector=q_sparse,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace or "",  # empty string → default namespace
    )

    # Normalize hits
    matches = []
    chunk_ids, seen = [], set()
    for m in resp.matches or []:
        md = dict(m.metadata) if m.metadata else {}
        matches.append(
            {
                "id": m.id,
                "score": float(m.score) if hasattr(m, "score") else None,
                "metadata": md,
            }
        )
        # Prefer explicit metadata.chunk_id; tolerate a few common variants
        cid = md.get("chunk_id") or md.get("chunkId") or md.get("chunkID")
        if cid and cid not in seen:
            seen.add(cid)
            chunk_ids.append(cid)

    return {"matches": matches, "chunk_ids": chunk_ids}


# ---------- Neo4j retrieval ----------
def _ensure_fulltext_index(session):
    """
    Neo4j v5+ uses DDL for fulltext indexes.
    We try v5 DDL first; if it fails (v4.x), we fall back to the procedure call.
    """
    try:
        # v5 DDL (works if the index doesn't already exist)
        session.run(
            """
        CREATE FULLTEXT INDEX entityFulltext IF NOT EXISTS
        FOR (n:__Entity) ON EACH [n.name, n.short_description, n.description, n.model, n.canonical_key]
        """
        )
    except Exception:
        # v4.x fallback (procedure existed in 4.x)
        session.run(
            """
        CALL db.index.fulltext.createNodeIndex(
          'entityFulltext', ['__Entity'],
          ['name','short_description','description','model','canonical_key'],
          { ifNotExists: true }
        )
        """
        )


def neo4j_fetch_graph(
    query_text: str, graph_nodes: int = 25, graph_hops: int = 1
) -> Dict[str, Any]:
    if GraphDatabase is None:
        raise RuntimeError("Neo4j driver not initialized.")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    keywords = _keywords(query_text, limit=8)

    with driver.session() as s:
        _ensure_fulltext_index(s)

        # 1) Use fulltext search to find seed nodes
        #    We build a query string like: "jaw~ crusher~ 1000~"
        if keywords:
            q = " ".join([f"{k}~" for k in keywords])
        else:
            q = query_text

        seeds = s.run(
            """
            CALL db.index.fulltext.queryNodes('entityFulltext', $q, {limit: $limit})
            YIELD node, score
            RETURN elementId(node) AS id, labels(node) AS labels, properties(node) AS props, score
            """,
            q=q,
            limit=graph_nodes,
        ).data()

        if not seeds:
            return {"nodes": [], "relationships": []}

        seed_ids = [rec["id"] for rec in seeds]

        # 2) Expand out by N hops to pick up immediate relationships
        #    We do bounded variable-length expansion with limit
        hops = max(0, min(2, int(graph_hops)))
        if hops == 0:
            data = s.run(
                """
                MATCH (n) WHERE elementId(n) IN $ids
                RETURN collect(DISTINCT {id: elementId(n), labels: labels(n), props: properties(n)}) AS Ns,
                       [] AS Rs
                """,
                ids=seed_ids,
            ).data()[0]
            return {"nodes": data["Ns"], "relationships": []}

        query = f"""
        MATCH (n) WHERE elementId(n) IN $ids
        CALL {{
            WITH n
            MATCH p=(n)-[r*1..{hops}]-(m)
            WITH nodes(p) AS ns, relationships(p) AS rs
            UNWIND ns AS x
            WITH collect(DISTINCT x) AS nx, rs
            UNWIND rs AS y
            RETURN nx AS NODES, collect(DISTINCT y) AS RELS
        }}
        WITH NODES, RELS
        // Limit output volume
        WITH NODES[0..$node_cap] AS NODES, RELS
        RETURN
            [x IN NODES | {{ id: elementId(x), labels: labels(x), props: properties(x) }}] AS Ns,
            [r IN RELS  | {{ type: type(r),
                              start: elementId(startNode(r)),
                              end: elementId(endNode(r)),
                              props: properties(r) }}] AS Rs
        """
        rec = s.run(query, ids=seed_ids, node_cap=graph_nodes).data()
        if rec:
            out = rec[0]
            return {"nodes": out["Ns"], "relationships": out["Rs"]}
        return {"nodes": [], "relationships": []}

# Add near the top of your file, after imports
def neo4j_read(cypher: str, params: dict) -> list:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        print(f"[QUERY ] Running neo4j_read..")
        result = session.run(cypher, **params)
        print(f"[QUERY ] Finished neo4j_read: {result}")
        return result.data()
# ---------- Route ----------


@costing_query_pipeline_bp.route("/query_health", methods=["GET"])
def query_health():
    return jsonify({"ok": True, "service": "costing_query_pipeline"}), 200


# --- Configure which domain edges to traverse for costing ---------------
REL_WHITELIST = [
    "USES_EQUIPMENT",
    "INCLUDES_PROCESS",
    "HAS_SCENARIO",
    "FEEDS",
    "OUTPUTS",
    "PART_OF",
    "LOCATED_IN",
    "REQUIRES",
    "POWERED_BY",
    "HAS_MATERIAL",
    "HAS_EQUIPMENT",
    "NEXT",
    "PRECEDES",
    # add/remove to taste
]


def _dedupe_preserve_order(xs):
    seen = set()
    out = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def extract_chunk_ids_from_matches(matches) -> list:
    """
    Accepts your Pinecone `matches` payload (either a list of matches or
    {"matches": [...]}). Returns a de-duped list of chunk_ids in ranking order.
    """
    if isinstance(matches, dict):
        matches_list = matches.get("matches", [])
    else:
        matches_list = matches or []

    chunk_ids = []
    for m in matches_list:
        md = (m.get("metadata") or {}) if isinstance(m, dict) else {}
        cid = md.get("chunk_id")
        if cid:
            chunk_ids.append(cid)
    return _dedupe_preserve_order(chunk_ids)


def neo4j_fetch_graph_around_chunks(
    chunk_ids: list,
    *,
    graph_hops: int = 2,
    graph_nodes: int = 50,
    rel_whitelist: list | None = None,
):
    """
    Build a compact subgraph for costing starting from retrieved Chunk nodes:
      Chunk --MENTIONS--> Entity --[REL_WHITELIST]*..hops-- Neighbor

    Returns { "nodes": [...], "edges": [...] } with ids projected from node props:
      id = coalesce(n.id, n.chunk_id, n.doc_id)
    Includes the MENTIONS edges for provenance.
    Uses your existing `neo4j_read(cypher, params)` helper.
    """
    if not chunk_ids:
        return {"nodes": [], "edges": []}

    rels = rel_whitelist or REL_WHITELIST
    # Build a typed variable-length pattern (no APOC needed)
    rel_pattern = "|".join(f"`{r}`" for r in rels)
    hops = max(1, int(graph_hops))  # ensure valid pattern
    print(f"[DEBUG : QUERY] hops: {hops}")
    cypher = f"""
    UNWIND $chunk_ids AS cid
    MATCH (c:Chunk {{chunk_id: cid}})-[:MENTIONS]->(e)
    WITH collect(DISTINCT c) AS chunks, collect(DISTINCT e) AS ents

    // Expand out from the mentioned entities up to N hops across your domain rels
    UNWIND ents AS s
    OPTIONAL MATCH p = (s)-[r:{rel_pattern}*..{hops}]-(n)
    UNWIND r AS rel
    WITH collect(DISTINCT s) AS ents,
        collect(DISTINCT n) AS others,
        collect(DISTINCT rel) AS rels,
        chunks
     
    // Also bring back provenance edges (Chunk)-[:MENTIONS]->(Entity)
    UNWIND chunks AS c2
    UNWIND ents   AS e2
    OPTIONAL MATCH (c2)-[rm:MENTIONS]->(e2)
    WITH chunks, ents, others, rels, collect(DISTINCT rm) AS mention_rels
    WITH chunks, ents, others, rels + mention_rels AS rels

    // Node budget
    WITH chunks + ents + others AS nlist, rels
    UNWIND nlist AS n
    WITH collect(DISTINCT n)[0..$graph_nodes] AS keep_nodes, rels

    // Keep only relationships whose endpoints are in-graph
    //@ WITH keep_nodes,
    //@     [r IN rels WHERE startNode(r) IN keep_nodes AND endNode(r) IN keep_nodes] AS keep_rels
    WITH keep_nodes,
        [r IN rels WHERE r IS NOT NULL AND type(r) IS NOT NULL AND startNode(r) IN keep_nodes AND endNode(r) IN keep_nodes] AS keep_rels
    RETURN
      [n IN keep_nodes |
        {{
          id: coalesce(n.id, n.chunk_id, n.doc_id),
          label: head(labels(n)),
          properties: properties(n)
        }}] AS nodes,
      [r IN keep_rels |
        {{
          source: coalesce(startNode(r).id, startNode(r).chunk_id, startNode(r).doc_id),
          target: coalesce(endNode(r).id,   endNode(r).chunk_id,   endNode(r).doc_id),
          type: type(r),
          properties: properties(r)
        }}] AS edges
    """

    nodes = []
    edges = []
    try:
        # Uses your project's Neo4j read helper (same one your old fetch function uses)
        recs = neo4j_read(cypher, {"chunk_ids": chunk_ids, "graph_nodes": int(graph_nodes)})
        if not recs:
            print("[QUERY] Neo4j returned ZERO records.")
            return {"nodes": [], "edges": []}
        row = recs[0]
        print(f"[QUERY] row: {row}")
        nodes = row.get("nodes", [])
        edges = row.get("edges", [])
    except Exception as e:
        print(f"[QUERY : ERROR] Error occurred: {e}")
    return {"nodes": nodes, "edges": edges}

@costing_query_pipeline_bp.route("/query", methods=["GET", "POST"])
def query():
    """
    RAG-based query:
    1) Embed the query
    2) Retrieve Pinecone top_k matches (dense + sparse)
    3) Retrieve Neo4j subgraph around best-matching concepts
    4) Run cost estimator on the returned subgraph (optional params)
    """
    print("[DEBUG : QUERY] running costing query")
    # Accept JSON body (POST) or query string (GET)
    data = request.get_json(silent=True) or {}
    query_text = (data.get("query") or request.args.get("query") or "").strip()
    if not query_text:
        return jsonify({"error": "Missing 'query' (JSON body or ?query=...)."}), 400

    # Retrieval knobs
    top_k = int(data.get("top_k", request.args.get("top_k", 8)))
    namespace = data.get("namespace", request.args.get("namespace"))
    graph_nodes = int(data.get("graph_nodes", request.args.get("graph_nodes", 25)))
    graph_hops = int(data.get("graph_hops", request.args.get("graph_hops", 1)))
    raw_ns = data.get("namespace", request.args.get("namespace") or "default")
    namespace = make_safe_ascii(raw_ns) if raw_ns else None

    # Costing knobs (all optional)
    cost_params = {
        "throughput_tpd": float(
            data.get("throughput_tpd", request.args.get("throughput_tpd", 0) or 0)
        ),
        "capex_exponent": float(
            data.get("capex_exponent", request.args.get("capex_exponent", 0.6) or 0.6)
        ),
        "electricity_rate": float(
            data.get(
                "electricity_rate", request.args.get("electricity_rate", 0.08) or 0.08
            )
        ),
    }
    include_costing = (
        str(
            data.get("include_costing", request.args.get("include_costing", "true"))
        ).lower()
        != "false"
    )

    try:
        # 1) Vector search (Pinecone)
        print(
            f"[DEBUG : QUERY] running Pinecone query with params: {query_text}, {top_k}, {namespace}"
        )
        matches = pinecone_query(query_text, top_k=top_k, namespace=namespace)

        # helper: pull chunk_ids out of Pinecone matches (handles both list and {"matches":[...]})
        def _extract_chunk_ids(m):
            items = m.get("matches") if isinstance(m, dict) else (m or [])
            ids, seen = [], set()
            for it in items:
                md = (it.get("metadata") or {}) if isinstance(it, dict) else {}
                cid = md.get("chunk_id")
                if cid and cid not in seen:
                    seen.add(cid)
                    ids.append(cid)
            return ids

        chunk_ids = _extract_chunk_ids(matches)
        print(f"[DEBUG : QUERY] retrieved {len(chunk_ids)} chunk_ids from Pinecone")

        # 2) Graph retrieval (Neo4j) — prefer Chunk → MENTIONS → domain graph
        if chunk_ids:
            # >>> This is the new, chunk-anchored retrieval <<<
            print(f"[QUERY] running Neo4j query around chunks: {chunk_ids}")
            graph = neo4j_fetch_graph_around_chunks(
                chunk_ids=chunk_ids,
                graph_nodes=graph_nodes,
                graph_hops=graph_hops,
                # rel_whitelist can be omitted to use defaults inside the helper
            )
            print(f"Graph FOUND> {graph}")
        else:
            # Fallback to your existing text-anchored graph fetch
            print(f"[QUERY] running Neo4j query around text (no chunk_ids): {query_text}")
            graph = neo4j_fetch_graph(
                query_text, graph_nodes=graph_nodes, graph_hops=graph_hops
            )
        print("[DEBUG] Neo4j graph retrieval complete")
        # de-dupe any fan-outs from Cypher or client merges
        graph = _dedupe_graph_payload(graph)

        # 3) Cost estimation on the subgraph
        costing = estimate_cost(graph, params=cost_params) if include_costing else None

        return (
            jsonify(
                {
                    "ok": True,
                    "query": query_text,
                    "matches": matches,
                    "chunk_ids": chunk_ids,  # helpful for debugging / provenance
                    "graph": graph,
                    "costing": costing,
                }
            ),
            200,
        )

    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 500


# # add near the top of your module
# import re
# from flask import Blueprint, request, jsonify
# from in_pipeline.storage import GraphDatabase, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# reuse your existing blueprint if you like
# costing_query_pipeline_bp = Blueprint("costing_query_pipeline", __name__, url_prefix="/costing/v1")

LABEL_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")  # Neo4j label safety


def _safe_label(lbl: str) -> str | None:
    if not lbl:
        return None
    s = lbl.strip()
    return s if LABEL_SAFE.match(s) else None


@costing_query_pipeline_bp.route("/entities", methods=["GET", "POST"])
def get_entities_by_type():
    """
    Retrieve all entities from Neo4j by a given type (label).
    Works with:
      GET  /entities?type=Equipment
      POST /entities  { "type": "Equipment" }
    """
    # Support both GET and POST
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        entity_type = (data.get("type") or "").strip()
    else:  # GET
        entity_type = (request.args.get("type") or "").strip()

    if not entity_type:
        return jsonify({"error": "Missing 'type' parameter"}), 400
    print(f"[DEBUG : QUERY] fetching entities of type: {entity_type}")
    try:
        if GraphDatabase is None:
            raise RuntimeError("Neo4j driver not initialized.")

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:

            query = f"""
            MATCH (n:`{entity_type}`)
            RETURN DISTINCT n
            """
            results = session.run(query)

            nodes = []
            for record in results:
                node = record["n"]  # Neo4j Node object
                nodes.append(
                    {
                        "id": str(node.id),  # Internal ID as string
                        "labels": list(node.labels),
                        "properties": dict(node),
                    }
                )
        return jsonify({"nodes": nodes}), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
