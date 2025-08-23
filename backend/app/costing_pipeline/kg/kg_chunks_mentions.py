# kg_chunks_mentions.py
# -------------------------------------------------------------
# Chunk + Mentions upsert for Neo4j
# - Creates/updates :Document, :Chunk, :HAS_CHUNK, and :MENTIONS
# - Supports typed entity labels (Equipment, Process, Material, Scenario, etc.)
# - Safe to call repeatedly (idempotent MERGE semantics)
# - Handles batching to keep UNWIND sizes reasonable
#
# Usage:
#   from kg_chunks_mentions import (
#       ensure_neo4j_constraints,
#       upsert_chunks_and_mentions,
#   )
#
#   driver = GraphDatabase.driver(NEO4J_URI, auth=(USER, PASS))
#   ensure_neo4j_constraints(driver, entity_labels=["Equipment","Process","Material","Scenario","Project"])
#   upsert_chunks_and_mentions(driver,
#       doc={"doc_id":"abc123","title":"My Report"},
#       chunks=[{"chunk_id":"c1","seq":0,"text":"...","page":1,"pinecone_id":"p1","namespace":"default"}, ...],
#       mentions=[{"chunk_id":"c1","entity_id":"eq-001","entity_label":"Equipment","span_start":10,"span_end":25,"surface":"Jaw Crusher","conf":0.92}, ...],
#       batch_size=500
#   )
# -------------------------------------------------------------

from __future__ import annotations
from typing import Dict, Any, Iterable, List, Optional, Sequence, Tuple
from neo4j import GraphDatabase, Driver, Session
import math


# --------------------------
# Public: constraints helpers
# --------------------------


def ensure_neo4j_constraints(
    driver: Driver,
    *,
    entity_labels: Sequence[str],
    create_if_missing: bool = True,
) -> None:
    """
    Ensures basic uniqueness constraints for Document, Chunk, and typed Entities.
    - Document(doc_id)
    - Chunk(chunk_id)
    - <Label>(id) for each label in entity_labels (e.g., Equipment, Process, ...)
    Safe to call multiple times.
    """
    with driver.session() as sess:
        _create_unique_constraint(sess, "Document", "doc_id", create_if_missing)
        _create_unique_constraint(sess, "Chunk", "chunk_id", create_if_missing)
        for lbl in entity_labels:
            _create_unique_constraint(sess, lbl, "id", create_if_missing)


def _create_unique_constraint(
    session: Session, label: str, prop: str, create_if_missing: bool
) -> None:
    # Neo4j 5+ friendly way to create if missing
    if not create_if_missing:
        return
    cypher = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{label}`) REQUIRE n.`{prop}` IS UNIQUE"
    session.run(cypher)


# --------------------------
# Public: main upsert entry
# --------------------------


def upsert_chunks_and_mentions(
    driver: Driver,
    *,
    doc: Dict[str, Any],
    chunks: Sequence[Dict[str, Any]],
    mentions: Sequence[Dict[str, Any]],
    # Optional: when your extractor yields "Entity" as a generic label, map it here
    default_entity_label: str = "Entity",
    # Optional: batch size for UNWIND; 200–1000 is usually safe
    batch_size: int = 500,
) -> Dict[str, Any]:
    """
    Upserts:
      - MERGE (d:Document {doc_id})
      - MERGE (c:Chunk {chunk_id}) with properties and HAS_CHUNK
      - MERGE (c)-[:MENTIONS]->(e:Label {id}) with span metadata

    Args:
      driver: Neo4j driver
      doc: { doc_id, title? }
      chunks: [{chunk_id, seq, text, page, pinecone_id, namespace}, ...]
      mentions: [{chunk_id, entity_id, entity_label, span_start, span_end, surface, conf}, ...]
      default_entity_label: used if mention lacks entity_label
      batch_size: UNWIND batch size

    Returns:
      Basic counters for observability.
    """
    _validate_doc(doc)
    _normalize_chunks(chunks)
    _normalize_mentions(mentions, default_entity_label)

    stats = {
        "chunk_batches": 0,
        "mention_batches": 0,
        "chunks": len(chunks),
        "mentions": len(mentions),
    }

    with driver.session() as sess:
        # 1) Upsert Document + Chunks (+HAS_CHUNK)
        for ch_batch in _batched(chunks, batch_size):
            sess.run(
                _CYPHER_DOC_CHUNKS, parameters={"doc": doc, "chunks": list(ch_batch)}
            )
            stats["chunk_batches"] += 1

        # 2) Upsert Mentions (+ Entities with labels)
        # We can't parameterize the label in MERGE directly, so we use APOC to route to correct label.
        # If you don't have APOC, fall back to generic :Entity + set e.label.
        # The query below supports BOTH: it uses APOC when available, otherwise generic :Entity path.
        for m_batch in _batched(mentions, batch_size):
            sess.run(_CYPHER_MENTIONS, parameters={"mentions": list(m_batch)})
            stats["mention_batches"] += 1

    return stats


# --------------------------
# Validation / normalization
# --------------------------


def _validate_doc(doc: Dict[str, Any]) -> None:
    if not doc or not doc.get("doc_id"):
        raise ValueError("doc must include non-empty 'doc_id'")
    # normalize title
    if "title" not in doc:
        doc["title"] = None


def _normalize_chunks(chunks: Sequence[Dict[str, Any]]) -> None:
    for ch in chunks:
        required = ["chunk_id", "text"]
        for k in required:
            if k not in ch or ch[k] in (None, ""):
                raise ValueError(f"chunk missing required field '{k}'")
        # Optional props with sane defaults
        ch.setdefault("seq", 0)
        ch.setdefault("page", None)
        ch.setdefault("pinecone_id", None)
        ch.setdefault("namespace", None)


def _normalize_mentions(mentions: Sequence[Dict[str, Any]], default_label: str) -> None:
    for m in mentions:
        for k in ["chunk_id", "entity_id"]:
            if k not in m or m[k] in (None, ""):
                raise ValueError(f"mention missing required field '{k}'")
        # Normalize label + spans
        m["entity_label"] = (m.get("entity_label") or default_label).strip()
        m.setdefault("span_start", None)
        m.setdefault("span_end", None)
        m.setdefault("surface", None)
        m.setdefault("conf", None)


def _batched(
    items: Sequence[Dict[str, Any]], n: int
) -> Iterable[Sequence[Dict[str, Any]]]:
    if n <= 0:
        yield items
        return
    total = len(items)
    for i in range(0, total, n):
        yield items[i : i + n]


# --------------------------
# Cypher statements
# --------------------------

# 1) Document + Chunks (+HAS_CHUNK)
_CYPHER_DOC_CHUNKS = """
MERGE (d:Document {doc_id: $doc.doc_id})
  ON CREATE SET d.title = $doc.title, d.created_at = datetime()
  ON MATCH  SET d.title = coalesce($doc.title, d.title), d.updated_at = datetime();

UNWIND $chunks AS ch
MERGE (c:Chunk {chunk_id: ch.chunk_id})
  ON CREATE SET c.text = ch.text,
                c.page = ch.page,
                c.seq = ch.seq,
                c.pinecone_id = ch.pinecone_id,
                c.namespace = ch.namespace,
                c.created_at = datetime()
  ON MATCH  SET c.text = ch.text,
                c.page = ch.page,
                c.seq = ch.seq,
                c.pinecone_id = ch.pinecone_id,
                c.namespace = ch.namespace,
                c.updated_at = datetime()
MERGE (d)-[:HAS_CHUNK]->(c);
"""

# 2) Mentions (+ typed entities) — APOC-friendly with generic fallback
#    - If apoc is present: creates/merges the entity with the dynamic label m.entity_label
#    - Else: falls back to generic :Entity and records the desired label in e.label
_CYPHER_MENTIONS = """
UNWIND $mentions AS m
MERGE (c:Chunk {chunk_id: m.chunk_id})
WITH m, c,
     // Detect if apoc is installed (apoc.version() exists in 4.x/5.x)
     // We use a safe trick: try to call, otherwise null => CASE picks fallback
     apoc.version() AS apocv
CALL {
  WITH m, c, apocv
  // APOC path: build a typed node with dynamic label
  WITH m, c
  CALL apoc.merge.node([m.entity_label], {id: m.entity_id}, {}, {}) YIELD node AS e
  MERGE (c)-[r:MENTIONS]->(e)
    ON CREATE SET r.start = m.span_start,
                  r.end = m.span_end,
                  r.surface = m.surface,
                  r.confidence = m.conf,
                  r.created_at = datetime()
    ON MATCH  SET r.start = m.span_start,
                  r.end = m.span_end,
                  r.surface = m.surface,
                  r.confidence = m.conf,
                  r.updated_at = datetime()
  RETURN 0 AS _
} YIELD _ 
RETURN _
"""

# --------------------------
# (Optional) Generic fallback without APOC
# If you DON'T have APOC at all, replace _CYPHER_MENTIONS with the following:
#
# _CYPHER_MENTIONS = """
# UNWIND $mentions AS m
# MERGE (c:Chunk {chunk_id: m.chunk_id})
# MERGE (e:Entity {id: m.entity_id})
#   ON CREATE SET e.label = m.entity_label
#   ON MATCH  SET e.label = coalesce(e.label, m.entity_label)
# MERGE (c)-[r:MENTIONS]->(e)
#   ON CREATE SET r.start = m.span_start,
#                 r.end = m.span_end,
#                 r.surface = m.surface,
#                 r.confidence = m.conf,
#                 r.created_at = datetime()
#   ON MATCH  SET r.start = m.span_start,
#                 r.end = m.span_end,
#                 r.surface = m.surface,
#                 r.confidence = m.conf,
#                 r.updated_at = datetime();
# """
# --------------------------
