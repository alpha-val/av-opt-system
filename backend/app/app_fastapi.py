# app_fastapi.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys

from app.bronze_store import ensure_bronze_indexes

from .etl_base_case import router_base_case
from .pipeline_costing import router_costing
from .pipeline_projects import router_projects
from .pipeline_query import router_query_vault_data
from .pipeline_users import router_auth
from .pipeline_admin import router_admin
from .scenario.pipeline_scenarios import router_scenarios
from .tabular_data.pipeline_tabular_data import router_ingest_tables

# API V2

from app.projects.api_for_project import router_for_projects
from app.documents.api_for_document import router_for_documents

# Configure logging at the top of your file, before creating the FastAPI app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Ensure output goes to stdout
)

# Set specific logger levels if needed
logging.getLogger("app.tabular_data").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[STARTUP] Initializing database...")
    ensure_bronze_indexes()

    # print("[STARTUP] Creating default user...")
    # result = create_default_user()
    # print(f"[STARTUP] Default user result: {result}")

    yield

    # Shutdown (if needed)
    print("[SHUTDOWN] Cleaning up...")


app = FastAPI(title="Alpha-Val ETL (FastAPI)", version="0.1.0", lifespan=lifespan)

# CORS (tune as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router_base_case, prefix="/api/v1")
app.include_router(router_query_vault_data, prefix="/api/v1")
app.include_router(router_costing, prefix="/api/v1")
# app.include_router(router_projects, prefix="/api/v1")
app.include_router(router_auth, prefix="/api/v1")
app.include_router(router_admin, prefix="/api/v1")
app.include_router(router_scenarios, prefix="/api/v1")
app.include_router(router_ingest_tables, prefix="/api/v1")


app.include_router(router_for_projects, prefix="/api/v1")
app.include_router(router_for_documents, prefix="/api/v1", tags=["documents"])

# Health
@app.get("/healthz")
def healthz():
    return {"ok": True}


# Local dev run: uvicorn package.app_fastapi:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.app_fastapi:app", host="0.0.0.0", port=8000, reload=True)
