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
from .kg.ontology import load_ontology

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


# ---------- Pinecone retrieval ----------
def pinecone_query(query_text: str, top_k: int = 8, namespace: Optional[str] = None, score_cutoff: float = 0.33) -> Dict[str, Any]:
    q_dense = embed_texts_dense([query_text])[0]
    q_sparse = build_sparse_hybrid_vectors([query_text])[0]
    print(f"[PINECONE] querying... for text {query_text}")
    idx = _pc.Index(PINECONE_INDEX)
    resp = idx.query(
        vector=q_dense,
        sparse_vector=q_sparse,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace or "",
    )

    matches = []
    chunk_ids, seen = [], set()
    print(f"[PINECONE] received {len(resp.matches or [])} matches")
    for m in resp.matches or []:
        md = dict(m.metadata) if m.metadata else {}
        print(f"[PINECONE] match: {m.id} > score: {m.score}")
        if m.score >= score_cutoff:
            matches.append(
                {
                    "id": m.id,
                    "score": float(m.score) if hasattr(m, "score") else None,
                    "metadata": md,
                }
            )
            cid = md.get("chunk_id") or md.get("chunkId") or md.get("chunkID")

        if cid and cid not in seen:
            seen.add(cid)
            chunk_ids.append(cid)

    return {"matches": matches, "chunk_ids": chunk_ids}


# Add near the top of your file, after imports
def neo4j_read(cypher: str, params: dict) -> list:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(cypher, **params)
        return result.data()


# ---------- Route ----------


@costing_query_pipeline_bp.route("/query_health", methods=["GET"])
def query_health():
    return jsonify({"ok": True, "service": "costing_query_pipeline"}), 200


# --- Configure which domain edges to traverse for costing ---------------
ont = load_ontology()
REL_WHITELIST = ont.get("EDGE_TYPES")
# [
#     "USES_EQUIPMENT",
#     "INCLUDES_PROCESS",
#     "HAS_SCENARIO",
#     "FEEDS",
#     "OUTPUTS",
#     "PART_OF",
#     "LOCATED_IN",
#     "REQUIRES",
#     "POWERED_BY",
#     "HAS_MATERIAL",
#     "HAS_EQUIPMENT",
#     "NEXT",
#     "PRECEDES",
#     # add/remove to taste
# ]


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
    chunk_matches,
    *,
    graph_hops: int = 2,
    graph_nodes: int = 50,
    rel_whitelist: list | None = None,
    min_score: float = 0.0,  # ignore low-confidence chunk matches
):
    """
    From Pinecone *chunk matches*, extract seed IDs and build a compact subgraph:
        (:Chunk {id = <cid>})-[:MENTIONS]->(:Entity)-[REL_WHITELIST]*..hops-(:Neighbor)
    """

    # --- 0) normalize matches -> ordered, de-duped seed ids ------------------
    def _coerce_matches(m):
        if isinstance(m, dict):
            if isinstance(m.get("matches"), dict):
                inner = m["matches"]
                return inner.get("chunk_ids") or [], inner.get("matches") or []
            return m.get("chunk_ids") or [], m.get("matches") or []
        return [], (m or [])

    def _extract_chunk_ids(m) -> list[str]:
        explicit_ids, match_list = _coerce_matches(m)
        seen, out = set(), []

        # Explicit first (preserve order)
        for cid in explicit_ids:
            if cid and cid not in seen:
                seen.add(cid)
                out.append(cid)

        # Then from matches (respect min_score)
        for it in match_list:
            if not isinstance(it, dict):
                continue
            score = it.get("score")
            if score is not None and float(score) < float(min_score):
                continue
            md = it.get("metadata") or {}
            # You said you want to use the Pinecone match "id";
            # still fall back to metadata.chunk_id if needed.
            cid = (
                it.get("id")
                or md.get("chunk_id")
                or md.get("chunkId")
                or md.get("chunkID")
            )
            if cid and cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out

    chunk_ids = _extract_chunk_ids(chunk_matches)
    print(f"[QUERY] using {len(chunk_ids)} seed chunk_ids (min_score={min_score})")
    if not chunk_ids:
        return {"nodes": [], "edges": []}

    # --- 1) traversal config --------------------------------------------------
    rels = rel_whitelist or REL_WHITELIST
    rel_pattern = "|".join(f"`{r}`" for r in rels)
    hops = max(1, int(graph_hops))

    # --- 2) Cypher: seed via WHERE (avoid {id: cid} map literal) -------------
    cypher = f"""
    // Seed strictly from provided chunk ids (property 'id' or 'chunk_id', not internal id())
    UNWIND $chunk_ids AS cid
    MATCH (c:Chunk)
    WHERE c.chunk_id = cid
        OR (c.canonical_key IS NOT NULL AND c.canonical_key ENDS WITH cid)
    // from these matched chunks, follow MENTIONS to entities
    OPTIONAL MATCH (c)-[:MENTIONS]->(e)
    WITH collect(DISTINCT c) AS chunks, collect(DISTINCT e) AS ents

    // Expand from mentioned entities up to N hops across domain rels
    UNWIND ents AS s
    OPTIONAL MATCH p = (s)-[r:{rel_pattern}*..{hops}]-(n)
    UNWIND r AS rel
    WITH collect(DISTINCT s) AS ents,
        [x IN collect(DISTINCT n) WHERE x IS NOT NULL] AS others,
        [x IN collect(DISTINCT rel) WHERE x IS NOT NULL] AS rels,
        chunks

    // Bring back provenance edges (Chunk)-[:MENTIONS]->(Entity)
    UNWIND chunks AS c2
    UNWIND ents   AS e2
    OPTIONAL MATCH (c2)-[rm:MENTIONS]->(e2)
    WITH chunks, ents, others, rels, collect(DISTINCT rm) AS mention_rels
    WITH chunks, ents, others, rels + mention_rels AS rels
    // Node budget
    WITH chunks + ents + others AS nlist, rels
    UNWIND nlist AS n
    WITH [x IN collect(DISTINCT n)[0..$graph_nodes] WHERE x IS NOT NULL] AS keep_nodes, rels

    // Keep only relationships whose endpoints are in-graph
    WITH keep_nodes,
        [r IN rels
            WHERE startNode(r) IN keep_nodes
            AND endNode(r)   IN keep_nodes] AS keep_rels

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

    # --- 3) run & return ------------------------------------------------------
    try:
        recs = neo4j_read(
            cypher, {"chunk_ids": chunk_ids, "graph_nodes": int(graph_nodes)}
        )
        if not recs:
            print("[QUERY] Neo4j returned ZERO records.")
            return {"nodes": [], "edges": []}
        row = recs[0]
        nodes = row.get("nodes", []) or []
        edges = row.get("edges", []) or []
        print(f"[QUERY] fetched graph: nodes={len(nodes)}, edges={len(edges)}")

    except Exception as e:
        print(f"[QUERY : ERROR] Error occurred: {e}")

    print(f"[QUERY] SUCCESS: graph with {len(nodes)} nodes and {len(edges)} edges")
    return {"nodes": nodes, "edges": edges}


def neo4j_fetch_graph_around_chunks_with_filtering(
    chunk_matches,
    *,
    graph_hops: int = 0,  # allow 0 to get only direct mentions
    graph_nodes: int = 50,
    rel_whitelist: list | None = None,
    min_score: float = 0.0,
    entity_names: list[str] | None = None,  # e.g., ["Jaw Crusher"]
    entity_regex: list[str] | None = None,  # e.g., [".*\\bjaw\\s+crusher\\b.*"]
):
    """
    From Pinecone *chunk matches*, extract seed IDs and build a compact subgraph.
    If entity_names or entity_regex are provided, we only keep entities that match
    those filters at the MENTIONS edge (exact-ish match via name/aliases/surface).
    """
    print("[NEO4j] - - - >")
    def _coerce_matches(m):
        if isinstance(m, dict):
            if isinstance(m.get("matches"), dict):
                inner = m["matches"]
                return inner.get("chunk_ids") or [], inner.get("matches") or []
            return m.get("chunk_ids") or [], m.get("matches") or []
        return [], (m or [])

    def _extract_chunk_ids(m) -> list[str]:
        explicit_ids, match_list = _coerce_matches(m)
        seen, out = set(), []

        for cid in explicit_ids:
            if cid and cid not in seen:
                seen.add(cid)
                out.append(cid)

        for it in match_list:
            if not isinstance(it, dict):
                continue
            score = it.get("score")
            print(f"\t id: {it.get('id')} score: {score}")
            if score is not None and float(score) < float(min_score):
                print(f"  - \tSkipping {it.get('id')} (score: {score} - min_score: {min_score})")
                continue
            md = it.get("metadata") or {}
            cid = (
                it.get("id")
                or md.get("chunk_id")
                or md.get("chunkId")
                or md.get("chunkID")
            )
            if cid and cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out

    try:
        chunk_ids = _extract_chunk_ids(chunk_matches)
        print(f"[QUERY] using {len(chunk_ids)} seed chunk_ids (min_score={min_score}), > > > entity names: {entity_names}")
    except Exception as e:
        print(f"[QUERY] Error extracting chunk IDs: {e}")

    if not chunk_ids:
        return {"nodes": [], "edges": []}

    rels = rel_whitelist or REL_WHITELIST
    rel_pattern = "|".join(f"`{r}`" for r in rels)
    hops = max(0, int(graph_hops))  # <-- allow zero-hop graphs

    # Lowercase names client-side (for case-insensitive exact checks)
    lowered_names = [s.strip().lower() for s in (entity_names or []) if s and s.strip()]
    regex_list = entity_regex or []

    cypher = f"""
    UNWIND $chunk_ids AS cid
    MATCH (c:Chunk)
    WHERE c.chunk_id = cid
       OR (c.canonical_key IS NOT NULL AND c.canonical_key ENDS WITH cid)

    // Filter MENTIONS to only entities matching provided names/regex (if any)
    OPTIONAL MATCH (c)-[m:MENTIONS]->(e)
    WHERE
      (
        // If no filters given, keep default behavior (everything mentioned)
        ($names_is_empty AND $regex_is_empty)
        // Otherwise require at least one match against names or regex
        OR
        (
          // exact-ish: compare lowercase forms of e.name, any e.aliases, or m.surface
          (size($names_lc) > 0 AND (
             toLower(e.name) IN $names_lc
             OR any(a IN coalesce(e.aliases, []) WHERE toLower(a) IN $names_lc)
             OR (m.surface IS NOT NULL AND toLower(m.surface) IN $names_lc)
          ))
          OR
          // regex option (server-side patterns). Use cautiously.
          (size($regex_list) > 0 AND (
             any(rx IN $regex_list WHERE e.name =~ rx)
             OR any(rx IN $regex_list WHERE any(a IN coalesce(e.aliases, []) WHERE a =~ rx))
             OR (m.surface IS NOT NULL AND any(rx IN $regex_list WHERE m.surface =~ rx))
          ))
        )
      )
    WITH collect(DISTINCT c) AS chunks,
         [x IN collect(DISTINCT e) WHERE x IS NOT NULL] AS ents,
         [x IN collect(DISTINCT m) WHERE x IS NOT NULL] AS mention_rels

    // Optional domain expansion from the filtered entities
    UNWIND ents AS s
    OPTIONAL MATCH p = (s)-[r:{rel_pattern}*..{hops}]-(n)
    UNWIND r AS rel
    WITH
        chunks,
        ents,
        mention_rels,
        collect(DISTINCT n)   AS others,
        collect(DISTINCT rel) AS rels1
    WITH chunks, ents, others, (rels1 + mention_rels) AS rels

    // Node budget
    WITH chunks + ents + others AS nlist, rels
    UNWIND nlist AS n
    WITH [x IN collect(DISTINCT n)[0..$graph_nodes] WHERE x IS NOT NULL] AS keep_nodes, rels

    // Keep only relationships whose endpoints are in-graph
    WITH keep_nodes,
         [r IN rels WHERE startNode(r) IN keep_nodes AND endNode(r) IN keep_nodes] AS keep_rels

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

    try:
        recs = neo4j_read(
            cypher,
            {
                "chunk_ids": chunk_ids,
                "graph_nodes": int(graph_nodes),
                "names_lc": lowered_names,
                "regex_list": regex_list,
                "names_is_empty": len(lowered_names) == 0,
                "regex_is_empty": len(regex_list) == 0,
            },
        )
    except Exception as e:
        print(f"[QUERY : ERROR] Error occurred: {e}")
        return {"nodes": [], "edges": []}
    if not recs:
        print("[NEO4j] Neo4j returned ZERO records.")
        return {"nodes": [], "edges": []}
    
    row = recs[0]
    nodes = row.get("nodes", []) or []
    edges = row.get("edges", []) or []
    print(f"[NEO4j] fetched graph: nodes={len(nodes)}, edges={len(edges)}")
    print("[NEO4j] < - - -")
    return {"nodes": nodes, "edges": edges}


def neo4j_print_basics(chunk_ids: list[str] | None = None, limit: int = 10) -> dict:
    """
    Quick inventory + sanity checks for your KG.
    Prints:
      - Label counts
      - Sample Chunk nodes (chunk_id/id/canonical_key/text snippet)
      - Sample MENTIONS edges
      - Optional: for each provided chunk_id, whether it exists & what it mentions

    Returns a dict with the same info for programmatic use.
    """
    out = {"labels": [], "chunks": [], "mentions": [], "checks": []}

    try:
        # 1) Label counts
        q_labels = """
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS cnt
        ORDER BY cnt DESC
        """
        rows = neo4j_read(q_labels, {})
        out["labels"] = rows
        print("\n[NEO4J] Label counts:")
        for r in rows:
            print(f"  {r['label']}: {r['cnt']}")

        # 2) Sample Chunk nodes
        q_chunks = """
        MATCH (c:Chunk)
        RETURN
          c.chunk_id      AS chunk_id,
          c.id            AS id,
          c.canonical_key AS canonical_key,
          c.seq           AS seq,
          left(toString(c.text), 160) AS text_snippet
        LIMIT $limit
        """
        rows = neo4j_read(q_chunks, {"limit": int(limit)})
        out["chunks"] = rows
        print("\n[NEO4J] Sample :Chunk nodes:")
        if not rows:
            print("  (none)")
        for r in rows:
            print(
                f"  chunk_id={r['chunk_id']} id={r['id']} seq={r['seq']} canon={r['canonical_key']}"
            )
            print(f"    text: {r['text_snippet']}")

        # 3) Sample MENTIONS edges
        q_mentions = """
        MATCH (c:Chunk)-[m:MENTIONS]->(e)
        RETURN
          c.chunk_id                             AS chunk_id,
          coalesce(e.id, e.name, e.uuid)        AS entity_id,
          head(labels(e))                        AS entity_label,
          m.start                                AS start,
          m.end                                  AS end,
          m.surface                              AS surface,
          m.confidence                           AS confidence
        LIMIT $limit
        """
        rows = neo4j_read(q_mentions, {"limit": int(limit)})
        out["mentions"] = rows
        print("\n[NEO4J] Sample (Chunk)-[:MENTIONS]->(Entity):")
        if not rows:
            print("  (none)")
        for r in rows:
            print(
                f"  {r['chunk_id']} -[:MENTIONS]-> ({r['entity_label']}:{r['entity_id']})"
                f" span=({r['start']},{r['end']}) surface={r['surface']!r} conf={r['confidence']}"
            )

        # 4) Optional: verify the specific chunk_ids you'll pass to the fetcher
        if chunk_ids:
            q_check = """
            UNWIND $chunk_ids AS cid
            OPTIONAL MATCH (c:Chunk {chunk_id: cid})
            WITH cid, c
            OPTIONAL MATCH (c)-[:MENTIONS]->(e)
            WITH cid, c, collect(DISTINCT {id: coalesce(e.id, e.name, e.uuid), label: head(labels(e))}) AS ents
            RETURN
              cid AS chunk_id,
              c IS NOT NULL AS found,
              size(ents) AS mentions_count,
              ents[0..$limit] AS sample_entities
            """
            rows = neo4j_read(q_check, {"chunk_ids": chunk_ids, "limit": int(limit)})
            out["checks"] = rows
            print("\n[NEO4J] Seed chunk_id checks:")
            for r in rows:
                print(
                    f"  {r['chunk_id']}: found={r['found']} mentions={r['mentions_count']}"
                    f" sample_ents={r['sample_entities']}"
                )

    except Exception as e:
        print(f"[NEO4J : ERROR] neo4j_print_basics failed: {e}")

    return out


@costing_query_pipeline_bp.route("/query", methods=["GET", "POST"])
def query():
    """
    RAG-based query:
    1) Embed the query
    2) Retrieve Pinecone top_k matches (dense + sparse)
    3) Retrieve Neo4j subgraph around best-matching concepts
    4) Run cost estimator on the returned subgraph (optional params)
    """

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
    entity_names = list(data.get("entity_names", request.args.getlist("entity_names", [])))
    
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
        matches = pinecone_query(query_text, top_k=top_k, namespace=namespace, score_cutoff=0.33)

        # chunk_ids = _extract_chunk_ids(matches)
        chunk_ids = matches.get("chunk_ids", [])

        # neo4j_print_basics(chunk_ids=chunk_ids, limit=5)

        graph = {}
        costing = {}

        # ------------>
        graph = neo4j_fetch_graph_around_chunks_with_filtering(
            chunk_matches=matches,  # <— pass the whole object
            graph_nodes=graph_nodes,
            graph_hops=graph_hops,
            min_score=0.25,  # optional score filter
            entity_names=entity_names
        )

        # normalize to {nodes, relationships} for consistency with docs/UI
        if "edges" in graph and "relationships" not in graph:
            graph = {
                "nodes": graph.get("nodes", []),
                "relationships": [
                    {
                        "type": e.get("type"),
                        "start": e.get("source"),
                        "end": e.get("target"),
                        "properties": e.get("properties", {}),
                    }
                    for e in graph.get("edges", [])
                ],
            }

        # print("[DEBUG] Neo4j graph retrieval complete")
        # # de-dupe any fan-outs from Cypher or client merges
        # graph = _dedupe_graph_payload(graph)

        # # 3) Cost estimation on the subgraph
        # costing = estimate_cost(graph, params=cost_params) if include_costing else None
        # <------------
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
    print(f"[QUERY] fetching entities of type: {entity_type}")
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
