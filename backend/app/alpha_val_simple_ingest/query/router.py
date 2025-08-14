# ````python // filepath: /Users/test/Documents/Projects/Optionality_Mining/av-opt-system/backend/app/alpha_val_simple_ingest/query/router.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from .service import run_query_pipeline

simple_ingest_query_bp = Blueprint("si_query", __name__)
"""
Attach /query route to provided blueprint.
POST JSON: { "question": "..." , "top_k": 8 }
"""
@simple_ingest_query_bp.post("/query")
def query_endpoint():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")
    if question is None:
        return jsonify({"error": "question_missing"}), 400
    top_k = int(data.get("top_k", 8))
    result = {"message": "success"}
    try:
        result = run_query_pipeline(question, top_k=top_k)
        pass
    except Exception as e:
        return jsonify({"error": "query_failed", "detail": str(e)}), 500
    return jsonify(result)