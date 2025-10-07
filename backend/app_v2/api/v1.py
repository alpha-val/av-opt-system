"""
API v1 routes.

Contains all v1 API endpoints.
"""

from fastapi import APIRouter
from app_v2.api.scenarios import router as scenarios_router
from app_v2.api.options import router as options_router
from app_v2.api.query import router as query_router

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(scenarios_router, prefix="/scenarios", tags=["scenarios"])
router.include_router(options_router, prefix="/options", tags=["options"])
router.include_router(query_router, prefix="/query", tags=["query"])

__all__ = ["router"]