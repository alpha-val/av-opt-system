from flask import Blueprint, request, jsonify
from rq import Queue
from redis import Redis
from redis.exceptions import RedisError
from .data_service.pipeline import make_graph
from .data_service.query import nodes, edges
# from .data_service.ingest_langex import build_graph as just_do_it
bp = Blueprint("api", __name__)

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
                full_wipe=False,  # Set to True for initial ingestion
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
        print("[DEBUG] Fetched nodes:", records)
        return jsonify(records)
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error in /api/nodes: {e}"}), 500


@bp.route("/file_upload", methods=["POST"])
async def upload_and_get_nodes():
    uploaded_file = request.files.get("file")
    print("Type of input: ", type(uploaded_file))
    if not uploaded_file:
        return jsonify({"error": "Missing file"}), 400

    try:
        # Await the asynchronous function to extract text from the PDF
        extracted_text = await extract_text_from_pdf(uploaded_file.stream)
        print(f"[DEBUG] Extracted text from PDF: {extracted_text[:100]}...")
        return run_ingestion(extracted_text, full_wipe=True)
        # return (
        #     jsonify(
        #         {
        #             "message": "File processed successfully",
        #             "extracted_text": extracted_text,
        #         }
        #     ),
        #     200,
        # )
    except Exception as e:
        return jsonify({"error": f"Failed to extract text from PDF: {e}"}), 500


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


@bp.route("/query_gen", methods=["POST"])
def query_gen():
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


