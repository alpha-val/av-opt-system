# extract_with_mentions.py
from __future__ import annotations
import re, uuid, json, logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

# Your existing modules
from .kg.ontology import load_ontology

DEFAULT_ONTOLOGY = load_ontology()

from .storage import (
    GNode,
    GRel,
    GDoc,
    Neo4jWriter,
    PineconeStore,
    embed_texts_dense,
    build_sparse_hybrid_vectors,
    make_namespace_from_filename,
    deterministic_uuid5,
    make_safe_ascii,
    PINECONE_INDEX,
)
from .textio import extract_text_from_pdf_stream

log = logging.getLogger(__name__)

# ==============================
# Section detection (plain text)
# ==============================


@dataclass
class Section:
    id: str
    title: str
    canon: Optional[str]
    char_start: int
    char_end: int


HEAD_RE = re.compile(r"^(?:\d+(?:\.\d+)*\s+)?([A-Z][A-Za-z0-9&/\-\s]{3,})$", re.M)
UPPER_RE = re.compile(r"^[A-Z0-9][A-Z0-9 \-,&/]{6,}$", re.M)

CANON_RULES = [
    (r"\bgeology|mineralization|litholog|stratigraph|structure\b", "geology"),
    (r"\bmining\s+method|pit\s+design|underground\b", "mining"),
    (r"\bprocessing|process\s+description|metallurgy|flowsheet\b", "processing"),
    (r"\breserves|resources|resource\s+estimate\b", "resources"),
    (r"\beinfrastructure|power|water|tailings|waste|environment\b", "infrastructure"),
    (r"\bcost|capital|operating\s+cost|economics|financial\b", "economics"),
    (r"\bintroduction|terms\s+of\s+reference|scope\b", "introduction"),
]


def _canon_for_title(title: str) -> Optional[str]:
    t = title.lower()
    for pat, canon in CANON_RULES:
        if re.search(pat, t):
            return canon
    return None


def detect_sections_from_text(text: str, doc_id: str) -> List[Section]:
    candidates = []
    for m in re.finditer(HEAD_RE, text):
        ttl = m.group(0).strip()
        if 3 <= len(ttl) <= 120:
            candidates.append((m.start(), m.end(), ttl))
    for m in re.finditer(UPPER_RE, text):
        ttl = m.group(0).strip()
        if 6 <= len(ttl) <= 120:
            candidates.append((m.start(), m.end(), ttl))
    candidates.sort(key=lambda x: x[0])

    if not candidates:
        sid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"section|{doc_id}|all|0"))
        return [
            Section(
                id=sid, title="Document", canon=None, char_start=0, char_end=len(text)
            )
        ]

    secs: List[Section] = []
    for i, (a_start, _a_end, ttl) in enumerate(candidates):
        b_start = candidates[i + 1][0] if (i + 1) < len(candidates) else len(text)
        sid = str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"section|{doc_id}|{ttl.lower()}|{a_start}")
        )
        secs.append(
            Section(
                id=sid,
                title=ttl,
                canon=_canon_for_title(ttl),
                char_start=a_start,
                char_end=b_start,
            )
        )
    return secs


# ==============================
# Chunking with provenance
# ==============================


def rechunk_with_provenance(
    text: str, sections: List[Section], chunk_size: int = 1200, chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    def _chunks():
        idx = 0
        n = len(text)
        cidx = 0
        while idx < n:
            end = min(idx + chunk_size, n)
            yield (cidx, idx, end, text[idx:end])
            if end == n:
                break
            idx = max(0, end - chunk_overlap)
            cidx += 1

    by_span = [(s.char_start, s.char_end, s) for s in sections]

    def _section_for(a: int, b: int) -> Optional[Section]:
        for sa, sb, s in by_span:
            if not (sb <= a or sa >= b):
                return s
        return None

    prov: List[Dict[str, Any]] = []
    for cidx, a, b, t in _chunks():
        sec = _section_for(a, b)
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"chunk|{a}|{cidx}"))
        prov.append(
            {
                "id": cid,
                "text": t,
                "chunk_idx": cidx,
                "char_start": a,
                "char_end": b,
                "section_id": getattr(sec, "id", None),
                "section_title": getattr(sec, "title", None),
                "section_canon": getattr(sec, "canon", None),
            }
        )
    return prov


# ==============================
# Structural graph (no :__Entity)
# ==============================


def build_structural_graph(
    doc_id: str, filename: str, sections: List[Section], chunks: List[Dict[str, Any]]
) -> GDoc:
    nodes: List[GNode] = []
    rels: List[GRel] = []

    nodes.append(
        GNode(
            id=doc_id,
            type="Document",
            properties={"filename": filename, "structural": True},
        )
    )

    for s in sections:
        nodes.append(
            GNode(
                id=s.id,
                type="Section",
                properties={
                    "title": s.title,
                    "canon": s.canon,
                    "char_start": s.char_start,
                    "char_end": s.char_end,
                    "structural": True,
                },
            )
        )
        rels.append(
            GRel(
                source=GNode(id=doc_id, type="Document", properties={}),
                target=GNode(id=s.id, type="Section", properties={}),
                type="HAS_SECTION",
                properties={},
            )
        )

    for c in chunks:
        nodes.append(
            GNode(
                id=c["id"],
                type="Chunk",
                properties={
                    "chunk_idx": c["chunk_idx"],
                    "char_start": c["char_start"],
                    "char_end": c["char_end"],
                    "section_id": c.get("section_id"),
                    "section_title": c.get("section_title"),
                    "section_canon": c.get("section_canon"),
                    "text_preview": (c.get("text") or "")[:500],
                    "structural": True,
                },
            )
        )
        if c.get("section_id"):
            rels.append(
                GRel(
                    source=GNode(id=c["section_id"], type="Section", properties={}),
                    target=GNode(id=c["id"], type="Chunk", properties={}),
                    type="HAS_CHUNK",
                    properties={},
                )
            )

    return GDoc(nodes=nodes, relationships=rels, source={"doc_id": doc_id})


# ==============================
# Mentions linking (no __Entity)
# ==============================

ENTITY_TYPES = set(DEFAULT_ONTOLOGY.get("NODE_TYPES", []))
STRUCTURAL_TYPES = {"Document", "Section", "Chunk"}
STRUCTURAL_TYPES_L = {t.lower() for t in STRUCTURAL_TYPES}
ENTITY_TYPES_L = {t.lower() for t in ENTITY_TYPES}


def _normalize_entity_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return "Other"
    r = raw.strip().lower()
    if r in STRUCTURAL_TYPES_L:
        return None  # skip structural
    for t in ENTITY_TYPES:
        if r == t.lower():
            return t
    return "Other"  # concrete but generic; never "__Entity"


def _build_lexicon(entities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    term -> {id, etype, norm}
    - etype is normalized to your ontology (no '__Entity')
    - structural types are skipped
    """
    terms: Dict[str, Dict[str, Any]] = {}
    for e in entities or []:
        etype = _normalize_entity_type(e.get("type"))
        if etype is None:
            continue
        eid = e.get("id")
        if not eid:
            continue
        props = e.get("properties", {}) or {}

        candidates: set[str] = set()
        for k in ("name", "alt_name", "model", "alias"):
            v = props.get(k)
            if isinstance(v, str) and v.strip():
                candidates.add(v.strip())
        syns = props.get("synonyms") or []
        if isinstance(syns, str):
            syns = [syns]
        for s in syns:
            if isinstance(s, str) and s.strip():
                candidates.add(s.strip())

        for c in candidates:
            terms[c.lower()] = {"id": eid, "etype": etype, "norm": c}
    return terms


def build_mentions_edges(
    chunks: List[Dict[str, Any]], entities: List[Dict[str, Any]]
) -> List[GRel]:
    """
    Create (:Chunk)-[:MENTIONS]->(:<ConcreteType>) with spans + evidence.
    - Never uses '__Entity'
    - Skips structural targets
    - Guards against missing IDs
    """
    lex = _build_lexicon(entities)
    rels: List[GRel] = []

    for c in chunks:
        text = c.get("text") or ""
        lower = text.lower()
        cid = c.get("id")
        if not cid:
            log.warning("Skipping mention creation: chunk missing id")
            continue

        for term, meta in lex.items():
            start = 0
            while True:
                i = lower.find(term, start)
                if i == -1:
                    break
                j = i + len(term)

                left_ok = (i == 0) or not lower[i - 1].isalnum()
                right_ok = (j >= len(lower)) or not lower[j : j + 1].isalnum()

                if left_ok and right_ok:
                    evidence = text[max(0, i - 60) : j + 60]
                    eid = meta.get("id")
                    etype = meta.get("etype") or "Other"
                    if not eid:
                        start = j
                        continue

                    rels.append(
                        GRel(
                            source=GNode(id=cid, type="Chunk", properties={}),
                            target=GNode(id=eid, type=etype, properties={}),
                            type="MENTIONS",
                            properties={
                                "start_char": i,
                                "end_char": j,
                                "surface": text[i:j],
                                "section_id": c.get("section_id"),
                                "section_canon": c.get("section_canon"),
                                "char_start": c.get("char_start"),
                                "char_end": c.get("char_end"),
                                "method": "lexicon_v1",
                                "confidence": 0.85,
                                "evidence": evidence,
                            },
                        )
                    )
                start = j
    return rels


# ==============================
# Merge utility
# ==============================
# Convert dicts to GNode objects
def dict_to_gnode(d):
    return GNode(id=d.get("id"), type=d.get("type"), properties=d.get("properties", {}))

def dict_to_grel(d):
    return GRel(
        source=GNode(id=d["source"], type=d.get("source_type", ""), properties={}),
        target=GNode(id=d["target"], type=d.get("target_type", ""), properties={}),
        type=d.get("type", ""),
        properties=d.get("properties", {}),
    )

def merge_graphdocs(
    base_gdoc: GDoc, extra_nodes: List[GNode], extra_rels: List[GRel]
) -> GDoc:
    node_map = {(n.id, n.type): n for n in base_gdoc.nodes}
    for n in extra_nodes:
        key = (n.id, n.type)
        if key in node_map:
            node_map[key].properties.update(n.properties or {})
        else:
            node_map[key] = n
    new_nodes = list(node_map.values())

    seen = {(r.source.id, r.target.id, r.type) for r in base_gdoc.relationships}
    new_rels = list(base_gdoc.relationships)
    for r in extra_rels:
        tup = (r.source.id, r.target.id, r.type)
        if tup in seen:
            continue
        seen.add(tup)
        new_rels.append(r)

    return GDoc(nodes=new_nodes, relationships=new_rels, source=base_gdoc.source or {})


# ==============================
# Main entrypoint (drop‑in)
# ==============================


def ingest_pdf_with_mentions(
    stream,
    writer: Neo4jWriter,
    pine: Optional[PineconeStore] = None,
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    filename: Optional[str] = None,
    # extract_graph_fn: Optional[Callable[[List[Dict[str, Any]]], GDoc]] = None,
) -> Dict[str, Any]:
    """
    Drop-in replacement for your ingestion:
      - Extracts text
      - Detects Sections
      - Chunks with provenance
      - (Optional) Upserts to Pinecone with rich metadata
      - Calls your extractor to produce domain graph (if provided or importable)
      - Builds MENTIONS and merges everything
      - Writes to Neo4j (structural nodes kept OUTSIDE :__Entity)
    """
    filename = filename or getattr(stream, "name", "uploaded.pdf")
    doc_id = f"doc|{filename}"

    # 1) text
    text = extract_text_from_pdf_stream(stream)
    print(f"[INGEST] extracted {len(text)} chars from {filename}")

    # 2) sections + chunks (provenance)
    sections = detect_sections_from_text(text, doc_id)
    prov_chunks = rechunk_with_provenance(text, sections, chunk_size, chunk_overlap)
    print(f"[INGEST] created {len(prov_chunks)} chunks (with provenance)")

    # 3) Pinecone upsert (optional)
    pine_stats = {"pinecone_upserted": 0}
    pine = PineconeStore(index_name=PINECONE_INDEX)
    if pine is not None and prov_chunks:
        texts = [c["text"] for c in prov_chunks]
        # print(f"[INGEST about to embed] embedding {len(texts)} chunks for Pinecone... {texts}")
        try:
            dense = embed_texts_dense(texts)
        except Exception:
            dense = [[0.0] * 1536 for _ in texts]
            print(f"[INGEST : dense] FALLBACK > {len(dense)} dense vectors created")
        sparse = build_sparse_hybrid_vectors(texts)
        metas = []
        for c in prov_chunks:
            vector = {
                "doc_id": doc_id,
                "filename": filename,
                "chunk_id": c["id"],
                "chunk_idx": c["chunk_idx"],
                "char_start": c["char_start"],
                "char_end": c["char_end"],
                "section_id": c.get("section_id"),
                "section_title": c.get("section_title"),
                "section_canon": c.get("section_canon") or "<none>",
                "neo4j_labels": ["Chunk"],
            }
            metas.append(vector)
        ns = "default"  # make_namespace_from_filename(filename)
        try:
            pine_stats["pinecone_upserted"] = pine.upsert_chunks(
                chunk_texts=texts,
                dense_vecs=dense,
                sparse_vecs=sparse,
                metas=metas,
                namespace=ns,
                id_prefix=f"{make_safe_ascii(doc_id)}_chunk_",
            )
            print(
                f"[INGEST] Pinecone upserted {pine_stats['pinecone_upserted']} vectors"
            )
        except Exception as e:
            print(f"[INGEST] Pinecone upsert failed: {e}")

    # 4) Extract domain KG (use your existing function if available)
    gdoc_llm: Optional[GDoc] = None

    try:
        from .kg.extract_with_openai import (
            openai_extract_nodes_rels as extract_graph_fn,
        )
    except Exception:
        extract_graph_fn = None
        print(f"[INGEST] Failed to import OpenAI extract function")
        return ({"error": "Failed to import OpenAI extract function"}), 500

    if extract_graph_fn is not None:
        print(f"[GRAPH] - building graph... 1")
        output = extract_graph_fn([{"text": c["text"]} for c in prov_chunks])
        gdoc_llm = GDoc(
            nodes=output.get("nodes", []),
            relationships=output.get("edges", []),
            source={"doc_id": doc_id},
        )
    else:
        gdoc_llm = GDoc(nodes=[], relationships=[], source={"doc_id": doc_id})
    print(f"[GRAPH] graph: {gdoc_llm}")

    # # 5) Build structural graph
    # print(f"[GRAPH] - building structural graph...")
    # gdoc_struct = build_structural_graph(doc_id, filename, sections, prov_chunks)
    # # print(f"[GRAPH] structural graph: {gdoc_struct}")

    # # 6) Collect entities from LLM graph for lexicon
    # print(f"[GRAPH] - collecting entities...")
    # entities = _collect_entities_for_lexicon(gdoc_llm)
    # print(f"[GRAPH] - collected entities: {len(entities)}")

    # # 7) Mentions'
    # print(f"[GRAPH] - building mentions edges...")
    # mentions = build_mentions_edges(prov_chunks, entities)
    # print(f"[GRAPH] - built mentions edges: {len(mentions)}")

    # # 8) Merge and write
    # print(f"[GRAPH] - converting gdoc_llm to GDoc object...")
    try:
        gdoc_llm = GDoc(
            nodes=[dict_to_gnode(n) for n in output.get("nodes", [])],
            relationships=[dict_to_grel(r) for r in output.get("edges", [])],
            source={"doc_id": doc_id},
        )
    except Exception as e:
        print(f"[ERROR] - failed to create GDoc: {e}")
        
    # print(f"[GRAPH] - writing final graph...")
    # try:
    #     final_gdoc = merge_graphdocs(
    #         base_gdoc=gdoc_llm,
    #         extra_nodes=gdoc_struct.nodes,
    #         extra_rels=gdoc_struct.relationships + mentions,
    #     )
    #     print(f"[GRAPH] - merged graph: {final_gdoc}")
    # except Exception as e:
    #     print(f"[ERROR] - failed to merge graph docs: {e}")

    # # constraints for structural nodes
    # print(f"[GRAPH] - creating constraints for structural nodes...")
    # try:
    #     with writer._driver.session() as s:
    #         s.run(
    #             "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE"
    #         )
    #         s.run(
    #             "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section)  REQUIRE s.id IS UNIQUE"
    #         )
    #         s.run(
    #             "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk)    REQUIRE c.id IS UNIQUE"
    #         )
    # except Exception as e:
    #     print(f"[ERROR] - failed to create constraints: {e}")
    final_gdoc = gdoc_llm
    print(f"[GRAPH] - writing final graph...")
    neo_stats = writer.save(final_gdoc, full_wipe=True)
    
    print(
        f"Final graph: {len(final_gdoc.nodes)} nodes, {len(final_gdoc.relationships)} relationships"
    )
    return {
        "file": filename,
        "doc_id": doc_id,
        "num_chunks": len(prov_chunks),
        "pinecone": pine_stats,
        "neo4j": neo_stats,
        "nodes": len(final_gdoc.nodes),
        "edges": len(final_gdoc.relationships),
        "sections": [s.__dict__ for s in sections],
        "chunks": [{**c, "text": (c.get("text") or "")[:180]} for c in prov_chunks],
    }


# ==============================
# Helpers
# ==============================


def _collect_entities_for_lexicon(gdoc: GDoc) -> List[Dict[str, Any]]:
    """
    From your LLM-extracted graph, collect a light entity dict for lexicon building.
    Uses ontology to decide what counts as a domain entity. Skips structural nodes.
    """
    out: List[Dict[str, Any]] = []
    entity_types_l = {t.lower() for t in ENTITY_TYPES}

    for n in getattr(gdoc, "nodes", []):
        ntype = (n.get("type") or "").strip()
        if not ntype:
            continue
        low = ntype.lower()
        if low in STRUCTURAL_TYPES_L:
            continue

        # normalize type
        if low in entity_types_l:
            tnorm = ntype[0].upper() + ntype[1:]
        else:
            tnorm = "Other"

        props = n.get("properties", {}) or {}

        out.append(
            {
                "id": n.get("id"),
                "type": tnorm,
                "properties": {
                    "name": props.get("name")
                    or props.get("model")
                    or props.get("title")
                    or "",
                    "synonyms": props.get("synonyms") or [],
                    "alt_name": props.get("alt_name") or "",
                    "alias": props.get("alias") or "",
                },
            }
        )

    return out
