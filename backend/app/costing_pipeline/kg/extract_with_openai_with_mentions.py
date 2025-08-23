# ─────────────────────────────────────────────────────────────────────────────
# Version that ALSO writes (:Chunk)-[:MENTIONS]->(:Entity) per chunk
# ─────────────────────────────────────────────────────────────────────────────
from typing import Dict, Any, List, Optional
import json, uuid
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from neo4j import GraphDatabase
from ..config_adapter import SETTINGS
from .ontology import load_ontology
from .build_prompt import gen_prompt
ont = load_ontology()
# Your existing imports / config
# from config_adapter import SETTINGS
# from ontology import ont
# from build_prompt import gen_prompt, TOOLS
# from pipeline import ingest_chunk_with_mentions   # if you inlined helpers into pipeline.py
from ..mentions_ingest import (
    ingest_chunk_with_mentions,
)  # if you kept helpers in a separate file

NAMESPACE = uuid.UUID(
    "5d3cbf2b-7fce-4f6f-8f35-4c0b3b8f5c55"
)  # stable UUID5 namespace for ids

# Map model "type" strings to your Neo4j labels (adjust as your ontology requires)
ENTITY_LABELS = {
    "equipment": "Equipment",
    "process": "Process",
    "material": "Material",
    "vendor": "Vendor",
    # add more if your tool outputs others (e.g., "process_unit" -> "ProcessUnit")
}

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

def _node_to_entity_payload(n: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert one extracted node into an entity dict expected by ingest_chunk_with_mentions.
    Returns None if this node shouldn't create a :MENTIONS edge.
    """
    typ_raw = (n.get("type") or "").strip()
    typ = ENTITY_LABELS.get(typ_raw.lower())
    if not typ:
        return None  # skip non-entity nodes (e.g., Document, Project if not desired)

    props = n.get("properties", {}) or {}
    # Prefer a canonical id if the model provided one; otherwise fall back to name-only merge.
    ent_id = (props.get("id") or props.get("original_id") or "").strip() or None
    name = (props.get("name") or "").strip() or None
    if not (ent_id or name):
        return None

    # Optional scoring/offsets if present in your tool outputs
    weight = props.get("weight") or 1.0
    confidence = props.get("confidence") or 1.0
    start = props.get("start")
    end = props.get("end")

    return {
        "type": typ,
        "id": ent_id,
        "name": name,
        "weight": (
            float(weight)
            if isinstance(weight, (int, float, str))
            and str(weight).replace(".", "", 1).isdigit()
            else 1.0
        ),
        "confidence": (
            float(confidence)
            if isinstance(confidence, (int, float, str))
            and str(confidence).replace(".", "", 1).isdigit()
            else 1.0
        ),
        "start": start,
        "end": end,
    }


def openai_extract_nodes_rels_and_ingest_mentions(
    chunks: List[Dict[str, Any]],
    use_next_links: bool = True,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Same as your current 'openai_extract_nodes_rels', but:
      • runs the LLM on each chunk,
      • merges/dedupes nodes/edges across chunks,
      • AND (critically) calls ingest_chunk_with_mentions(...) per chunk
        to store (:Chunk)-[:MENTIONS]->(:EntityLabel) in Neo4j.

    Returns the merged {'nodes': [...], 'edges': [...]} for any downstream uses you already have.
    """
    print("====================================================")
    print("[DEBUG] Starting text ingestion with chunking (+MENTIONS)…")
    print("====================================================")

    # 1) Prep LLM + tools (same as your current version)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SETTINGS.openai_api_key,
        temperature=0,
        timeout=60,
        model_kwargs={"tools": TOOLS, "tool_choice": "auto"},
    )

    all_nodes: List[Dict[str, Any]] = []
    all_edges: List[Dict[str, Any]] = []

    user_prompt = gen_prompt(ontology=ont)
    SYSTEM_PROMPT = SystemMessage(content=user_prompt)

    prev_chunk_id: Optional[str] = None

    for idx, chunk in enumerate(chunks):
        text = chunk.get("text", "") or ""
        if not text.strip():
            print(f"[DEBUG] ⇒ Skipping empty chunk {idx+1}/{len(chunks)} …")
            continue

        print(
            f"[DEBUG] ⇒ Processing chunk {idx+1}/{len(chunks)} (chunk_id={chunk.get('chunk_id')}) …"
        )
        messages = [SYSTEM_PROMPT, HumanMessage(content=text)]
        resp = llm.invoke(messages)

        # 2) Collect tool calls (same as before)
        nodes_this_chunk: List[Dict[str, Any]] = []
        edges_this_chunk: List[Dict[str, Any]] = []

        for call in resp.additional_kwargs.get("tool_calls", []):
            fn = call.get("function", {})
            name = fn.get("name")
            payload = json.loads(fn.get("arguments", "{}"))
            if name == "extract_nodes":
                nodes_this_chunk.extend(payload.get("nodes", []))
            elif name == "extract_edges":
                edges_this_chunk.extend(payload.get("edges", []))

        # Accumulate for global graph doc de-dupe later
        all_nodes.extend(nodes_this_chunk)
        all_edges.extend(edges_this_chunk)

        # 3) Build entities for this chunk and write :MENTIONS
        entities_payload = []
        for n in nodes_this_chunk:
            ent = _node_to_entity_payload(n)
            if ent:
                entities_payload.append(ent)

        if entities_payload:
            neo4j_driver = GraphDatabase.driver(
                SETTINGS.neo4j_uri, auth=(SETTINGS.neo4j_user, SETTINGS.neo4j_password)
            )

            try:
                ingest_chunk_with_mentions(
                    neo4j_driver,
                    chunk,
                    entities_payload,
                    use_next_link=use_next_links,
                    prev_chunk_id=prev_chunk_id,
                )
            except Exception as e:
                # Don't fail the whole ingestion if one chunk's write has an issue
                print(
                    f"[WARN] Failed to write :MENTIONS for chunk_id={chunk.get('chunk_id')}: {e}"
                )

        prev_chunk_id = chunk.get("chunk_id") if use_next_links else prev_chunk_id

    # 4) Normalize + UUID5 + DEDUPE nodes (same as your original)
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
        original_to_uuid[n.get("id", "")] = new_id
        n["id"] = new_id
        n.setdefault("properties", {})["canonical_key"] = key
        normalized_nodes.append(n)

    by_id = {}
    for n in normalized_nodes:
        nid = n["id"]
        if nid in by_id:
            by_id[nid]["properties"].update(n.get("properties", {}))
        else:
            by_id[nid] = n
    all_nodes = list(by_id.values())

    # Remap edges to new ids & coalesce duplicates
    remapped_edges = []
    seen = set()
    for e in all_edges:
        src = original_to_uuid.get(e.get("source"), e.get("source"))
        tgt = original_to_uuid.get(e.get("target"), e.get("target"))
        typ = e.get("type")
        if not src or not tgt or src == tgt:
            continue
        key = (src, tgt, typ)
        if key in seen:
            continue
        seen.add(key)
        remapped = dict(e)
        remapped["source"] = src
        remapped["target"] = tgt
        remapped_edges.append(remapped)
    all_edges = remapped_edges

    return {"nodes": all_nodes, "edges": all_edges}
