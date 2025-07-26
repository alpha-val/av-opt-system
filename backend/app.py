
# app.py
from flask_cors import CORS
from app import create_app
import os

# Create the Flask app instance using the factory function
app = create_app()
CORS(app, supports_credentials=True)

if __name__ == '__main__':
    app.run(debug=True)
