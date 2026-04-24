"""Background tasks for package management"""

import asyncio
from src.services.package_service import package_service
from src.utils.logger import logger
from src.config import get_settings

settings = get_settings()


async def cleanup_old_jobs_task():
    """Background task to clean up old package installation jobs"""
    while True:
        try:
            # Sleep for 1 hour
            await asyncio.sleep(3600)
            
            # Clean up jobs older than configured age
            cleaned = package_service.cleanup_old_jobs(
                max_age_hours=settings.PACKAGE_CLEANUP_AGE_HOURS
            )
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old package installation jobs")
                
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")