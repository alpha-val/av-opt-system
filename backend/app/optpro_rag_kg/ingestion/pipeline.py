from typing import Dict, Any, List
from .pdf_parser import parse_pdf
from .chunker import chunk_text
from .chunking_adapter import extract_chunks_from_pdf_bytes
from .normalize import normalize_payload

# from .extract_ner_rel import extract_entities, extract_relations
from ..stores.vector_store import VectorStore
from ..stores.neo4j_store import Neo4jStore
from ..utils.logging import get_logger

log = get_logger(__name__)

class IngestionPipeline:
    def __init__(self, vs: VectorStore, kg: Neo4jStore):
        self.vs = vs
        self.kg = kg

    def ingest_document(
        self, doc_id: str, pdf_bytes: bytes, filename: str
    ) -> Dict[str, Any]:
        # 1) Extract chunks from PDF bytes
        chunks = chunk_text(pdf_bytes=pdf_bytes, doc_id=doc_id, title=filename)

        # 2) Normalize metadata (convert to compatible format)
        for c in chunks:
            # Ensure metadata is not empty and convert values to strings
            c["metadata"] = {
                k: str(v) if v is not None else "" for k, v in c["metadata"].items()
            }
            # Add default metadata if empty
            if not c["metadata"]:
                c["metadata"] = {"title": c["title"]}

        # 3) Upsert vectors (dense + optional sparse)
        self.vs.upsert(
            [
                {
                    "id": c["id"],
                    "text": c["text"],
                    "doc_id": c["doc_id"],
                    "section_id": c["section_id"],
                    "title": c["title"],
                    "page_start": c["page_start"],
                    "page_end": c["page_end"],
                    # "standard_units": c["metadata"],  # Ensure metadata is compatible
                    "cost_curated": False,
                    "text": c["text"]
                }
                for c in chunks
            ]
        )

        # 4) Write minimal KG (sections mention entities)
        for c in chunks:
            if c["entity_ids"]:
                self.kg.upsert_section_mentions(
                    c["doc_id"], c["section_id"], c["title"], c["entity_ids"]
                )
        for c in chunks:
            log.info(f"\t [CHUNK_TEXT] {c['text']}")

        return chunks
