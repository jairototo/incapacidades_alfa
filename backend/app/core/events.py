"""
Event handlers para startup y shutdown de la aplicación.
"""
import os
from typing import Callable
from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from app.db.session import engine
from app.core.config import settings


def create_start_app_handler(app: FastAPI) -> Callable:
    """Crear handler para inicio de aplicación."""
    
    async def start_app() -> None:
        logger.info("Starting application...")
        logger.info(f"Environment: {app.title}")
        
        # Test database connection
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
        
        # Initialize storage backend
        try:
            from app.core.storage import storage_backend
            
            if settings.STORAGE_BACKEND == "filesystem":
                # Crear directorio base si no existe
                os.makedirs(settings.FILESYSTEM_BASE_PATH, exist_ok=True)
                logger.info(
                    f"FileSystem storage initialized at: {settings.FILESYSTEM_BASE_PATH}"
                )
            elif settings.STORAGE_BACKEND == "minio":
                # MinIO ya inicializa el bucket en el constructor
                logger.info(
                    f"MinIO storage initialized at: {settings.STORAGE_ENDPOINT}"
                )
            else:
                logger.warning(f"Unknown storage backend: {settings.STORAGE_BACKEND}")
                
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            # No raise - storage is optional for some operations
        
        logger.info("Application started successfully")
    
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """Crear handler para cierre de aplicación."""
    
    async def stop_app() -> None:
        logger.info("Stopping application...")
        
        # Dispose database engine
        await engine.dispose()
        
        logger.info("Application stopped")
    
    return stop_app
