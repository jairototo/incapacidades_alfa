"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db import get_db
from apps.backend.app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """
    Database health check endpoint.
    
    Args:
        db: Database session
        
    Returns:
        dict: Database health status
    """
    try:
        # Execute a simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {
            "status": "ok",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message
    """
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }
