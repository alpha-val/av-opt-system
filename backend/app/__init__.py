from flask import Flask, send_from_directory, request, jsonify
import os
from dotenv import load_dotenv
from .api import bp as api_bp
# from .ingestion_pipeline.main import ingestion_bp
# from .alpha_val_simple_ingest.si_main import simple_ingest_bp
# from .alpha_val_simple_ingest.query.router import simple_ingest_query_bp
from .optpro_rag_kg.api.router import opt_pipeline_bp
from . import data_service

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def create_app():
    react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "./build"))
    app = Flask(__name__, static_folder=react_build_dir, static_url_path="")
    print("Serving static site from: ", react_build_dir)

    # Core API blueprint
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    app.register_blueprint(opt_pipeline_bp, url_prefix="/opt/v1")
    
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/") or request.path.startswith("/ingest/"):
            return jsonify({"error": "API route not found"}), 404
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api") or path.startswith("ingest"):
            return "Page not Found!", 404
        static_dir = app.static_folder
        file_path = os.path.join(static_dir, path)
        if path and os.path.exists(file_path):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")


    return app
