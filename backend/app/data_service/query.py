from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from .config import NEO4J_CONFIG, NODE_TYPES, EDGE_TYPES
import pprint
import ast
import os
import re
try:
    import google.generativeai as genai
except Exception:
    genai = None
pp = pprint.PrettyPrinter(indent=2)
uri = NEO4J_CONFIG["uri"]
username = NEO4J_CONFIG["auth"][0]
password = NEO4J_CONFIG["auth"][1]
driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(username, password))


def nodes(node_type=None, limit=100):
    print(f"DEBUG: Fetching nodes of type '{node_type}' with limit {limit}")
    try:
        with driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE $node_type IS NULL OR $node_type IN labels(n)
            RETURN { id: elementId(n), labels: labels(n), properties: n } AS n
            LIMIT $limit
            """
            res = session.run(cypher, node_type=node_type, limit=limit)
            # Consume once; cursor is exhausted after this
            rows = res.data()
            return [row["n"] for row in rows]
    except ServiceUnavailable as e:
        print(f"Neo4j connection error: {e}")
        return []
    except Neo4jError as e:
        print(f"Cypher query error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in nodes query: {e}")
        return []


def edges(edge_type=None, limit=100):
    try:
        with driver.session() as session:
            cypher = f"MATCH (a)-[r{':' + edge_type if edge_type else ''}]->(b) RETURN a, r, b LIMIT $limit"
            result = session.run(cypher, limit=limit)
            rows = result.data()
            return [
                {"from": record["a"], "edge": record["r"], "to": record["b"]}
                for record in rows
            ]
    except ServiceUnavailable as e:
        print(f"Neo4j connection error: {e}")
        return []
    except Neo4jError as e:
        print(f"Cypher query error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in edges query: {e}")
        return []


def create_d3_graph(node_records, edge_records):
    import re
    from flask import request, jsonify

    def slugify(s: str) -> str:
        s = (s or "").strip()
        s = s.lower()
        s = re.sub(r"[\s/|]+", "_", s)
        s = re.sub(r"[^a-z0-9:_\-\.]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s or "unnamed"

    # map primary label → prefix used in D3 ids
    PREFIX = {
        "Document": "doc",
        "Scenario": "scn",
        "Equipment": "equip",
        "Material": "mat",
        "Process": "proc",
        "Workspace": "loc",
        "Project": "proj",
    }

    def pick_label(labels, fallback_label=None, category=None):
        # prefer first label; else fallback to provided label; else infer from category; else "Node"
        if labels and len(labels) > 0:
            return labels[0]
        if fallback_label:
            return fallback_label
        if category:
            # very light mapping from your sample categories
            cat_map = {
                "project_scenario": "Scenario",
                "crusher": "Equipment",
                "ore": "Material",
                "location": "Workspace",
            }
            return cat_map.get(category, "Node")
        return "Node"

    def make_d3_id(obj) -> str:
        """
        Accepts either a node from node_records:
            { "id": "...", "labels":[...], "properties": {...} }
        or an inline node-like dict from edges:
            { "label": "...", "category": "...", "id": "...", "name": "...", ... }
        Returns something like "equip:jaw_crusher".
        """
        labels = None
        props = {}

        if "labels" in obj and "properties" in obj:
            labels = obj.get("labels") or []
            props = obj.get("properties") or {}
            lbl = pick_label(labels, category=props.get("category"))
            base = props.get("id") or props.get("name") or obj.get("id")
        else:
            # inline edge node case
            lbl = pick_label(
                None, fallback_label=obj.get("label"), category=obj.get("category")
            )
            base = obj.get("id") or obj.get("name")

        prefix = PREFIX.get(lbl, slugify(lbl) or "node")
        return f"{prefix}:{slugify(str(base))}" if base else f"{prefix}:{slugify(lbl)}"

    try:
        # node_limit = int(request.args.get("node_limit", 1000))
        # edge_limit = int(request.args.get("edge_limit", 1000))
        # node_records = nodes(limit=node_limit)
        # edge_records = edges(limit=edge_limit)

        # ---- Build D3 nodes (dedupe + merge) -------------------------------
        d3_nodes_map = {}

        def merge_props(a: dict, b: dict) -> dict:
            # shallow union, b wins on conflicts
            out = dict(a or {})
            out.update(b or {})
            return out

        for n in node_records:
            d3_id = make_d3_id(n)
            labels = n.get("labels") or []
            props = n.get("properties") or {}

            if d3_id in d3_nodes_map:
                # merge labels + properties
                existing = d3_nodes_map[d3_id]
                merged_labels = sorted(set(list(existing.get("labels", [])) + labels))
                merged_props = merge_props(existing.get("properties", {}), props)
                d3_nodes_map[d3_id].update(
                    {"labels": merged_labels, "properties": merged_props}
                )
            else:
                d3_nodes_map[d3_id] = {
                    "id": d3_id,
                    "labels": labels,
                    "properties": props,
                }

        # ---- Build D3 links -----------------------------------------------
        d3_links = []

        for e in edge_records:
            rel_type = None
            props = e.get("properties", {}) if isinstance(e, dict) else {}

            if (
                isinstance(e, dict)
                and "edge" in e
                and isinstance(e["edge"], list)
                and len(e["edge"]) == 3
            ):
                # shape: { edge: [ fromNode, "RELTYPE", toNode ], from: {...}, to: {...} }
                src_obj, rel_type, tgt_obj = e["edge"]
                src_id = make_d3_id(src_obj)
                tgt_id = make_d3_id(tgt_obj)
                # ensure nodes exist even if they weren't in node_records
                d3_nodes_map.setdefault(
                    src_id,
                    {
                        "id": src_id,
                        "labels": [
                            pick_label(
                                None,
                                fallback_label=src_obj.get("label"),
                                category=src_obj.get("category"),
                            )
                        ],
                        "properties": {
                            k: v for k, v in src_obj.items() if k not in ("label",)
                        },
                    },
                )
                d3_nodes_map.setdefault(
                    tgt_id,
                    {
                        "id": tgt_id,
                        "labels": [
                            pick_label(
                                None,
                                fallback_label=tgt_obj.get("label"),
                                category=tgt_obj.get("category"),
                            )
                        ],
                        "properties": {
                            k: v for k, v in tgt_obj.items() if k not in ("label",)
                        },
                    },
                )
                d3_links.append(
                    {
                        "source": src_id,
                        "target": tgt_id,
                        "type": rel_type,
                        "properties": props or {},
                    }
                )
            else:
                # pp.pprint(f"edge: {e.get("edge")}")
                # more generic fallback: expect keys {from, to, type}
                src_obj = e.get("from") or e.get("source") or {}
                tgt_obj = e.get("to") or e.get("target") or {}
                edge = e.get("edge") or {}
                if isinstance(edge, tuple) and len(edge) > 1:
                    relation = edge[1]
                else:
                    relation = "RELATED"  # or some default value
                rel_type = relation
                if not src_obj or not tgt_obj:
                    continue
                src_id = make_d3_id(src_obj)
                tgt_id = make_d3_id(tgt_obj)

                d3_nodes_map.setdefault(
                    src_id,
                    {
                        "id": src_id,
                        "labels": [
                            pick_label(
                                None,
                                fallback_label=src_obj.get("label"),
                                category=src_obj.get("category"),
                            )
                        ],
                        "properties": {
                            k: v for k, v in src_obj.items() if k not in ("label",)
                        },
                    },
                )
                d3_nodes_map.setdefault(
                    tgt_id,
                    {
                        "id": tgt_id,
                        "labels": [
                            pick_label(
                                None,
                                fallback_label=tgt_obj.get("label"),
                                category=tgt_obj.get("category"),
                            )
                        ],
                        "properties": {
                            k: v for k, v in tgt_obj.items() if k not in ("label",)
                        },
                    },
                )

                d3_links.append(
                    {
                        "source": src_id,
                        "target": tgt_id,
                        "type": rel_type,
                        "properties": e.get("properties", {}) or {},
                    }
                )

        # ---- Return in D3 format ------------------------------------------
        d3_graph = {
            "nodes": list(d3_nodes_map.values()),
            "links": d3_links,
        }
        print(f"[DEBUG] Created D3 graph with {len(d3_graph['nodes'])} nodes and {len(d3_graph['links'])} links")
        return d3_graph

    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/graph: {e}"}), 500

GEMINI_MODEL_ID = "gemini-2.5-pro"  # keep consistent with ingest_langex.py

def _cypher_is_read_only(cypher: str) -> bool:
    """Very small guard to avoid accidental writes."""
    banned = r"\b(CREATE|MERGE|DELETE|SET|DROP|REMOVE|LOAD\s+CSV|CALL\s+dbms\.)\b"
    return not re.search(banned, cypher, flags=re.IGNORECASE)

def _extract_cypher(text: str) -> str:
    """Extract cypher from LLM output. Supports ```cypher ...``` or raw string."""
    if not text:
        return ""
    m = re.search(r"```(?:cypher|CYPHER)?\s*(.*?)```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    # fallback: take first semicolon-terminated statement
    parts = [p.strip() for p in text.split(";") if p.strip()]
    return (parts[0] + ";") if parts else text.strip()

def _build_prompt(question: str) -> str:
    return f"""
You are a helpful assistant that translates natural language questions into READ-ONLY Cypher (Neo4j 5.x).
Return ONLY a Cypher query, nothing else, ideally wrapped in a fenced code block ```cypher ...```.
Never use CREATE/MERGE/SET/DELETE or modify data.

Graph ontology (labels and relationship types):
- Node labels: {', '.join(NODE_TYPES)}
- Relationship types: {', '.join(EDGE_TYPES)}

Guidelines:
- Prefer returning both nodes and relationships when appropriate.
- Include useful properties in the RETURN (e.g., id(n) or elementId(n), labels(n), and properties(n)).
- Use OPTIONAL MATCH when the question may not require strict existence.
- If the question mentions "costs" or "cost", consider properties like cost_value, annual_op_cost, cost_basis.
- Limit results to a reasonable default, e.g., LIMIT 100.

Examples:
-- Q: "list all equipment"
RETURN: ```cypher
MATCH (e:Equipment)
RETURN elementId(e) AS id, labels(e) AS labels, e AS properties
LIMIT 100
```
-- Q: "costs of all equipments"
RETURN: ```cypher
MATCH (e:Equipment)
RETURN elementId(e) AS id, labels(e) AS labels,
       {name: e.name, annual_op_cost: e.annual_op_cost, cost_value: e.cost_value, currency: e.currency} AS properties
LIMIT 100
```

Now generate the Cypher for:
Q: "{question}"
"""

def create_neo4j_query(question: str):
    """
    Generate a Cypher query with Gemini, execute it against Neo4j, and return both
    the Cypher and the result rows.
    """
    if not isinstance(question, str) or not question.strip():
        return {"error": "Question must be a non-empty string"}, 400

    api_key = os.getenv("GEMINI_API_KEY")
    cypher = None

    try:
        if genai is None or not api_key:
            raise RuntimeError("Gemini SDK or API key not available")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL_ID)
        prompt = _build_prompt(question.strip())
        resp = model.generate_content(prompt)
        text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if getattr(resp, "candidates", None) else "")
        cypher = _extract_cypher(text)
    except Exception as e:
        # Fall back to a generic read-only query if LLM fails
        cypher = "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, n AS properties LIMIT 50"
        print(f"[WARN] Gemini generation failed: {e}. Using fallback Cypher.")

    if not cypher:
        cypher = "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, n AS properties LIMIT 50"

    # Safety check
    if not _cypher_is_read_only(cypher):
        print(f"[WARN] Blocked non-read-only Cypher generated: {cypher}")
        return {"error": "Generated query attempted to modify data"}, 400

    # Execute against Neo4j
    try:
        with driver.session() as session:
            rows = session.run(cypher).data()
        return {"cypher": cypher, "rows": rows}
    except ServiceUnavailable as e:
        return {"error": f"Neo4j connection error: {e}"}, 500
    except Neo4jError as e:
        return {"error": f"Cypher execution error: {e}", "cypher": cypher}, 400
    except Exception as e:
        return {"error": f"Unexpected error executing Cypher: {e}", "cypher": cypher}, 500