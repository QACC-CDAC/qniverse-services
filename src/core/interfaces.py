"""Abstract base classes and interfaces"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional


class BaseTranspiler(ABC):
    """Abstract base class for all transpilers"""
    
    @abstractmethod
    async def transpile(
        self, 
        source_code: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str], List[str]]:
        """
        Transpile source code to target language
        
        Args:
            source_code: Source code to transpile
            options: Transpilation options
            
        Returns:
            Tuple of (transpiled_code, warnings, errors)
        """
        pass
    
    @abstractmethod
    def supports(self, source: str, target: str) -> bool:
        """Check if this transpiler supports the language pair"""
        pass
    
    @abstractmethod
    def get_source_language(self) -> str:
        """Get source language for this transpiler"""
        pass
    
    @abstractmethod
    def get_target_language(self) -> str:
        """Get target language for this transpiler"""
        pass


class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass


class MetricsCollector(ABC):
    """Abstract base class for metrics collection"""
    
    @abstractmethod
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics"""
        pass
    
    @abstractmethod
    def record_transpilation(self, source: str, target: str, duration: float, success: bool):
        """Record transpilation metrics"""
        pass
    
    @abstractmethod
    def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        pass
    
    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric"""
        pass