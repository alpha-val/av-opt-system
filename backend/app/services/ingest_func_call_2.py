from __future__ import annotations
import json
import pprint
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from .prompt_engine import build_extraction_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument
from langchain.text_splitter import CharacterTextSplitter

from ..config import (
    NODE_TYPES,
    EDGE_TYPES,
    NODE_PROPERTIES,
    EDGE_PROPERTIES,
    NEO4J_CONFIG,
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


def ingest_doc_func_call_2(
    text: str,
    llm: Optional[ChatOpenAI] = None,
    full_wipe: bool = False,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract nodes and edges from input text using OpenAI function-calling,
    splitting the document into overlapping chunks for more robust coverage.
    """
    print("[DEBUG] > > > > > Using Chunking")
    # 1) Instantiate LLM
    llm = llm or ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    # 2) Build the extraction prompt once
    # user_prompt = build_extraction_prompt()
    user_prompt = "Extract nodes and edges from the text."
    # 3) Configure and run chunking
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_text(text)
    print(f"[DEBUG] number of chunks: {len(chunks)}")

    all_nodes: List[Dict[str, Any]] = []
    all_edges: List[Dict[str, Any]] = []
    pp = pprint.PrettyPrinter(indent=2)

    # 4) Loop over each chunk and invoke the LLM
    for idx, chunk in enumerate(chunks):
        messages = [
            SystemMessage(content=user_prompt),
            HumanMessage(content=chunk),
        ]
        print(f"[DEBUG] Processing chunk {idx+1}/{len(chunks)}...")
        response = llm.invoke(messages)
        tool_calls = response.additional_kwargs.get("tool_calls", [])

        # 5) Accumulate nodes & edges from each function call
        for call in tool_calls:
            fn = call.get("function", {})
            args_str = fn.get("arguments", "{}")
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                continue
            if nodes := args.get("nodes"):
                all_nodes.extend(nodes)
            if rels := args.get("edges"):
                all_edges.extend(rels)

    # 6) Post-process combined extracts
    #    (Dedup, add placeholders, convert to Neo4j Node/Relationship objects)
    id_to_type = {n["id"]: n["type"] for n in all_nodes}
    # Convert nodes
    nodes_neo = [
        Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
        for n in all_nodes
    ]
    print(f"[DEBUG] EDGES FOUND >> ", all_edges)
    # Convert and filter edges
    rels_neo = [
        Relationship(
            source=Node(
                id=e["source"], type=id_to_type.get(e["source"], ""), properties={}
            ),
            target=Node(
                id=e["target"], type=id_to_type.get(e["target"], ""), properties={}
            ),
            type=e["type"],
            properties=e.get("properties", {}),
        )
        for e in all_edges
        if e["source"] != e["target"]
    ]
    # Ensure placeholders for missing types
    for rel in rels_neo:
        for endpoint in (rel.source, rel.target):
            if endpoint.id not in id_to_type:
                nodes_neo.append(endpoint)
                id_to_type[endpoint.id] = endpoint.type

    # 7) Ingest into Neo4j
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

    print("! ! DEBUG: Final Nodes ! !")
    pp.pprint(all_nodes)
    print("! ! DEBUG: Final Edges ! !")
    pp.pprint(all_edges)

    neo_graph.add_graph_documents([graph_doc])

    return {"nodes": nodes_neo, "relationships": rels_neo}
