from flask import Blueprint, request, jsonify
from rq import Queue
from redis import Redis
from redis.exceptions import RedisError
from .data_service.pipeline import make_graph
from .data_service.query import nodes, edges, create_d3_graph
from .data_service.file_handler import extract_text_from_pdf
from .data_service.parse_reports import process_report
import asyncio

# Create a Blueprint for the API
bp = Blueprint("api", __name__)

# Initialize Redis connection and RQ queue
q = Queue(
    connection=Redis.from_url("redis://localhost:6379")
)  # Update Redis URL if needed


@bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"message": "Hello from Alpha-Val Optionality backend!"}), 200


"""
rq-worker-1  | [DEBUG]: Error in ingest_document: Error during graph transformation: Task exceeded maximum timeout value (180 seconds)
rq-worker-1  | 13:07:14 Successfully completed app.services.ingest_graph_transform.ingest_doc_graph_transform(' \nNI 43 -101 Technical Report  \non the  \nRogue  Gold Property  \nYukon,..., full_wipe=True) job in 0:03:10.959246s on worker 3dfa72e0cd9e422a8ea174eb86cd4892
rq-worker-1  | 13:07:14 default: Job OK (cc864214-dc48-4e8c-9a6d-af30e5210505)
rq-worker-1  | 13:07:14 Result is kept for 500 seconds
"""


@bp.route("/pipeline", methods=["POST"])
def ingest_document():
    try:
        data = request.json

        try:
            job = q.enqueue(
                make_graph,
                data,
                full_wipe=True,  # Set to True for initial ingestion
            )
        except RedisError as e:
            return jsonify({"error": f"Failed to enqueue job: {e}"}), 500
        print("\n[DEBUG] S U C C E S S\n")
        return jsonify({"job_id": job.get_id()}), 202
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/ingest_doc: {e}"}), 500


@bp.route("/nodes", methods=["GET"])
def get_nodes():
    try:
        print("[DEBUG] Fetching nodes with parameters:", request.args)
        node_type = request.args.get("type")
        limit = int(request.args.get("limit", 100))
        records = nodes(node_type=node_type, limit=limit)
        # print("[DEBUG] Fetched nodes:", records)
        return jsonify(records)
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/nodes: {e}"}), 500


@bp.route("/ingest_report", methods=["POST"])
def ingest_report():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"error": "Missing file"}), 400
    try:
        print("[DEBUG] Processing report...")
        # Await the asynchronous function to extract text from the PDF
        pdf_bytes = request.files["file"].read()  # Flask FileStorage
        print(f"[DEBUG] PDF bytes read successfully. Number of bytes {len(pdf_bytes)}")
        result = process_report(pdf_bytes)
        print(f"[DEBUG] Processed report with result: {result}")
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to extract text from PDF: {e}"}), 500


@bp.route("/file_upload", methods=["POST"])
def upload_and_get_nodes():
    uploaded_file = request.files.get("file")
    print("Type of input: ", type(uploaded_file))
    if not uploaded_file:
        return jsonify({"error": "Missing file"}), 400

    try:
        # Await the asynchronous function to extract text from the PDF
        extracted_text = asyncio.run(extract_text_from_pdf(uploaded_file.stream))
        # print(f"[DEBUG] Extracted text from PDF: {extracted_text[:100]}...")

    except Exception as e:
        return jsonify({"error": f"Failed to extract text from PDF: {e}"}), 500

    # return jsonify({"text": "done"}), 200

    print("[DEBUG] Extracted text length:", len(extracted_text))
    try:
        job = q.enqueue(
            make_graph,
            {"text": extracted_text},
            full_wipe=True,  # Set to True for initial ingestion
            job_timeout=600,  # Set a higher timeout for longer processing
        )
    except RedisError as e:
        return jsonify({"error": f"Failed to enqueue job: {e}"}), 500
    print("\n[DEBUG] S U C C E S S\n")
    return jsonify({"job_id": job.get_id()}), 202


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


@bp.route("/user_query", methods=["POST"])
def user_query():
    try:
        data = request.json
        print("[DEBUG] Received query generation request with data:", data)
        # Call the appropriate service function for query generation
        # For example:
        # result = query_generation_service.generate_query(data)
        result = {"query": "MATCH (n) RETURN n LIMIT 10"}  # Placeholder
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/query_gen: {e}"}), 500


@bp.route("/graph", methods=["GET"])
def get_full_graph():
    try:
        node_limit = int(request.args.get("node_limit", 1000))
        edge_limit = int(request.args.get("edge_limit", 1000))
        node_records = nodes(limit=node_limit)
        edge_records = edges(limit=edge_limit)
        graph = create_d3_graph(node_records, edge_records)

        if not graph:
            return jsonify({"error": "No nodes or edges found"}), 404
        return jsonify({"graph": graph})
        # return jsonify({
        #     "nodes": node_records,
        #     "edges": edge_records
        # })
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/graph: {e}"}), 500
