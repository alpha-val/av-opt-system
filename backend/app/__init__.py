from flask import Flask, send_from_directory, request, jsonify

import os
from dotenv import load_dotenv

from .api import bp as api_bp

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def create_app():

    react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "./build"))
    app = Flask(__name__, static_folder=react_build_dir, static_url_path="")
    print("Serving static site from: ", react_build_dir)

    app.register_blueprint(api_bp, url_prefix="/api/v1")


    # ✅ Handle 404 for API and fallback to index.html for everything else
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "API route not found"}), 404
        return send_from_directory(app.static_folder, "index.html")

    # ✅ Serve frontend fallback
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):

        if path.startswith("api"):
            return "Page not Found!", 404

        static_dir = app.static_folder
        file_path = os.path.join(static_dir, path)

        if path != "" and os.path.exists(file_path):
            return send_from_directory(static_dir, path)
        else:
            return send_from_directory(static_dir, "index.html")


    return app
