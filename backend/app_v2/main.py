# Load .env globally
from dotenv import load_dotenv
import os
import logging
import sys

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"), override=True
)

# Configure logging
# Get log level from environment or default to INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to console
    ],
    force=True  # Override any existing configuration
)

# Set specific logger levels
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

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
        logger.info("Ensuring indexes during startup...")
        ensure_bronze_indexes()
        logger.info("Indexes ensured.")
        yield  # This is where the app runs
        # Shutdown logic (if needed)
        logger.info("Application is shutting down...")

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
