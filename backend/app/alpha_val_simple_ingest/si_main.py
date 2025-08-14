from __future__ import annotations
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import io, os, uuid
from typing import List, Dict, Any

from .config import SETTINGS
from .ingest.parsing import extract_pages_from_pdf
from .ingest.chunking import chunk_pages
from .ingest.embeddings import build_dense_embeddings, build_sparse_vectors
from .ingest.vector_store import PineconeHybridStore
from .ingest.langex_kg_extraction import KGExtractor
from .ingest.graph_store import GraphLoader
from .ingest.ontology import load_ontology
from .ingest.utils import now_iso
from .ingest.neo4j_utils import save_to_neo4j
import pprint
pp = pprint.PrettyPrinter(indent=2)
# app = Flask(__name__)
# Rename the blueprint (was "api") to avoid clash with the main API blueprint
simple_ingest_bp = Blueprint("ingest", __name__)  # unique name now


@simple_ingest_bp.get("/health")
def health():
    return {"ok": True, "ts": now_iso(), "pinecone_index": SETTINGS.pinecone_index_name}


@simple_ingest_bp.post("/ingest")
def ingest():
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Empty files list"}), 400
    # Load ontology (built-in, overridden by user config if present)
    ontology = load_ontology()
    pp.pprint(f"[DEBUG] Loaded ontology")

    # Initialize components
    vector_store = PineconeHybridStore(SETTINGS)
    kg_extractor = KGExtractor(ontology=ontology, settings=SETTINGS)
    graph_loader = GraphLoader(SETTINGS)

    summaries = []
    for f in files:
        doc_id = str(uuid.uuid4())
        print(f"* * * [DEBUG] Processing file: {f.filename} (doc_id: {doc_id})")
        filename = secure_filename(f.filename) if f.filename else f"doc_{doc_id}.pdf"
        pdf_bytes = f.read()
        pages = extract_pages_from_pdf(io.BytesIO(pdf_bytes))
        chunks = chunk_pages(doc_id, filename, pages, SETTINGS.chunk_size, SETTINGS.chunk_overlap)


        # # --- Embeddings ---
        # # Upsert to Pinecone
        # try:
        #     dense, dense_dim = build_dense_embeddings([c.text for c in chunks], SETTINGS.embed_model)
        #     print("\t[DIM] upsert dim:", dense_dim)
        #     sparse, vecorizer = build_sparse_vectors([c.text for c in chunks])  # indices + values

        #     vector_store.ensure_index(dense_dim)
        #     print(f"\t[DEBUG] Upserting chunks to Pinecone: doc ID: {doc_id}")
        #     vector_store.upsert_chunks(doc_id, chunks, dense, sparse)

        #     print("[DEBUG] Fetching stats")
        #     vector_store.fetch_stats(doc_id, dense)
        #     ###
        # except Exception as e:
        #     return jsonify({"error": "pinecone_upsert_failed", "detail": str(e)}), 400
        
        
        # --- KG Extraction ---
        create_neo4j_graph = True
        graph_docs = []
        if create_neo4j_graph:
            # Batch KG extraction across all chunks (alternative to per-chunk loop)
            try:
                graph_docs = kg_extractor.build_graph_from_chunks(
                    chunks
                )
                print("\t[DEBUG] Finished KG extraction")
            except Exception as e:
                print(f"\t[ERROR] Failed to build graph from chunks: {e}")
                return jsonify({"error": "kg_extraction_failed", "detail": str(e)}), 400
            # pp.pprint(f"[DEBUG] Graph documents: {graph_docs}")
            
            # --- KG Storage ---
            # Write Neo4j graph to database
            try:
                neo_status = save_to_neo4j(graph_docs, full_wipe=True)
            except Exception as e:
                print(f"\t[ERROR] Failed to save graph to Neo4j: {e}")
                return jsonify({"error": "neo4j_save_failed", "detail": str(e)}), 400

        summaries.append({
            "doc_id": doc_id,
            "filename": filename,
            "num_pages": len(pages),
            "num_chunks": len(chunks),
            "num_nodes": sum(len(doc.nodes) for doc in graph_docs),
            "num_rels": sum(len(doc.relationships) for doc in graph_docs),
        })
        print(f"\t[DEBUG] Summary: {summaries[0]}")
    return jsonify({"result": "ok", "docs": summaries})
