"""
Blueprint + endpoints for PDF → chunks → embeddings (dense+sparse) → Pinecone,
then OpenAI function-calls (TOOLS + ontology) → nodes/edges → Neo4j.
"""

from __future__ import annotations
import logging
from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
from typing import List, Dict, Any, Tuple, Optional
import io
import os

from .pipeline import run_ingestion_for_pdf_stream, run_ingestion_for_pdf_path

# Set up logger
from .utils.logging import get_logger
log = get_logger(__name__)
log.debug(f"Logger handlers: {log.handlers}")

costing_pipeline_bp = Blueprint("in_pipeline", __name__, url_prefix="/in_pipeline")


@costing_pipeline_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "in_pipeline"}), 200


@costing_pipeline_bp.route("/ingest", methods=["POST"])
def ingest():
    """
    Ingest one or more PDFs.
    - Form-data: files=<file(s)>
    - OR JSON:   {"paths": ["/abs/path/file1.pdf", ...]}
    Returns: per-file summary with chunks, pinecone upserts, neo4j writes
    """
    results: List[Dict[str, Any]] = []

    # Case A: files uploaded via multipart/form-data
    files: List[FileStorage] = request.files.getlist("files")
    if files:
        for f in files:
            file_bytes = f.read()
            stream = io.BytesIO(file_bytes)
            stream.name = getattr(f, "filename", "uploaded.pdf")
            try:
                summary = run_ingestion_for_pdf_stream(stream)
                results.append(summary)
            except Exception as ex:
                results.append({"file": stream.name, "error": str(ex)})
        return jsonify({"results": results}), 200

    # Case B: JSON payload with paths
    data = request.get_json(silent=True) or {}
    paths: List[str] = data.get("paths", [])
    if paths:
        for p in paths:
            try:
                summary = run_ingestion_for_pdf_path(p)
                results.append(summary)
            except Exception as ex:
                results.append({"file": p, "error": str(ex)})
        return jsonify({"results": results}), 200

    return (
        jsonify(
            {
                "error": "No files or paths provided. Use form-data 'files' or JSON {'paths': [...]}."
            }
        ),
        400,
    )
