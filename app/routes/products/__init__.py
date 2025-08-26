"""Product management routes package."""

# Combine all product routers
from fastapi import APIRouter

from .bulk_delete import router as bulk_delete_router
from .create import router as create_router
from .csv import router as csv_router
from .edit import router as edit_router
from .search import router as search_router

router = APIRouter()
router.include_router(create_router)
router.include_router(edit_router)
router.include_router(csv_router)
router.include_router(bulk_delete_router)
router.include_router(search_router)
