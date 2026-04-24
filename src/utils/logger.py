"""Logging configuration and utilities"""

import sys
from loguru import logger
from src.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure logging with Loguru"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colorization for development
    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
            enqueue=True,
        )
    else:
        # JSON format for production
        logger.add(
            sys.stdout,
            format="{time} | {level} | {name} | {message}",
            level=settings.LOG_LEVEL,
            serialize=True,
            enqueue=True,
        )
    
    # File handler with rotation
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_MAX_SIZE,
            retention=f"{settings.LOG_BACKUP_COUNT} days",
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    
    # Log startup message
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")