"""Flask Blueprint exposing ingestion & query endpoints (router style)."""

from flask import Blueprint, request, jsonify
from ..config_adapter import SETTINGS
from ..stores.vector_store import VectorStore
from ..stores.neo4j_store import Neo4jStore
from ..ingestion.pipeline import IngestionPipeline
from ..retrieval.vector_retriever import VectorRetriever
from ..retrieval.graph_expander import GraphExpander
from ..retrieval.orchestrator import QueryOrchestrator
from ..ingestion.langextract_wrapper import extract_graph
from ..ingestion.extract_ner_rel import extract_entities_and_relations
from ..ingestion.langex_kg import KGExtractor

from ..utils.logging import get_logger
import uuid

log = get_logger(__name__)

opt_pipeline_bp = Blueprint("opt_pipeline_bp", __name__)

# Singletons for the blueprint
_vs = VectorStore()
_kg = Neo4jStore()
_ing = IngestionPipeline(_vs, _kg)
_q = QueryOrchestrator(VectorRetriever(_vs), GraphExpander(_kg))


@opt_pipeline_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@opt_pipeline_bp.route("/ingest", methods=["POST"])
def ingest():
    """
    Body:
    {
      "doc_id": "...",
      "path": "/abs/path/to/text/or/pdf",
      "title": "...",
      "enable_ner": true,                # optional: run NER pass
      "ner_mode": "full" | "light"       # optional hint forwarded to extract_ner_rel
    }
    """
    log.info("Ingesting document")

    if request.content_type and "multipart/form-data" in request.content_type.lower():
        files = request.files.getlist("files") or []
        if not files:
            return jsonify({"error": "No files uploaded"}), 400
        for f in files:
            if not f or not f.filename:
                continue
            pdf_bytes = f.read()
            doc_id = str(uuid.uuid4())
            filename = f.filename

            res = {"doc_id": doc_id, "filename": filename, "chunks": []}
            res["chunks"] = _ingest_internal(doc_id, pdf_bytes, filename)
            chunks = res.get("chunks", [])
            log.info("----->")
            # Entity and Relationships extractor
            if SETTINGS.enable_kg:
                try:
                    ner_result = None
                    ner_result = extract_entities_and_relations(chunks=chunks)

                    res["ner"] = ner_result
                except Exception as e:
                    res["ner"] = {"error": str(e)}
            else:
                res["ner"] = {"error": "NER extraction not enabled"}
            log.info("----->")
    return jsonify({"message": res}), 200


def _ingest_internal(doc_id: str, pdf_bytes: bytes, filename: str):
    return _ing.ingest_document(doc_id=doc_id, pdf_bytes=pdf_bytes, filename=filename)


def _create_kg_extraction(chunks):
    return extract_graph(neo4j=_kg, chunks=chunks)


@opt_pipeline_bp.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    q = data.get("q", "")
    params = data.get("params", {})
    top_k = int(data.get("top_k", 8))
    hop = int(data.get("hop", 2))
    res = _q.query(q, params=params, top_k=top_k, hop=hop)
    return jsonify(res), 200
