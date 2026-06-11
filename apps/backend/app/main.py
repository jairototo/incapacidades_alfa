"""
Punto de entrada principal de la aplicacion FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.api.v1.router import api_router
from app.middleware.error_handler import add_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware

# Setup logging
setup_logging()

# Create FastAPI app
_is_production = settings.ENVIRONMENT == "production"
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gestion de incapacidades en aseguradoras",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if not _is_production else None,
    docs_url="/docs" if not _is_production else None,
    redoc_url="/redoc" if not _is_production else None,
)

# Add middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

# Add exception handlers
add_exception_handlers(app)

# Event handlers
app.add_event_handler("startup", create_start_app_handler(app))
app.add_event_handler("shutdown", create_stop_app_handler(app))

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy"
    }
