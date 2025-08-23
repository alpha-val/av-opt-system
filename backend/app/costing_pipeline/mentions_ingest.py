# === Inline helpers to add (:Chunk)-[:MENTIONS]->(:Entity) edges ===
# Requires: from neo4j import Driver  (you likely already import this)

from typing import Dict, Any, List, Optional
from neo4j import Driver

def ensure_schema(driver: Driver):
    """One-time safe bootstrapping; call once at startup."""
    with driver.session() as s:
        s.run("""
        CREATE CONSTRAINT chunk_id IF NOT EXISTS
        FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
        """)
        s.run("""
        CREATE CONSTRAINT doc_id IF NOT EXISTS
        FOR (d:Document) REQUIRE d.doc_id IS UNIQUE
        """)
        # Optional: uniqueness by id for your common entity labels
        for lab in ["Equipment", "Process", "Material", "Vendor"]:
            s.run(f"""
            CREATE CONSTRAINT entity_id_{lab} IF NOT EXISTS
            FOR (e:{lab}) REQUIRE e.id IS UNIQUE
            """)

def _tx_upsert_chunk_and_doc(tx, chunk: Dict[str, Any]):
    """
    Upserts :Chunk and links it to :Document.
    'chunk' must contain at least: chunk_id, doc_id, text
    Optional: doc_title, section, page, version, source, embedding_id
    """
    tx.run(
        """
        MERGE (c:Chunk {chunk_id: $chunk_id})
          SET c.text        = $text,
              c.doc_id      = $doc_id,
              c.section     = $section,
              c.page        = $page,
              c.version     = $version,
              c.source      = $source,
              c.embedding_id= $embedding_id,
              c.updated_at  = datetime()
          ON CREATE SET c.created_at = datetime()
        WITH c
        MERGE (d:Document {doc_id: $doc_id})
          ON CREATE SET d.title = $doc_title, d.created_at = datetime()
          ON MATCH  SET d.title = coalesce($doc_title, d.title)
        MERGE (c)-[:IN_DOC]->(d)
        """,
        **{
            "chunk_id":      chunk.get("chunk_id"),
            "text":          chunk.get("text"),
            "doc_id":        chunk.get("doc_id"),
            "doc_title":     chunk.get("doc_title"),
            "section":       chunk.get("section"),
            "page":          chunk.get("page"),
            "version":       chunk.get("version"),
            "source":        chunk.get("source"),
            "embedding_id":  chunk.get("embedding_id"),
        }
    )

def _tx_link_mentions(tx, chunk_id: str, entities: List[Dict[str, Any]]):
    """
    Creates (:Chunk {chunk_id})-[:MENTIONS]->(:EntityLabel) edges.
    Each entity dict should have:
      - 'type' (label, e.g. 'Equipment' | 'Process' | 'Material' | 'Vendor' | ...)
      - one of: 'id' or 'name' (if you have a canonical ID, prefer it)
      - optional: 'weight', 'confidence', 'start', 'end'
    """
    tx.run(
        """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        WITH c, $entities AS ents
        UNWIND ents AS ent
        WITH c, ent,
             CASE WHEN ent.type IS NULL OR ent.type = '' THEN 'Entity' ELSE ent.type END AS typ
        CALL apoc.merge.node([typ],
          CASE WHEN ent.id IS NOT NULL THEN {id: ent.id} ELSE {name: ent.name} END,
          CASE WHEN ent.id IS NOT NULL THEN {name: ent.name} ELSE {} END
        ) YIELD node AS e
        MERGE (c)-[r:MENTIONS]->(e)
          SET r.weight     = coalesce(ent.weight, 1.0),
              r.confidence = coalesce(ent.confidence, 1.0),
              r.start      = ent.start,
              r.end        = ent.end
        """,
        chunk_id=chunk_id,
        entities=entities or []
    )

def ingest_chunk_with_mentions(
    driver: Driver,
    chunk: Dict[str, Any],
    entities: List[Dict[str, Any]],
    use_next_link: bool = False,
    prev_chunk_id: Optional[str] = None
) -> None:
    """Convenience wrapper: upsert chunk + link :MENTIONS (+ optional [:NEXT])."""
    with driver.session() as s:
        s.execute_write(_tx_upsert_chunk_and_doc, chunk)
        s.execute_write(_tx_link_mentions, chunk.get("chunk_id"), entities)
        if use_next_link and prev_chunk_id:
            s.run(
                """
                MATCH (p:Chunk {chunk_id:$prev}), (n:Chunk {chunk_id:$curr})
                MERGE (p)-[:NEXT]->(n)
                """,
                prev=prev_chunk_id,
                curr=chunk.get("chunk_id")
            )
