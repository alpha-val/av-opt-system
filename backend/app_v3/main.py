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
    handlers=[logging.StreamHandler(sys.stdout)],  # Output to console
    force=True,  # Override any existing configuration
)

# Set specific logger levels
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import progress tracking components
from .domain.progress import InMemoryProgressPublisher, BackgroundTaskRunner
from .domain.file_processing import FileProcessingService
from .domain.projects.orchestration import ProjectOrchestrationService
from .domain.projects.file_storage import FileStorageService
from .domain.parsing.services import DocumentProcessingService

# Import MongoDB index setup
from .adapters.mongo.client import ensure_bronze_indexes

# Import routers
from .api.v1.routers import websocket, files, auth, projects, scenarios, cost_estimates, costing_api

# Initialize global instances (will be set during startup)
progress_publisher: InMemoryProgressPublisher | None = None
task_runner: BackgroundTaskRunner | None = None
file_processing_service: FileProcessingService | None = None
project_orchestration_service: ProjectOrchestrationService | None = None
file_storage_service: FileStorageService | None = None
document_processing_service: DocumentProcessingService | None = None


def create_app() -> FastAPI:
    async def lifespan(app: FastAPI):
        # Startup logic
        logger.info("Initializing application components...")

        # Initialize progress tracking infrastructure
        global progress_publisher, task_runner, file_processing_service, project_orchestration_service, file_storage_service, document_processing_service

        # Create progress publisher (in-memory implementation)
        # This can be swapped with Redis-based implementation for multi-process deployments
        progress_publisher = InMemoryProgressPublisher()
        logger.info("Progress publisher initialized")

        # Create background task runner
        # Uses ThreadPoolExecutor by default (can be changed to ProcessPoolExecutor)
        max_workers = int(os.getenv("BACKGROUND_WORKERS", "4"))
        task_runner = BackgroundTaskRunner(max_workers=max_workers, use_processes=False)
        logger.info(f"Background task runner initialized (max_workers={max_workers})")

        # Create file processing service
        file_processing_service = FileProcessingService()
        logger.info("File processing service initialized")

        # Create file storage service
        file_storage_service = FileStorageService()
        logger.info("File storage service initialized")

        # Create document processing service (for table and entity extraction)
        document_processing_service = DocumentProcessingService()
        logger.info("Document processing service initialized")

        # Create project orchestration service (inject file storage and document processing services)
        project_orchestration_service = ProjectOrchestrationService(
            file_storage_service=file_storage_service,
            document_processing_service=document_processing_service
        )
        logger.info("Project orchestration service initialized")

        # Set publisher for WebSocket router
        websocket.set_progress_publisher(progress_publisher)

        # Set services for files router
        files.set_file_processing_service(file_processing_service)
        files.set_task_runner(task_runner)
        files.set_progress_publisher(progress_publisher)

        # Set orchestration service for projects router
        projects.set_orchestration_service(project_orchestration_service)

        # Set file storage service for projects router
        projects.set_file_storage_service(file_storage_service)

        # Set orchestration service for scenarios router
        scenarios.set_orchestration_service(project_orchestration_service)
        
        # Set file storage service for scenarios router
        scenarios.set_file_storage_service(file_storage_service)

        logger.info("All components initialized successfully")

        # Ensure indexes during startup
        logger.info("Ensuring MongoDB indexes during startup...")
        try:
            ensure_bronze_indexes()
            logger.info("MongoDB indexes ensured successfully.")
        except Exception as e:
            logger.error(f"Failed to ensure indexes: {e}", exc_info=True)
            # Don't fail startup if index creation fails, but log the error
            logger.warning("Continuing startup despite index creation failure...")

        yield  # This is where the app runs

        # Shutdown logic
        logger.info("Application is shutting down...")

        # Shutdown background task runner
        if task_runner:
            task_runner.shutdown(wait=True)
            logger.info("Background task runner shut down")

        logger.info("Shutdown complete")

    app = FastAPI(title="Alpha‑Val Optionality API", version="0.0.1", lifespan=lifespan)

    # CORS (tune as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    """
    # Example of more restrictive and secure CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-frontend-domain.com"],  # Replace with your frontend's domain
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],  # Restrict to necessary methods
        allow_headers=["Authorization", "Content-Type"],  # Restrict to necessary headers
    )
    """

    # Include routers
    # Register WebSocket router for progress updates
    app.include_router(websocket.websocket_router)
    logger.info("WebSocket router registered")

    # Register file processing router
    app.include_router(files.files_router)
    logger.info("File processing router registered")

    # Register auth router
    app.include_router(auth.auth_router)
    logger.info("Auth router registered")

    # Register projects router
    app.include_router(projects.projects_router)
    logger.info("Projects router registered")

    # Register scenarios router
    app.include_router(scenarios.scenarios_router)
    logger.info("Scenarios router registered")
    
    # Register cost estimates router
    app.include_router(cost_estimates.cost_estimates_router)
    logger.info("Cost estimates router registered")
    
    # Register costing API router
    app.include_router(costing_api.costing_router)
    logger.info("Costing API router registered")

    # Simple health check endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


# Create the FastAPI app instance
app = create_app()
