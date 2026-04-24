"""Transpiler registry for managing transpiler instances"""

from typing import Dict, Optional, List
from src.core.interfaces import BaseTranspiler
from src.utils.logger import logger


class TranspilerRegistry:
    """Registry for managing and discovering transpilers"""
    
    def __init__(self):
        self._transpilers: Dict[str, Dict[str, BaseTranspiler]] = {}
    
    def register(self, transpiler: BaseTranspiler) -> None:
        """Register a transpiler in the registry"""
        source = transpiler.get_source_language()
        target = transpiler.get_target_language()
        
        if source not in self._transpilers:
            self._transpilers[source] = {}
        
        self._transpilers[source][target] = transpiler
        logger.info(f"Registered transpiler: {source} -> {target}")
    
    def get_transpiler(self, source_lang: str, target_lang: str) -> Optional[BaseTranspiler]:
        """Get transpiler for language pair"""
        if source_lang in self._transpilers:
            return self._transpilers[source_lang].get(target_lang)
        return None
    
    def get_all_transpilers(self) -> List[BaseTranspiler]:
        """Get all registered transpilers"""
        transpilers = []
        for source_dict in self._transpilers.values():
            transpilers.extend(source_dict.values())
        return transpilers
    
    def get_supported_sources(self) -> List[str]:
        """Get list of supported source languages"""
        return list(self._transpilers.keys())
    
    def get_supported_targets(self, source_lang: str) -> List[str]:
        """Get supported targets for a source language"""
        if source_lang in self._transpilers:
            return list(self._transpilers[source_lang].keys())
        return []
    
    def is_supported(self, source_lang: str, target_lang: str) -> bool:
        """Check if language pair is supported"""
        return self.get_transpiler(source_lang, target_lang) is not None
    
    def clear(self):
        """Clear all registered transpilers"""
        self._transpilers.clear()
        logger.info("Cleared all transpilers from registry")