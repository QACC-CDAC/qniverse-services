"""API route aggregator"""

from fastapi import APIRouter
from .transpile import router as transpile_router
from .health import router as health_router
from .languages import router as languages_router
from .package import router as package_router
from .qrng import router as qrng_router

api_router = APIRouter()

# Include all routers
api_router.include_router(transpile_router, prefix="/transpile", tags=["transpilation"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(languages_router, prefix="/languages", tags=["languages"])
api_router.include_router(package_router, prefix="/packages", tags=["packages"])
api_router.include_router(qrng_router, prefix="/qrng", tags=["qrng"])