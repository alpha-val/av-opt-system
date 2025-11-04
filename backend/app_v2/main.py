# Load .env globally
from dotenv import load_dotenv
import os

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"), override=True
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.routers.projects import projects_router
from .api.v1.routers.auth import auth_router
from .api.v1.routers.documents import documents_router
from .api.v1.routers.etl import etl_router
from .adapters.mongo.client import ensure_bronze_indexes


def create_app() -> FastAPI:
    async def lifespan(app: FastAPI):
        # Startup logic
        print("[DEBUG : main.py] Ensuring indexes during startup...")
        ensure_bronze_indexes()
        print("[DEBUG : main.py] Indexes ensured.")
        yield  # This is where the app runs
        # Shutdown logic (if needed)
        print("[DEBUG : main.py] Application is shutting down...")

    app = FastAPI(title="Alpha‑Val Optionality API", version="0.0.1", lifespan=lifespan)

    # CORS (tune as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    '''
    # Example of more restrictive and secure CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-frontend-domain.com"],  # Replace with your frontend's domain
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],  # Restrict to necessary methods
        allow_headers=["Authorization", "Content-Type"],  # Restrict to necessary headers
    )
    '''
    
    
    # Include routers
    app.include_router(projects_router)
    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(etl_router)
    
    # Simple health check endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


# Create the FastAPI app instance
app = create_app()
