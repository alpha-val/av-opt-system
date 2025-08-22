# graph_endpoints.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from typing import Any, List, Dict

# Reuse your existing config + driver
from ..config_adapter import SETTINGS

graph_query_bp = Blueprint("graph_query_bp", __name__, url_prefix="/graph/v1")

uri = SETTINGS.neo4j_uri
username = SETTINGS.neo4j_user
password = SETTINGS.neo4j_password
driver = GraphDatabase.driver(uri, auth=(username, password))
print(f"Driver : {driver}")

def _int(v, default):
    try:
        return int(v)
    except Exception:
        return default


def _clean_label(lbl: str | None) -> str | None:
    if not lbl:
        return None
    lbl = lbl.strip()
    return lbl if lbl.replace("_", "").isalnum() and lbl[0].isalpha() else None


# ---------- /nodes ----------
@graph_query_bp.route("/nodes", methods=["GET", "POST"])
def api_nodes():
    """
    Retrieve nodes; optional type filter and text filter.
    Params (GET or POST JSON):
      - type: optional node label (must match your labels)
      - q:    optional text filter (name/short_description/description/canonical_key)
      - limit: int (default 100, max 1000)
    """
    data = request.get_json(silent=True) or {}
    node_type = _clean_label(data.get("type") or request.args.get("type"))
    q = (data.get("q") or request.args.get("q") or "").strip().lower()
    limit = _int(data.get("limit", request.args.get("limit", 100)), 100)
    limit = max(1, min(1000, limit))

    try:
        with driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE ($node_type IS NULL OR $node_type IN labels(n))
              AND (
                $q = '' OR
                toLower(coalesce(n.name, ''))              CONTAINS $q OR
                toLower(coalesce(n.short_description, '')) CONTAINS $q OR
                toLower(coalesce(n.description, ''))       CONTAINS $q OR
                toLower(coalesce(n.canonical_key, ''))     CONTAINS $q
              )
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
            LIMIT $limit
            """
            rows = session.run(cypher, node_type=node_type, q=q, limit=limit).data()

        # JSON-serializable nodes
        items = [
            {"id": r["id"], "labels": r["labels"], "properties": r["props"]}
            for r in rows
        ]
        return jsonify({"ok": True, "count": len(items), "items": items}), 200

    except (ServiceUnavailable, Neo4jError) as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- /edges ----------
@graph_query_bp.route("/edges", methods=["GET", "POST"])
def api_edges():
    """
    Retrieve edges; optional type filter and endpoint type filters.
    Params (GET or POST JSON):
      - type: optional relationship type (must match your EDGE_TYPES)
      - from_type: optional source node label
      - to_type:   optional target node label
      - limit: int (default 100, max 1000)
    """
    data = request.get_json(silent=True) or {}
    rel_type = (data.get("type") or request.args.get("type") or "").strip()
    from_type = _clean_label(data.get("from_type") or request.args.get("from_type"))
    to_type = _clean_label(data.get("to_type") or request.args.get("to_type"))
    limit = _int(data.get("limit", request.args.get("limit", 100)), 100)
    limit = max(1, min(1000, limit))

    # Keep it safe & dynamic without string‑building the type:
    # Filter type(r) via a WHERE clause
    try:
        with driver.session() as session:
            cypher = """
            MATCH (a)-[r]->(b)
            WHERE ($rel_type = '' OR type(r) = $rel_type)
              AND ($from_type IS NULL OR $from_type IN labels(a))
              AND ($to_type   IS NULL OR $to_type   IN labels(b))
            RETURN
              elementId(a) AS a_id, labels(a) AS a_labels, properties(a) AS a_props,
              type(r)      AS r_type, properties(r) AS r_props,
              elementId(b) AS b_id, labels(b) AS b_labels, properties(b) AS b_props
            LIMIT $limit
            """
            rows = session.run(
                cypher,
                rel_type=rel_type,
                from_type=from_type,
                to_type=to_type,
                limit=limit,
            ).data()

        items = []
        for r in rows:
            items.append(
                {
                    "from": {
                        "id": r["a_id"],
                        "labels": r["a_labels"],
                        "properties": r["a_props"],
                    },
                    "edge": {"type": r["r_type"], "properties": r["r_props"]},
                    "to": {
                        "id": r["b_id"],
                        "labels": r["b_labels"],
                        "properties": r["b_props"],
                    },
                }
            )
        return jsonify({"ok": True, "count": len(items), "items": items}), 200

    except (ServiceUnavailable, Neo4jError) as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- /graph (D3 bundle of nodes+links) ----------
@graph_query_bp.route("/graph", methods=["GET", "POST"])
def api_graph_d3():
    """
    Return a compact D3 graph:
      - Node slice: optional node type + text filter
      - Edge slice: optional rel type + endpoint type filters
    Params:
      Nodes: type, q, node_limit
      Edges: type (edge), from_type, to_type, edge_limit
    """
    data = request.get_json(silent=True) or {}
    print("[DEBUG] /graph request")
    # node slice
    node_type = _clean_label(data.get("type") or request.args.get("type"))
    q = (data.get("q") or request.args.get("q") or "").strip().lower()
    node_limit = _int(data.get("node_limit", request.args.get("node_limit", 200)), 200)
    node_limit = max(1, min(2000, node_limit))
    # edge slice
    edge_type = (data.get("edge_type") or request.args.get("edge_type") or "").strip()
    from_type = _clean_label(data.get("from_type") or request.args.get("from_type"))
    to_type = _clean_label(data.get("to_type") or request.args.get("to_type"))
    edge_limit = _int(data.get("edge_limit", request.args.get("edge_limit", 500)), 500)
    edge_limit = max(1, min(5000, edge_limit))

    try:
        with driver.session() as session:
            # Nodes
            cy_nodes = """
            MATCH (n)
            WHERE ($node_type IS NULL OR $node_type IN labels(n))
              AND (
                $q = '' OR
                toLower(coalesce(n.name, ''))              CONTAINS $q OR
                toLower(coalesce(n.short_description, '')) CONTAINS $q OR
                toLower(coalesce(n.description, ''))       CONTAINS $q OR
                toLower(coalesce(n.canonical_key, ''))     CONTAINS $q
              )
            RETURN { id: elementId(n), labels: labels(n), properties: properties(n) } AS n
            LIMIT $limit
            """
            node_rows = session.run(
                cy_nodes, node_type=node_type, q=q, limit=node_limit
            ).data()
            node_records = [r["n"] for r in node_rows]

            # Edges
            cy_edges = """
            MATCH (a)-[r]->(b)
            WHERE ($edge_type = '' OR type(r) = $edge_type)
              AND ($from_type IS NULL OR $from_type IN labels(a))
              AND ($to_type   IS NULL OR $to_type   IN labels(b))
            RETURN
              { id: elementId(a), labels: labels(a), properties: properties(a) } AS a,
              type(r) AS reltype,
              { id: elementId(b), labels: labels(b), properties: properties(b) } AS b,
              properties(r) AS rprops
            LIMIT $limit
            """
            edge_rows = session.run(
                cy_edges,
                edge_type=edge_type,
                from_type=from_type,
                to_type=to_type,
                limit=edge_limit,
            ).data()
            edge_records = [
                {
                    "from": r["a"],
                    "edge": ["FROM", r["reltype"], "TO"],
                    "properties": r["rprops"],
                    "to": r["b"],
                }
                for r in edge_rows
            ]
        # print("------------------------------")
        # print(f"[DEBUG] nodes: {node_records}")
        # print(f"[DEBUG] edges: {edge_records}")
        # print("------------------------------")
        d3 = convert_to_d3_graph(node_records, edge_records)
        return jsonify({"ok": True, "graph": d3}), 200

    except (ServiceUnavailable, Neo4jError) as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def convert_to_d3_graph(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convert nodes and edges into D3 graph format.

    Parameters:
    ----------
    nodes : List[Dict[str, Any]]
        List of node dictionaries with id, labels, and properties.
    edges : List[Dict[str, Any]]
        List of edge dictionaries with from, to, edge type, and properties.

    Returns:
    -------
    Dict[str, Any]
        D3 graph format with nodes and links.
    """

    def ensure_serializable(obj):
        """
        Ensure all properties in the object are JSON-serializable.
        """
        if isinstance(obj, dict):
            return {
                k: (
                    str(v)
                    if not isinstance(v, (str, int, float, bool, type(None)))
                    else v
                )
                for k, v in obj.items()
            }
        return obj

    def slugify(s: str) -> str:
        """
        Create a slugified string for IDs and labels.
        """
        import re

        s = (s or "").strip().lower()
        s = re.sub(r"[\s/|]+", "_", s)
        s = re.sub(r"[^a-z0-9:_\-\.]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s or "unnamed"

    # Map primary label → prefix used in D3 IDs
    PREFIX = {
        "Document": "doc",
        "Scenario": "scn",
        "Equipment": "equip",
        "Material": "mat",
        "Process": "proc",
        "Workspace": "loc",
        "Project": "proj",
    }

    def make_d3_id(obj) -> str:
        """
        Generate a D3-compatible ID for nodes.
        """
        labels = obj.get("labels", [])
        props = obj.get("properties", {})
        label = labels[0] if labels else "Node"
        prefix = PREFIX.get(label, slugify(label))
        base = props.get("id") or props.get("name") or obj.get("id")
        return (
            f"{prefix}:{slugify(str(base))}" if base else f"{prefix}:{slugify(label)}"
        )

    # Build D3 nodes
    d3_nodes_map = {}
    for node in nodes:
        d3_id = make_d3_id(node)
        labels = node.get("labels", [])
        props = ensure_serializable(node.get("properties", {}))

        if d3_id in d3_nodes_map:
            # Merge labels and properties if the node already exists
            existing = d3_nodes_map[d3_id]
            merged_labels = sorted(set(existing.get("labels", []) + labels))
            merged_props = {**existing.get("properties", {}), **props}
            d3_nodes_map[d3_id].update(
                {"labels": merged_labels, "properties": merged_props}
            )
        else:
            d3_nodes_map[d3_id] = {"id": d3_id, "labels": labels, "properties": props}

    # Build D3 links
    d3_links = []
    for edge in edges:
        src_obj = edge.get("from", {})
        tgt_obj = edge.get("to", {})
        rel_type = (
            edge.get("edge", ["RELATED"])[1]
            if isinstance(edge.get("edge"), list)
            else "RELATED"
        )
        props = ensure_serializable(edge.get("properties", {}))

        src_id = make_d3_id(src_obj)
        tgt_id = make_d3_id(tgt_obj)

        # Ensure nodes exist even if they weren't in the node list
        d3_nodes_map.setdefault(
            src_id,
            {
                "id": src_id,
                "labels": src_obj.get("labels", []),
                "properties": ensure_serializable(src_obj.get("properties", {})),
            },
        )
        d3_nodes_map.setdefault(
            tgt_id,
            {
                "id": tgt_id,
                "labels": tgt_obj.get("labels", []),
                "properties": ensure_serializable(tgt_obj.get("properties", {})),
            },
        )

        d3_links.append(
            {"source": src_id, "target": tgt_id, "type": rel_type, "properties": props}
        )

    # Convert to D3 graph format
    return {"nodes": list(d3_nodes_map.values()), "links": d3_links}

