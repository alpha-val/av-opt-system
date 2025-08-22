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
        namespace=namespace or "",  # empty string → search default namespace
    )
    # Normalize hits
    matches = []
    for m in resp.matches or []:
        matches.append(
            {
                "id": m.id,
                "score": float(m.score) if hasattr(m, "score") else None,
                "metadata": dict(m.metadata) if m.metadata else {},
            }
        )
    return matches


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


# ---------- Routew ----------


@costing_query_pipeline_bp.route("/query_health", methods=["GET"])
def query_health():
    return jsonify({"ok": True, "service": "costing_query_pipeline"}), 200


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
        print(f"[DEBUG : QUERY] running Pinecone query with params: {query_text}, {top_k}, {namespace}")
        matches = pinecone_query(query_text, top_k=top_k, namespace=namespace)

        # 2) Graph retrieval (Neo4j)
        graph = neo4j_fetch_graph(
            query_text, graph_nodes=graph_nodes, graph_hops=graph_hops
        )

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
