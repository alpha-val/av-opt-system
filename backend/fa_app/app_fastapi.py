# app_fastapi.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from .etl_bronze_DELETE import router as etl_router
from .etl_base_case import router_base_case
from .etl_vault_data import router_vault_data
from .query_vault_data import router_query_vault_data

app = FastAPI(title="Alpha-Val ETL (FastAPI)", version="0.1.0")

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


# Health
@app.get("/healthz")
def healthz():
    return {"ok": True}


# Local dev run: uvicorn package.app_fastapi:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("package_name.app_fastapi:app", host="0.0.0.0", port=8000, reload=True)
