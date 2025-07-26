from flask import Blueprint, request, jsonify
from rq import Queue
from redis import Redis
from redis.exceptions import RedisError
from .services.ingest import ingest_document
from .services.query import nodes, edges

bp = Blueprint("api", __name__)
q = Queue(
    connection=Redis.from_url("redis://localhost:6379")
)  # Update Redis URL if needed

@bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"message": "Hello from Alpha-Val Optionality backend!"}), 200

@bp.route("/ingest", methods=["POST"])
def ingest():
    try:
        uploaded = request.files.get("file")
        text = request.json.get("text") if request.is_json else None
        if not uploaded and not text:
            return jsonify({"error": "No input provided"}), 400

        try:
            job = q.enqueue(ingest_document, uploaded.read() if uploaded else text)
        except RedisError as e:
            return jsonify({"error": f"Failed to enqueue job: {e}"}), 500

        return jsonify({"job_id": job.get_id()}), 202
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/ingest: {e}"}), 500


@bp.route("/nodes", methods=["GET"])
def get_nodes():
    try:
        node_type = request.args.get("type")
        limit = int(request.args.get("limit", 100))
        records = nodes(node_type=node_type, limit=limit)
        return jsonify(records)
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/nodes: {e}"}), 500


@bp.route("/api/edges", methods=["GET"])
def get_edges():
    try:
        edge_type = request.args.get("type")
        limit = int(request.args.get("limit", 100))
        records = edges(edge_type=edge_type, limit=limit)
        return jsonify(records)
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/edges: {e}"}), 500