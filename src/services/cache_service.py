"""Caching service for transpilation results"""

import json
import hashlib
from typing import Optional, Dict, Any
import redis.asyncio as redis
from src.config import get_settings
from src.utils.logger import logger

settings = get_settings()


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.client = None
        self.enabled = settings.ENABLE_CACHE and settings.REDIS_URL is not None
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self.enabled and not self.client:
            try:
                self.client = redis.from_url(
                    settings.REDIS_URL,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    decode_responses=True
                )
                await self.client.ping()
                logger.info("Redis cache service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {str(e)}")
                self.enabled = False
                self.client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis cache service closed")
    
    def generate_key(
        self, 
        source_code: str, 
        source_lang: str, 
        target_lang: str,
        options: Dict[str, Any]
    ) -> str:
        """
        Generate cache key from request parameters
        """
        # Create a deterministic string for the key
        key_data = {
            "source_code": source_code,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "options": options
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"transpile:{source_lang}:{target_lang}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        if not self.enabled or not self.client:
            return None
        
        try:
            cached = await self.client.get(key)
            if cached:
                logger.debug(f"Cache hit for key: {key[:20]}...")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> bool:
        """Cache response"""
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or settings.CACHE_TTL_SECONDS
            await self.client.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
            logger.debug(f"Cached response with TTL {ttl}s: {key[:20]}...")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached entry"""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {str(e)}")
            return 0
    
    async def health_check(self) -> bool:
        """Check cache service health"""
        if not self.enabled:
            return False
        
        try:
            await self.client.ping()
            return True
        except:
            return False


# Singleton instance
cache_service = CacheService()