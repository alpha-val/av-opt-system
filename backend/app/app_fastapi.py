# app_fastapi.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.bronze_store import ensure_bronze_indexes

# from .etl_bronze_DELETE import router as etl_router
from .etl_base_case import router_base_case
from .etl_vault_data import router_vault_data
from .pipeline_costing import router_costing
from .pipeline_projects import router_projects
from .pipeline_query import router_query_vault_data
from .pipeline_users import router_auth

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
app.include_router(router_vault_data, prefix="/api/v1")
app.include_router(router_query_vault_data, prefix="/api/v1")
app.include_router(router_costing, prefix="/api/v1")
app.include_router(router_projects, prefix="/api/v1")
app.include_router(router_auth, prefix="/api/v1")

# Health
@app.get("/healthz")
def healthz():
    return {"ok": True}

# Local dev run: uvicorn package.app_fastapi:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app_fastapi:app", host="0.0.0.0", port=8000, reload=True)
