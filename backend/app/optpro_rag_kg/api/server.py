"""Standalone server registering the blueprint."""
from flask import Flask
from .router import opt_pipeline_bp

app = Flask(__name__)
app.register_blueprint(opt_pipeline_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
