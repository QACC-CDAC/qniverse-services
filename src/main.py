"""Main application entry point"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_fastapi_instrumentator import Instrumentator
import time

import asyncio

from src.config import get_settings
from src.api.routes import api_router
from src.core.tasks import cleanup_old_jobs_task
from src.middleware.request_id import RequestIDMiddleware
from src.middleware.logging import LoggingMiddleware
from src.utils.logger import setup_logging
from src.utils.metrics import setup_metrics
from src.core.exceptions import setup_exception_handlers
from src.workers.package_worker import worker_loop


settings = get_settings()
setup_logging()

# Track startup time
start_time = time.time()

# Define security scheme for OpenAPI
security_scheme = HTTPBearer(
    auto_error=False,
    description="Enter your API key in the format: 'your-api-key-here'"
)


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Verify API key from Authorization header"""
    api_key = credentials.credentials if credentials else None
    
    # Also check X-API-Key header (will be handled by middleware)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide via Authorization header or X-API-Key header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if api_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Handle application startup and shutdown events"""
    # Startup
    print(f"\n{'='*60}")
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print(f"🌐 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"{'='*60}\n")
    
    # Initialize connections
    await initialize_connections()
    # Start background tasks
    asyncio.create_task(cleanup_old_jobs_task())
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down application...")
    await shutdown_connections()
    print("✅ Shutdown complete")


async def initialize_connections() -> None:
    """Initialize database and cache connections"""
    from src.services.cache_service import cache_service
    await cache_service.initialize()
    print("✅ Cache connection established")

    


async def shutdown_connections() -> None:
    """Close database and cache connections"""
    from src.services.cache_service import cache_service
    await cache_service.close()
    print("✅ Cache connection closed")


def create_app() -> FastAPI:
    """Application factory pattern"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="""
        ## Transpilation API
        
        Convert source code between multiple programming languages with high performance and reliability.
        
        ### Features:
        * 🔄 Support for multiple language pairs
        * 🚀 High performance async processing
        * 🔒 Secure API key authentication
        * 📊 Built-in monitoring and metrics
        * 💾 Optional caching with Redis
        
        ### Authentication
        All endpoints require an API key passed in the `X-API-Key` header.
        """,
        docs_url="/docs",
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "transpilation",
                "description": "Endpoints for transpiling code between languages"
            },
            {
                "name": "health",
                "description": "Health check and monitoring endpoints"
            },
            {
                "name": "languages",
                "description": "Get information about supported languages"
            },
            {
                "name": "packages",
                "description": "Get information about supported packages"
            },
            {
                "name": "qrng",
                "description": "Get Random numbers from Quantum Random Number Generator"
            }
        ]
    )
    
    # Add middleware (order matters!)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
        max_age=3600,
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Override in production
    )
    
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # Setup monitoring
    if settings.PROMETHEUS_ENABLED:
        setup_metrics(app)
        Instrumentator().instrument(app).expose(app)
    
    return app


app = create_app()


def main() -> None:
    """Entry point for console script"""
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
