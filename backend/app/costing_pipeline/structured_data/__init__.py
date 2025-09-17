# Structured (Spreadsheet) → RAG + GraphRAG Pipeline

# This package adds **tabular ingestion** (Excel/CSV) alongside your existing PDF pipeline. It:

# * Parses spreadsheets with **unit/currency normalization**
# * Builds **provenance spine** `Table → Row → Cell`
# * Maps rows to **domain nodes** (Equipment, CostEstimate, CapacityPoint, …)
# * Creates **row‑card \:Chunk** nodes + **MENTIONS** edges so Pinecone retrieval works identically to PDF chunks
# * Upserts **row‑cards to Pinecone** (dense + sparse hybrid) with rich metadata
# * Provides a **Flask blueprint** parallel to your PDF endpoints
# * Ships a **Cypher bundle** (constraints + merge templates) for the provenance spine

# > Drop these files under your project (e.g., `app/structured/…`) and register the blueprint.

# ---

## File: `structured/__init__.py`

# ```python
from __future__ import annotations
from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
import io
from typing import List, Dict, Any

from .pipeline import run_ingestion_for_table_stream, run_ingestion_for_table_path
from .pdf_pipeline import run_ingestion_for_structured_pdf_stream, run_ingestion_for_structured_pdf_path

structured_bp = Blueprint("structured", __name__, url_prefix="/structured")


@structured_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "structured"}), 200


@structured_bp.route("/ingest_xls_csv", methods=["POST"])
def ingest_xls_csv():
    """
    Ingest one or more spreadsheets (xlsx/csv).
    - form-data: files=<file(s)> [sheet="Gyratory" optional]
    - JSON: {"paths": ["/abs/file.xlsx"], "sheet": "Gyratory"}
    Returns: per-file summary (nodes/edges written, pinecone upserts, counts)
    """
    results: List[Dict[str, Any]] = []

    # A) multipart files
    files: List[FileStorage] = request.files.getlist("files")
    sheet = request.form.get("sheet")
    currency = request.form.get("currency")  # e.g., USD; overrides auto-detect
    base_year = request.form.get("base_year")  # e.g., 2015
    if files:
        for f in files:
            stream = io.BytesIO(f.read())
            stream.name = f.filename
            try:
                out = run_ingestion_for_table_stream(
                    stream,
                    sheet=sheet,
                    currency_override=currency,
                    base_year_override=base_year,
                )
                results.append(out)
            except Exception as ex:
                results.append({"file": stream.name, "error": str(ex)})
        return jsonify({"results": results}), 200

    # B) JSON with paths
    data = request.get_json(silent=True) or {}
    paths = data.get("paths") or []
    sheet = data.get("sheet")
    currency = data.get("currency")
    base_year = data.get("base_year")
    if paths:
        for p in paths:
            try:
                out = run_ingestion_for_table_path(
                    p,
                    sheet=sheet,
                    currency_override=currency,
                    base_year_override=base_year,
                )
                results.append(out)
            except Exception as ex:
                results.append({"file": p, "error": str(ex)})
        return jsonify({"results": results}), 200

    return jsonify({"error": "Provide form-data 'files' or JSON {'paths': [...]}"}), 400


@structured_bp.route("/ingest_pdf", methods=["POST"])
def ingest_pdf():
    """
    Ingest tables from a PDF (vector or scanned).
    - form-data: file=<pdf> [pages="1,3-5"] [dpi=300] [currency] [base_year]
    - JSON: {"path": "/abs/file.pdf", "pages": "2-4", "dpi": 300, "currency": "USD", "base_year": 2015}
    """
    # A) multipart
    if "file" in request.files:
        pdf = request.files["file"]
        pages = request.form.get("pages")
        dpi = int(request.form.get("dpi", "300"))
        currency = request.form.get("currency")
        base_year = request.form.get("base_year")
        import io as _io

        stream = _io.BytesIO(pdf.read())
        stream.name = pdf.filename
        try:
            res = run_ingestion_for_structured_pdf_stream(
                stream,
                file_name=pdf.filename,
                pages=pages,
                dpi=dpi,
                currency_override=currency,
                base_year_override=int(base_year) if base_year else None,
            )
            return jsonify(res), 200
        except Exception as ex:
            return jsonify({"error": str(ex)}), 500

    # B) JSON path
    data = request.get_json(silent=True) or {}
    path = data.get("path")
    if path:
        pages = data.get("pages")
        dpi = int(data.get("dpi", 300))
        currency = data.get("currency")
        base_year = data.get("base_year")
        try:
            res = run_ingestion_for_structured_pdf_path(
                path,
                pages=pages,
                dpi=dpi,
                currency_override=currency,
                base_year_override=int(base_year) if base_year else None,
            )
            return jsonify(res), 200
        except Exception as ex:
            return jsonify({"error": str(ex)}), 500

    return jsonify({"error": "Send multipart 'file' or JSON {'path': ...}"}), 400
