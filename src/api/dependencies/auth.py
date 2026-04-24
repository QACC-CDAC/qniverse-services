"""Authentication dependencies"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.config import get_settings
from src.utils.logger import logger

settings = get_settings()
security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API Key authentication handler"""
    
    async def __call__(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> str:
        """
        Validate API key from either header or bearer token
        """
        # Try to get API key from custom header first
        api_key = request.headers.get(settings.API_KEY_HEADER)
        
        # If not in custom header, try bearer token
        if not api_key and credentials:
            api_key = credentials.credentials
        
        # Validate API key
        if not api_key:
            logger.warning(f"Missing API key for request to {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Please provide via X-API-Key header or Bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if api_key not in settings.API_KEYS:
            logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log successful authentication (without full key)
        logger.debug(f"Authentication successful for key: {api_key[:8]}...")
        
        return api_key


# Singleton instance
api_key_auth = APIKeyAuth()


async def verify_api_key(
    request: Request,
    api_key: str = Depends(api_key_auth)
) -> str:
    """
    Dependency to verify API key
    """
    return api_key