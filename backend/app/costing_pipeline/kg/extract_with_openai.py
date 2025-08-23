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

import re

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
        original_to_uuid[n.get("id", "")] = new_id  # keep for edge remap if present
        n["id"] = new_id  # overwrite any model id
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


# def openai_extract_nodes_rels_mentions(
#     chunks: List[Dict[str, Any]],
# ) -> Dict[str, List[Dict[str, Any]]]:
#     """
#     2. Run the function-calling LLM on each chunk.
#     3. Merge & de-dupe nodes / edges across chunks.
#     4. Also produce Chunk->MENTIONS for Neo4j upsert.
#     """

#     # NOTE: assumes SETTINGS, TOOLS, ont, ChatOpenAI, NAMESPACE, gen_prompt are already defined in your module.

#     print("====================================================")
#     print("[DEBUG] Starting text ingestion with chunking and MENTIONS...")
#     print("====================================================")
#     # ── 1. Prep the LLM with tools ──────────────────────────
#     llm = ChatOpenAI(
#         model="gpt-4o-mini",
#         api_key=SETTINGS.openai_api_key,
#         temperature=0,
#         timeout=60,
#         model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
#     )

#     # ── helpers kept local to minimize file changes ─────────
#     _ALLOWED_LABELS = {
#         "Equipment",
#         "Process",
#         "Material",
#         "Scenario",
#         "Project",
#         "Entity",
#     }

#     def _node_name(n: dict) -> str:
#         props = n.get("properties", {}) or {}
#         return (
#             props.get("surface")
#             or props.get("name")
#             or props.get("title")
#             or props.get("text")
#             or ""
#         ).strip()

#     def _node_label(n: dict, default="Entity") -> str:
#         raw = (n.get("type") or n.get("label") or n.get("category") or default).strip()
#         aliases = {
#             "equip": "Equipment",
#             "equipment": "Equipment",
#             "process": "Process",
#             "proc": "Process",
#             "material": "Material",
#             "mat": "Material",
#             "scenario": "Scenario",
#             "project": "Project",
#             "entity": "Entity",
#             "thing": "Entity",
#         }
#         lbl = aliases.get(raw.lower(), raw.title())
#         return lbl if lbl in _ALLOWED_LABELS else "Entity"

#     def canonical_key(n: dict) -> str:
#         props = n.get("properties", {}) or {}
#         name = (props.get("name") or props.get("surface") or "").strip().lower()
#         orig = (props.get("original_id") or n.get("id") or "").strip().lower()
#         typ = (n.get("type") or n.get("label") or "").strip().lower()
#         return f"{typ}|{name}|{orig}"

#     def _find_spans(text: str, needle: str) -> List[Tuple[int, int, str]]:
#         if not text or not needle:
#             return []
#         out: List[Tuple[int, int, str]] = []
#         # Exact (case-insensitive)
#         for m in re.finditer(re.escape(needle), text, flags=re.IGNORECASE):
#             out.append((m.start(), m.end(), text[m.start() : m.end()]))
#         if out:
#             return out
#         # Flexible hyphen/space variants
#         toks = [t for t in re.split(r"\s+", needle.strip()) if t]
#         if not toks:
#             return out
#         pat = r"(?:" + r"[\s\-]+".join(map(re.escape, toks)) + r")"
#         for m in re.finditer(pat, text, flags=re.IGNORECASE):
#             out.append((m.start(), m.end(), text[m.start() : m.end()]))
#         return out

#     # ── 2. Normalize chunks up-front (ids + minimal fields) ─
#     out_chunks: List[Dict[str, Any]] = []
#     chunk_id_by_index: Dict[int, str] = {}
#     for i, ch in enumerate(chunks):
#         raw_text = ch.get("text", "") or ""
#         cid = (
#             ch.get("chunk_id")
#             or ch.get("id")
#             or str(
#                 uuid.uuid5(
#                     NAMESPACE,
#                     f"chunk|{i}|{ch.get('page')}|{raw_text[:128]}",
#                 )
#             )
#         )
#         # hard guarantee: never None/empty chunk_id
#         if not cid:
#             cid = str(uuid.uuid4())
#         out_chunks.append(
#             {
#                 "chunk_id": cid,
#                 "seq": ch.get("seq", i),
#                 "text": raw_text,
#                 "page": ch.get("page"),
#                 "pinecone_id": ch.get("pinecone_id"),
#                 "namespace": ch.get("namespace"),
#             }
#         )
#         chunk_id_by_index[i] = cid

#     # ── 3. Iterate through chunks & collect calls + raw mentions ─
#     all_nodes, all_edges = [], []
#     all_mentions_tmp = []  # will store with 'entity_key' then remap to final entity_id
#     user_prompt = gen_prompt(ontology=ont)
#     SYSTEM_PROMPT = SystemMessage(content=(user_prompt))

#     for idx, chunk in enumerate(out_chunks):
#         text = chunk.get("text", "")
#         if not text.strip():
#             print(f"[DEBUG] ⇒ Skipping empty chunk {idx+1}/{len(out_chunks)} …")
#             continue
#         print(f"[DEBUG] ⇒ Processing chunk {idx+1}/{len(out_chunks)} …")
#         messages = [SYSTEM_PROMPT, HumanMessage(content=text)]
#         resp = llm.invoke(messages)

#         # Accumulate tool outputs
#         for call in resp.additional_kwargs.get("tool_calls", []):
#             fn = call.get("function", {})
#             name = fn.get("name")
#             payload = json.loads(fn.get("arguments", "{}"))
#             if name == "extract_nodes":
#                 nodes = payload.get("nodes", []) or []
#                 all_nodes.extend(nodes)

#                 # --- build raw mentions for this chunk directly from nodes ---
#                 for n in nodes:
#                     surface = _node_name(n)
#                     if not surface:
#                         continue
#                     spans = _find_spans(text, surface)
#                     label = _node_label(n)
#                     key = canonical_key(n)
#                     if spans:
#                         for s, e, matched in spans:
#                             all_mentions_tmp.append(
#                                 {
#                                     "chunk_id": chunk["chunk_id"],
#                                     "entity_key": key,  # temp; will map to final id later
#                                     "entity_label": label,
#                                     "span_start": s,
#                                     "span_end": e,
#                                     "surface": matched,
#                                     "conf": (n.get("properties", {}) or {}).get(
#                                         "confidence"
#                                     ),
#                                 }
#                             )
#                     else:
#                         # allow span-less mention for provenance
#                         all_mentions_tmp.append(
#                             {
#                                 "chunk_id": chunk["chunk_id"],
#                                 "entity_key": key,
#                                 "entity_label": label,
#                                 "span_start": None,
#                                 "span_end": None,
#                                 "surface": surface,
#                                 "conf": (n.get("properties", {}) or {}).get(
#                                     "confidence"
#                                 ),
#                             }
#                         )

#             elif name == "extract_edges":
#                 all_edges.extend(payload.get("edges", []) or [])
#     # --- 4. Normalize nodes, UUID5, de-dupe; build key->uuid map ----
#     original_to_uuid = {}
#     key_to_uuid = {}
#     normalized_nodes = []
#     for n in all_nodes:
#         key = canonical_key(n)
#         new_id = str(uuid.uuid5(NAMESPACE, key))
#         key_to_uuid[key] = new_id
#         if n.get("id"):
#             original_to_uuid[n["id"]] = new_id  # keep for edge remap if present
#         n["id"] = new_id  # overwrite any model id
#         n.setdefault("properties", {})["canonical_key"] = key
#         normalized_nodes.append(n)

#     # DEDUPE AFTER assigning UUID5
#     by_id = {}
#     for n in normalized_nodes:
#         nid = n["id"]
#         if nid in by_id:
#             by_id[nid]["properties"].update(n.get("properties", {}))
#         else:
#             by_id[nid] = n
#     all_nodes = list(by_id.values())

#     try:
#         # Remap edges to the new ids (works even if model omitted id entirely)
#         unique_edges = []
#         seen_edges = set()
#         for e in all_edges:
#             if e.get("source") in original_to_uuid:
#                 e["source"] = original_to_uuid[e["source"]]
#             if e.get("target") in original_to_uuid:
#                 e["target"] = original_to_uuid[e["target"]]
#             tup = (e.get("source"), e.get("target"), e.get("type"))
#             if None in tup or e.get("source") == e.get("target"):
#                 continue
#             if tup in seen_edges:
#                 continue
#             seen_edges.add(tup)
#             unique_edges.append(e)
#         all_edges = unique_edges
#     except Exception as e:
#         print("[ERROR] Failed to remap edges:", e)

#     # --- 5. Finalize mentions: map entity_key -> entity_id, clean, de-dupe ----
#     try:
#         final_mentions = []
#         seen_m = set()
#         valid_chunk_ids = {c["chunk_id"] for c in out_chunks if c.get("chunk_id")}
#         for m in all_mentions_tmp:
#             ent_id = key_to_uuid.get(m["entity_key"])
#             if not ent_id:
#                 continue
#             # enforce valid chunk + normalize label once more
#             c_id = m.get("chunk_id")
#             if not c_id or c_id not in valid_chunk_ids:
#                 continue
#             e_label = m.get("entity_label") or "Entity"
#             e_label = e_label if e_label in _ALLOWED_LABELS else "Entity"

#             rec = {
#                 "chunk_id": c_id,
#                 "entity_id": ent_id,
#                 "entity_label": e_label,
#                 "span_start": m.get("span_start"),
#                 "span_end": m.get("span_end"),
#                 "surface": m.get("surface"),
#                 "conf": m.get("conf"),
#             }
#             sig = (rec["chunk_id"], rec["entity_id"], rec["span_start"], rec["span_end"])
#             if sig in seen_m:
#                 continue
#             seen_m.add(sig)
#             final_mentions.append(rec)

#     except Exception as e:
#         print("[ERROR] Failed to process mentions:", e)

#     # Last uniqueness guard
#     all_nodes = list({n["id"]: n for n in all_nodes}.values())
#     print(f"Nodes >\n {len(all_nodes)} : \n{all_nodes}")
#     print(f"Edges >\n {len(all_edges)} : \n{all_edges}")
#     print(f"Chunks >\n {len(out_chunks)} : \n{out_chunks}")
#     print(f"Mentions >\n {len(final_mentions)} : \n{final_mentions}")
#     return {
#         "nodes": all_nodes,
#         "edges": all_edges,
#         # for Chunk + MENTIONS upsert
#         "chunks": out_chunks,
#         "mentions": final_mentions,
#     }


def openai_extract_nodes_rels_mentions(
    chunks: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    2. Run the function-calling LLM on each chunk.
    3. Merge & de-dupe nodes / edges across chunks.
    4. Also produce Chunk->MENTIONS for Neo4j upsert.
    """

    # NOTE: assumes SETTINGS, TOOLS, ont, ChatOpenAI, NAMESPACE, gen_prompt are already defined in your module.

    print("====================================================")
    print("[DEBUG] Starting text ingestion with chunking and MENTIONS...")
    print("====================================================")
    # ── 1. Prep the LLM with tools ──────────────────────────
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SETTINGS.openai_api_key,
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    # ── helpers kept local to minimize file changes ─────────
    _ALLOWED_LABELS = {
        "Equipment",
        "Process",
        "Material",
        "Scenario",
        "Project",
        "Entity",
    }

    def _node_name(n: dict) -> str:
        props = n.get("properties", {}) or {}
        return (
            props.get("surface")
            or props.get("name")
            or props.get("title")
            or props.get("text")
            or ""
        ).strip()

    def _node_label(n: dict, default="Entity") -> str:
        raw = (n.get("type") or n.get("label") or n.get("category") or default).strip()
        aliases = {
            "equip": "Equipment",
            "equipment": "Equipment",
            "process": "Process",
            "proc": "Process",
            "material": "Material",
            "mat": "Material",
            "scenario": "Scenario",
            "project": "Project",
            "entity": "Entity",
            "thing": "Entity",
        }
        lbl = aliases.get(raw.lower(), raw.title())
        return lbl if lbl in _ALLOWED_LABELS else "Entity"

    def canonical_key(n: dict) -> str:
        props = n.get("properties", {}) or {}
        name = (props.get("name") or props.get("surface") or "").strip().lower()
        orig = (props.get("original_id") or n.get("id") or "").strip().lower()
        typ = (n.get("type") or n.get("label") or "").strip().lower()
        return f"{typ}|{name}|{orig}"

    def _find_spans(text: str, needle: str) -> List[Tuple[int, int, str]]:
        if not text or not needle:
            return []
        out: List[Tuple[int, int, str]] = []
        # Exact (case-insensitive)
        for m in re.finditer(re.escape(needle), text, flags=re.IGNORECASE):
            out.append((m.start(), m.end(), text[m.start() : m.end()]))
        if out:
            return out
        # Flexible hyphen/space variants
        toks = [t for t in re.split(r"\s+", needle.strip()) if t]
        if not toks:
            return out
        pat = r"(?:" + r"[\s\-]+".join(map(re.escape, toks)) + r")"
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            out.append((m.start(), m.end(), text[m.start() : m.end()]))
        return out

    # ── 2. Normalize chunks up-front (ids + minimal fields) ─
    out_chunks: List[Dict[str, Any]] = []
    chunk_id_by_index: Dict[int, str] = {}
    for i, ch in enumerate(chunks):
        raw_text = ch.get("text", "") or ""
        cid = (
            ch.get("chunk_id")
            or ch.get("id")
            or str(
                uuid.uuid5(
                    NAMESPACE,
                    f"chunk|{i}|{ch.get('page')}|{raw_text[:128]}",
                )
            )
        )
        # hard guarantee: never None/empty chunk_id
        if not cid:
            cid = str(uuid.uuid4())
        out_chunks.append(
            {
                "chunk_id": cid,
                "seq": ch.get("seq", i),
                "text": raw_text,
                "page": ch.get("page"),
                "pinecone_id": ch.get("pinecone_id"),
                "namespace": ch.get("namespace"),
            }
        )
        chunk_id_by_index[i] = cid

    # ── 3. Iterate through chunks & collect calls + raw mentions ─
    all_nodes, all_edges = [], []
    all_mentions_tmp = []  # will store with 'entity_key' then remap to final entity_id
    user_prompt = gen_prompt(ontology=ont)
    SYSTEM_PROMPT = SystemMessage(content=(user_prompt))

    for idx, chunk in enumerate(out_chunks):
        text = chunk.get("text", "")
        if not text.strip():
            print(f"[DEBUG] ⇒ Skipping empty chunk {idx+1}/{len(out_chunks)} …")
            continue
        print(f"[DEBUG] ⇒ Processing chunk {idx+1}/{len(out_chunks)} …")
        messages = [SYSTEM_PROMPT, HumanMessage(content=text)]
        resp = llm.invoke(messages)

        # Accumulate tool outputs
        for call in resp.additional_kwargs.get("tool_calls", []):
            fn = call.get("function", {})
            name = fn.get("name")
            payload = json.loads(fn.get("arguments", "{}"))
            if name == "extract_nodes":
                nodes = payload.get("nodes", []) or []
                all_nodes.extend(nodes)

                # --- build raw mentions for this chunk directly from nodes ---
                for n in nodes:
                    surface = _node_name(n)
                    if not surface:
                        continue
                    spans = _find_spans(text, surface)
                    label = _node_label(n)
                    key = canonical_key(n)
                    if spans:
                        for s, e, matched in spans:
                            all_mentions_tmp.append(
                                {
                                    "chunk_id": chunk["chunk_id"],
                                    "entity_key": key,  # temp; will map to final id later
                                    "entity_label": label,
                                    "span_start": s,
                                    "span_end": e,
                                    "surface": matched,
                                    "conf": (n.get("properties", {}) or {}).get(
                                        "confidence"
                                    ),
                                }
                            )
                    else:
                        # allow span-less mention for provenance
                        all_mentions_tmp.append(
                            {
                                "chunk_id": chunk["chunk_id"],
                                "entity_key": key,
                                "entity_label": label,
                                "span_start": None,
                                "span_end": None,
                                "surface": surface,
                                "conf": (n.get("properties", {}) or {}).get(
                                    "confidence"
                                ),
                            }
                        )

            elif name == "extract_edges":
                all_edges.extend(payload.get("edges", []) or [])
    # --- 4. Normalize nodes, UUID5, de-dupe; build key->uuid map ----
    original_to_uuid = {}
    key_to_uuid = {}
    normalized_nodes = []
    for n in all_nodes:
        key = canonical_key(n)
        new_id = str(uuid.uuid5(NAMESPACE, key))
        key_to_uuid[key] = new_id
        if n.get("id"):
            original_to_uuid[n["id"]] = new_id  # keep for edge remap if present
        n["id"] = new_id  # overwrite any model id
        n.setdefault("properties", {})["canonical_key"] = key
        normalized_nodes.append(n)

    # DEDUPE AFTER assigning UUID5
    by_id = {}
    for n in normalized_nodes:
        nid = n["id"]
        if nid in by_id:
            by_id[nid]["properties"].update(n.get("properties", {}))
        else:
            by_id[nid] = n
    all_nodes = list(by_id.values())

    try:
        # Remap edges to the new ids (works even if model omitted id entirely)
        unique_edges = []
        seen_edges = set()
        for e in all_edges:
            if e.get("source") in original_to_uuid:
                e["source"] = original_to_uuid[e["source"]]
            if e.get("target") in original_to_uuid:
                e["target"] = original_to_uuid[e["target"]]
            tup = (e.get("source"), e.get("target"), e.get("type"))
            if None in tup or e.get("source") == e.get("target"):
                continue
            if tup in seen_edges:
                continue
            seen_edges.add(tup)
            unique_edges.append(e)
        all_edges = unique_edges
    except Exception as e:
        print("[ERROR] Failed to remap edges:", e)

    # --- 5. Finalize mentions: map entity_key -> entity_id, clean, de-dupe ----
    final_mentions = []  # ensure defined even if try fails
    try:
        seen_m = set()
        valid_chunk_ids = {c["chunk_id"] for c in out_chunks if c.get("chunk_id")}
        for m in all_mentions_tmp:
            ent_id = key_to_uuid.get(m["entity_key"])
            if not ent_id:
                continue
            # enforce valid chunk + normalize label once more
            c_id = m.get("chunk_id")
            if not c_id or c_id not in valid_chunk_ids:
                continue
            e_label = m.get("entity_label") or "Entity"
            e_label = e_label if e_label in _ALLOWED_LABELS else "Entity"

            rec = {
                "chunk_id": c_id,
                "entity_id": ent_id,
                "entity_label": e_label,
                "span_start": m.get("span_start"),
                "span_end": m.get("span_end"),
                "surface": m.get("surface"),
                "conf": m.get("conf"),
            }
            sig = (
                rec["chunk_id"],
                rec["entity_id"],
                rec["span_start"],
                rec["span_end"],
            )
            if sig in seen_m:
                continue
            seen_m.add(sig)
            final_mentions.append(rec)
    except Exception as e:
        print("[ERROR] Failed to process mentions:", e)

    # ── 6. Merge: add Chunk nodes and MENTIONS edges ─────────
    # Build Chunk nodes
    chunk_nodes = []
    for c in out_chunks:
        if not c.get("chunk_id"):
            continue
        chunk_nodes.append(
            {
                "id": c["chunk_id"],
                "type": "Chunk",
                "properties": {
                    "text": c.get("text", ""),
                    "seq": c.get("seq"),
                    "page": c.get("page"),
                    "pinecone_id": c.get("pinecone_id"),
                    "namespace": c.get("namespace"),
                },
            }
        )

    # Build MENTIONS edges (Chunk -> Entity)
    mention_edges = []
    for m in final_mentions:
        mention_edges.append(
            {
                "source": m["chunk_id"],
                "target": m["entity_id"],
                "type": "MENTIONS",
                "properties": {
                    "start": m.get("span_start"),
                    "end": m.get("span_end"),
                    "surface": m.get("surface"),
                    "confidence": m.get("conf"),
                },
            }
        )

    # Merge nodes (dedupe by id; merge properties)
    merged_by_id = {n["id"]: n for n in all_nodes if n.get("id")}
    for n in chunk_nodes:
        nid = n["id"]
        if nid in merged_by_id:
            merged_by_id[nid].setdefault("properties", {}).update(
                n.get("properties", {}) or {}
            )
            # prefer existing type; if missing, set it
            if not merged_by_id[nid].get("type"):
                merged_by_id[nid]["type"] = n.get("type")
        else:
            n.setdefault("properties", {})
            merged_by_id[nid] = n
    merged_nodes = list(merged_by_id.values())

    # Merge edges (dedupe by (source,target,type))
    merged_edges = []
    seen_e = set()
    for e in all_edges + mention_edges:
        src, tgt, typ = e.get("source"), e.get("target"), e.get("type")
        if not src or not tgt or not typ:
            continue
        sig = (src, tgt, typ)
        if sig in seen_e:
            continue
        seen_e.add(sig)
        e.setdefault("properties", {})
        merged_edges.append(e)

    # # Debug
    # print(f"Nodes > {len(merged_nodes)}")
    # print(f"Edges > {len(merged_edges)}")

    return {
        "nodes": merged_nodes,
        "edges": merged_edges,
    }


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
