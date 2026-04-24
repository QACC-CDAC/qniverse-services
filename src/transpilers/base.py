"""Base transpiler implementation"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from src.core.interfaces import BaseTranspiler as IBaseTranspiler


class BaseTranspiler(IBaseTranspiler):
    """Base class for all transpilers with common functionality"""
    
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
    
    def clear_messages(self):
        """Clear warnings and errors"""
        self.warnings = []
        self.errors = []
    
    def format_code(self, code: str, language: str, options: Dict[str, Any]) -> str:
        """Format code according to language standards"""
        if options.get("format_code", True):
            # Implement code formatting based on language
            # This is a placeholder
            pass
        return code
    
    @abstractmethod
    async def transpile(
        self, 
        source_code: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str], List[str]]:
        """Transpile source code"""
        pass
    
    @abstractmethod
    def supports(self, source: str, target: str) -> bool:
        """Check if language pair is supported"""
        pass
    
    @abstractmethod
    def get_source_language(self) -> str:
        """Get source language"""
        pass
    
    @abstractmethod
    def get_target_language(self) -> str:
        """Get target language"""
        pass