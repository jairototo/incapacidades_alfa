"""
Configuración de logging.
"""
import sys
import logging
import os
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging():
    """Configurar logging con Loguru."""
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # File handler (JSON format for production)
    if settings.ENVIRONMENT == "production":
        # Create logs directory if it doesn't exist
        log_dir = Path("/app/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure proper permissions
        try:
            logger.add(
                str(log_dir / "app.log"),
                rotation="500 MB",
                retention="10 days",
                compression="zip",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
                level=settings.LOG_LEVEL,
                serialize=True  # JSON format
            )
        except PermissionError:
            # If file logging fails, just use console 
            logger.warning("Could not create log file, using console only")
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    return logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging to Loguru."""
    
    def emit(self, record):
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
