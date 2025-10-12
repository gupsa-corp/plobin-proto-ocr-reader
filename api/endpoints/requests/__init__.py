"""
Modularized requests API endpoints
"""

from fastapi import APIRouter

from .request_processing import router as processing_router
from .request_queries import router as queries_router
from .page_content import router as content_router
from .block_access import router as access_router
from .section_access import router as section_router
from .search import router as search_router

# Main router that combines all request-related endpoints
router = APIRouter()

# Include all sub-routers
router.include_router(processing_router, tags=["Request Processing"])
router.include_router(queries_router, tags=["Request Queries"])
router.include_router(content_router, tags=["Page Content"])
router.include_router(access_router, tags=["Block Access"])
router.include_router(section_router, tags=["Section Access"])
router.include_router(search_router, tags=["Search"])

# Export the set_dependencies functions for backward compatibility
from .dependencies import set_dependencies, set_processing_dependencies

__all__ = [
    "router",
    "set_dependencies",
    "set_processing_dependencies"
]