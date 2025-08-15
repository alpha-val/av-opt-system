from __future__ import annotations
import os
import json
import logging
import pprint
import uuid
from collections import OrderedDict

# from langchain_community.graphs import Node, Relationship
from typing import Dict, List, Any, Union, Tuple
from .build_prompt import gen_prompt
from .ontology import load_ontology
from ..config_adapter import SETTINGS
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument

# ------------------------------------------------------------------ #
# Logging                                                            #
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("graph_ingest")

ont = load_ontology()
# ------------------------------------------------------------------ #
# OpenAI function‑calling schemas                                    #
# ------------------------------------------------------------------ #
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
                                "type": {"type": "string", "enum": ont["NODE_TYPES"]},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"}
                                        for p in ont["NODE_PROPERTIES"]
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["type"],
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
                                "type": {"type": "string", "enum": ont["EDGE_TYPES"]},
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        p: {"type": "string"}
                                        for p in ont["EDGE_PROPERTIES"]
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


# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #
def _to_document(payload: Union[str, bytes]) -> Document:
    """Normalise text / bytes to a langchain Document."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    elif isinstance(payload, str):
        text = payload
    else:
        raise TypeError(f"Unsupported type {type(payload)} – expected str or bytes.")
    return Document(page_content=text, metadata={"source": "graph_ingest"})


def _dedupe(seq: List[Dict[str, Any]], key: str = "id") -> List[Dict[str, Any]]:
    """Order‑preserving deduplication by `key`."""
    od = OrderedDict()
    for item in seq:
        od[item[key]] = item
    return list(od.values())


pp = pprint.PrettyPrinter(indent=1)

# ------------------- sanitiser utilities -------------------
import json
from typing import Any, Iterable

_PRIMITIVES: tuple[type, ...] = (str, int, float, bool, type(None))


def _sanitize(v: Any) -> Any:
    if isinstance(v, _PRIMITIVES):
        return v
    if isinstance(v, Iterable) and not isinstance(v, (str, bytes, dict)):
        return [_sanitize(x) for x in v]  # recurse into lists
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)  # stringify nested map
    return str(v)


def clean_props(d: dict) -> dict:
    return {k: _sanitize(v) for k, v in d.items()}


@staticmethod
def _to_document(payload: Union[str, bytes]) -> Document:
    """Normalise text / bytes to a langchain Document."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    elif isinstance(payload, str):
        text = payload
    else:
        raise TypeError(f"Unsupported type {type(payload)} – expected str or bytes.")
    return Document(page_content=text, metadata={"source": "graph_ingest"})


NAMESPACE = uuid.UUID("6d978d8b-9e1b-4d3e-9f0a-2cfd5f9a9d9a")  # any constant


def openai_extract_nodes_rels(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    2. Run the function-calling LLM on each chunk.
    3. Merge & de-dupe nodes / edges across chunks.
    4. Ingest a single GraphDocument into Neo4j.
    """
    print("====================================================")
    print("[DEBUG] Starting text ingestion with chunking...")
    print("====================================================")

    # ── 1. Prep the LLM with tools ──────────────────────────
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SETTINGS.openai_api_key,
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    # ── 2. Iterate through chunks & collect calls ───────────
    all_nodes, all_edges, all_mentions = [], [], []

    user_prompt = gen_prompt(ontology=ont)
    # print("[DEBUG] Using user prompt:", user_prompt)
    SYSTEM_PROMPT = SystemMessage(content=(user_prompt))
    input_text = ""
    for idx, chunk in enumerate(chunks):
        text = chunk.get("text", "")
        if not text.strip():
            print(f"[DEBUG] ⇒ Skipping empty chunk {idx+1}/{len(chunks)} …")
            continue
        print(f"[DEBUG] ⇒ Processing chunk {idx+1}/{len(chunks)} …")
        input_text += text
        messages = [SYSTEM_PROMPT, HumanMessage(content=text)]
        resp = llm.invoke(messages)

        for call in resp.additional_kwargs.get("tool_calls", []):
            fn = call.get("function", {})
            name = fn.get("name")
            payload = json.loads(fn.get("arguments", "{}"))
            if name == "extract_nodes":
                all_nodes.extend(payload.get("nodes", []))
            elif name == "extract_edges":
                all_edges.extend(payload.get("edges", []))

    # --- 3. Normalize, generate UUID5, then DEDUPE by new id -----------------
    def canonical_key(n: dict) -> str:
        name = (n.get("properties", {}).get("name") or "").strip().lower()
        orig = (
            (n.get("properties", {}).get("original_id") or n.get("id") or "")
            .strip()
            .lower()
        )
        typ = (n.get("type") or "").strip().lower()
        return f"{typ}|{name}|{orig}"

    original_to_uuid = {}
    normalized_nodes = []
    for n in all_nodes:
        key = canonical_key(n)
        new_id = str(uuid.uuid5(NAMESPACE, key))
        original_to_uuid[n.get("id","")] = new_id  # keep for edge remap if present
        n["id"] = new_id                           # overwrite any model id
        n.setdefault("properties", {})["canonical_key"] = key
        normalized_nodes.append(n)

    # DEDUPE AFTER assigning UUID5
    by_id = {}
    for n in normalized_nodes:
        nid = n["id"]
        # Merge properties if you see dupes
        if nid in by_id:
            by_id[nid]["properties"].update(n.get("properties", {}))
            # (optional) keep the longest short_description, etc.
        else:
            by_id[nid] = n
    all_nodes = list(by_id.values())

    # Remap edges to the new ids (works even if model omitted id entirely)
    for e in all_edges:
        if e.get("source") in original_to_uuid:
            e["source"] = original_to_uuid[e["source"]]
        if e.get("target") in original_to_uuid:
            e["target"] = original_to_uuid[e["target"]]

    # coalesce exact duplicate edges by (source,target,type)
    seen_edges = set()
    unique_edges = []
    for e in all_edges:
        tup = (e.get("source"), e.get("target"), e.get("type"))
        if None in tup or tup in seen_edges or e["source"] == e["target"]:
            continue
        seen_edges.add(tup)
        unique_edges.append(e)
    all_edges = unique_edges

    # If anything slipped, enforce uniqueness one last time
    all_nodes = {n["id"]: n for n in all_nodes}.values()

    return {"nodes": all_nodes, "edges": all_edges}


def openai_extract_graph_doc(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    2. Run the function-calling LLM on each chunk.
    3. Merge & de-dupe nodes / edges across chunks.
    4. Ingest a single GraphDocument into Neo4j.
    """
    print("====================================================")
    print("[DEBUG] Starting text ingestion with chunking...")
    print("====================================================")

    # ── 1. Prep the LLM with tools ──────────────────────────
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SETTINGS.openai_api_key,
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    # ── 2. Iterate through chunks & collect calls ───────────
    all_nodes, all_edges, all_mentions = [], [], []

    user_prompt = gen_prompt(ontology=ont)
    # print("[DEBUG] Using user prompt:", user_prompt)
    SYSTEM_PROMPT = SystemMessage(content=(user_prompt))
    input_text = ""
    for idx, chunk in enumerate(chunks):
        text = chunk.get("text", "")
        if not text.strip():
            print(f"[DEBUG] ⇒ Skipping empty chunk {idx+1}/{len(chunks)} …")
            continue
        # print(f"[DEBUG] ⇒ Processing chunk {idx+1}/{len(chunks)} …")
        # print(f"[DEBUG] ⇒ Chunk text: {text}")
        input_text += text
        messages = [SYSTEM_PROMPT, HumanMessage(content=text)]
        resp = llm.invoke(messages)

        for call in resp.additional_kwargs.get("tool_calls", []):
            fn = call.get("function", {})
            name = fn.get("name")
            payload = json.loads(fn.get("arguments", "{}"))
            if name == "extract_nodes":
                all_nodes.extend(payload.get("nodes", []))
            elif name == "extract_edges":
                all_edges.extend(payload.get("edges", []))

    # print("[DEBUG] ⇒ Finished processing chunks")
    # ── 3. De-dupe & normalize ──────────────────────────────
    all_nodes = _dedupe(all_nodes, key="id")

    def canonical_key(n: dict) -> str:
        name = (n.get("properties", {}).get("name") or "").strip().lower()
        orig = (
            (n.get("properties", {}).get("original_id") or n.get("id") or "")
            .strip()
            .lower()
        )
        typ = (n.get("type") or "").strip().lower()
        return f"{typ}|{name}|{orig}"

    original_to_uuid = {}
    for n in all_nodes:
        key = canonical_key(n)
        new_id = str(uuid.uuid5(NAMESPACE, key))
        original_to_uuid[n["id"]] = new_id
        n["id"] = new_id
        n.setdefault("properties", {})["canonical_key"] = key
    # Update relationships to use the new UUIDs
    for e in all_edges:
        if e["source"] in original_to_uuid:
            e["source"] = original_to_uuid[e["source"]]  # Replace source ID with UUID
        if e["target"] in original_to_uuid:
            e["target"] = original_to_uuid[e["target"]]  # Replace target ID with UUID

    # # Debugging output
    # print("[DEBUG] ⇒ Updated nodes with UUIDs:")
    # for n in all_nodes:
    #     print(f"Node: {n}")

    # print("[DEBUG] ⇒ Updated relationships with UUIDs:")
    # for e in all_edges:
    #     print(f"Relationship: {e}")

    # Convert nodes to Neo4j format
    nodes_neo = [
        Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
        for n in all_nodes
    ]
    # print(f"[DEBUG] nodes_neo: {nodes_neo}")

    # Convert relationships to Neo4j format
    id_to_type = {n["id"]: n["type"] for n in all_nodes}

    def _safe_node(node_id: str) -> Node | None:
        label = id_to_type.get(node_id)
        return Node(id=node_id, type=label, properties={}) if label else None

    rels_neo = []
    for e in all_edges:
        if e["source"] == e["target"]:
            continue
        s = _safe_node(e["source"])
        t = _safe_node(e["target"])
        if not s or not t:
            # log and skip instead of inventing placeholders
            # print(f"[WARN] dropping edge {e['type']} because endpoint missing: {e}")
            continue
        rels_neo.append(
            Relationship(
                source=s, target=t, type=e["type"], properties=e.get("properties", {})
            )
        )  # print(f"[DEBUG] rels_neo: {rels_neo}")

    graph_doc = GraphDocument(
        nodes=nodes_neo,
        relationships=rels_neo,
        source=_to_document(input_text),
    )
    # print("= = = = = = =")
    # print(f"{graph_doc}")
    print("[DEBUG] done  <  < < < ")
    return graph_doc
