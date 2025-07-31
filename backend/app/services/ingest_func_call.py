from __future__ import annotations
import json
import pprint
from typing import List, Dict, Any
from collections import OrderedDict
from .prompt_engine import build_extraction_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument

from ..config import (
    NODE_TYPES,
    EDGE_TYPES,
    NEO4J_CONFIG,
    NODE_PROPERTIES,
    EDGE_PROPERTIES,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_nodes",
            "description": "Extract nodes from the text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string", "enum": NODE_TYPES},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"} for p in NODE_PROPERTIES
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["id", "type"],
                        },
                    }
                },
                "required": ["nodes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_edges",
            "description": "Extract relationships between nodes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "edges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "type": {"type": "string", "enum": EDGE_TYPES},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"} for p in EDGE_PROPERTIES
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["source", "target", "type"],
                        },
                    }
                },
                "required": ["edges"],
            },
        },
    },
]

pp = pprint.PrettyPrinter(indent=1)


def reset_neo4j_graph(neo_graph: Neo4jGraph, full_wipe: bool = True):
    """Reset the Neo4j graph."""
    if full_wipe:
        neo_graph.query("MATCH (n) DETACH DELETE n")
    return


def dedupe(seq: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """De-duplicate a list of dictionaries by a specific key."""
    seen = OrderedDict()
    for item in seq:
        seen[item[key]] = item
    return list(seen.values())


def ingest_doc_func_call(
    text: str, llm: ChatOpenAI | None = None, full_wipe: bool = False
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract nodes and edges from input text using OpenAI function-calling,
    and return Neo4j-compatible dictionaries for each.
    """
    llm = llm or ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    # user_prompt = build_extraction_prompt()
    user_prompt = """Get all nodes and relationships from user's text."""
    messages = [
        SystemMessage(content=user_prompt),
        HumanMessage(content=text),
    ]

    response = llm.invoke(messages)
    all_nodes, all_edges = [], []
    tool_calls = response.additional_kwargs.get("tool_calls", [])

    for call in tool_calls:
        fn = call.get("function", {})
        tool_name = fn.get("name")
        try:
            arguments = json.loads(fn.get("arguments", "{}"))
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode arguments for {tool_name}: {e}")
            continue

        if tool_name == "extract_nodes":
            all_nodes.extend(arguments.get("nodes", []))
        elif tool_name == "extract_edges":
            all_edges.extend(arguments.get("edges", []))

    print("> > > DEBUG: Tool Calls Response")
    pp.pprint(tool_calls)
    print("> > > DEBUG: All Nodes with IDs")
    pp.pprint(all_nodes)
    # ── 3. De-dupe & normalize ──────────────────────────────

    def _dedupe(seq: List[Dict[str, Any]], key: str = "id") -> List[Dict[str, Any]]:
        """Order‑preserving deduplication by `key`."""
        od = OrderedDict()
        for item in seq:
            od[item[key]] = item
        return list(od.values())

    all_nodes = _dedupe(all_nodes, key="id")

    nodes_neo = [
        Node(
            id=n["id"].lower().replace(" ", "_"),
            type=n["type"],
            properties={**n.get("properties", {}), "name": n["id"]},
        )
        for n in all_nodes
    ]

    # ---------------- lookup table of known node-id → label -----------------
    id_to_type = {n["id"]: n["type"] for n in all_nodes}

    def _safe_node(node_id: str) -> Node:
        label = id_to_type.get(node_id) or "Placeholder"  # never ""
        return Node(id=node_id, type=label, properties={})

    print("! ! DEBUG: All Nodes ! !")
    pp.pprint(nodes_neo)
    # ---------------- build relationships safely ----------------------------
    rels_neo = [
        Relationship(
            source=_safe_node(e["source"]),
            target=_safe_node(e["target"]),
            type=e["type"],
            properties=e.get("properties", {}),
        )
        for e in all_edges
        if e["source"] != e["target"]
    ]

    # ---------------- ensure placeholders are present in the node list ------
    for rel in rels_neo:
        for endpoint in (rel.source, rel.target):
            if endpoint.id not in id_to_type:
                nodes_neo.append(endpoint)  # adds the placeholder once
                id_to_type[endpoint.id] = endpoint.type

    print("! ! DEBUG: All Relationships ! !")
    pp.pprint(all_edges)
    # rels_neo = [
    #     Relationship(
    #         source=Node(id=e["source"], type="", properties={}),
    #         target=Node(id=e["target"], type="", properties={}),
    #         type=e["type"],
    #         properties=e.get("properties", {}),
    #     )
    #     for e in raw_edges if e["source"] != e["target"]
    # ]

    neo_graph = Neo4jGraph(
        url=NEO4J_CONFIG["uri"],
        username=NEO4J_CONFIG["auth"][0],
        password=NEO4J_CONFIG["auth"][1],
    )
    graph_doc = GraphDocument(
        nodes=nodes_neo,
        relationships=rels_neo,
        source=Document(page_content=text, metadata={"id": "generated-by-llm"}),
    )
    reset_neo4j_graph(neo_graph, full_wipe=full_wipe)

    print("! ! DEBUG: All Nodes ! !")
    pp.pprint(all_nodes)

    neo_graph.add_graph_documents([graph_doc])

    return {"nodes": nodes_neo, "relationships": rels_neo}
