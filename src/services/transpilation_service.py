"""Transpilation business logic service"""

from typing import Dict, Any, Tuple, List, Optional
import asyncio

from src.core.interfaces import BaseTranspiler
from src.transpilers.qasm_to_qiskit import QasmToQiskitTranspiler
from src.transpilers.registry import TranspilerRegistry
from src.transpilers.python_to_js import PythonToJavaScriptTranspiler
from src.core.exceptions import LanguageNotSupportedError, TranspilerError
from src.utils.logger import logger
from src.config import get_settings

settings = get_settings()


class TranspilationService:
    """Service for handling transpilation operations"""
    
    def __init__(self):
        self.registry = TranspilerRegistry()
        self._register_transpilers()
    
    def _register_transpilers(self):
        """Register all available transpilers"""
        # Register Python to JavaScript
        self.registry.register(PythonToJavaScriptTranspiler())
        self.registry.register(QasmToQiskitTranspiler())
        
        # Register more transpilers here
        # self.registry.register(PythonToGoTranspiler())
        # self.registry.register(JavaScriptToPythonTranspiler())
        # etc.
        
        logger.info(f"Registered {len(self.registry.get_all_transpilers())} transpilers")
    
    async def transpile(
        self,
        source_code: str,
        source_lang: str,
        target_lang: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str], List[str], float]:
        """
        Transpile code from source to target language
        
        Args:
            source_code: Source code to transpile
            source_lang: Source language
            target_lang: Target language
            options: Transpilation options
            
        Returns:
            Tuple of (transpiled_code, warnings, errors, execution_time_ms)
        """
        import time
        
        start_time = time.time()
        
        # Validate language pair
        if not self.is_language_pair_supported(source_lang, target_lang):
            raise LanguageNotSupportedError(
                f"Transpilation from {source_lang} to {target_lang} is not supported"
            )
        
        # Get appropriate transpiler
        transpiler = self.registry.get_transpiler(source_lang, target_lang)
        
        if not transpiler:
            raise TranspilerError(f"No transpiler found for {source_lang} to {target_lang}")
        
        # Validate input
        if options and options.get("strict_mode"):
            self._validate_code(source_code, source_lang)
        
        # Perform transpilation
        try:
            transpiled_code, warnings, errors = await transpiler.transpile(
                source_code, options or {}
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Log performance
            if execution_time_ms > 1000:  # Warning if > 1 second
                logger.warning(
                    f"Slow transpilation detected: {execution_time_ms:.2f}ms",
                    extra={
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "code_size": len(source_code),
                        "execution_time_ms": execution_time_ms
                    }
                )
            
            return transpiled_code, warnings, errors, execution_time_ms
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Transpilation failed: {str(e)}")
            raise TranspilerError(f"Transpilation failed: {str(e)}") from e
    
    def is_language_pair_supported(self, source_lang: str, target_lang: str) -> bool:
        """Check if language pair is supported"""
        supported_targets = settings.SUPPORTED_LANGUAGES.get(source_lang, [])
        return target_lang in supported_targets
    
    def _validate_code(self, code: str, language: str):
        """Validate code syntax for the source language"""
        # Implement language-specific validation
        # This is a placeholder for actual validation logic
        if language == "python":
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                raise TranspilerError(f"Invalid Python syntax: {str(e)}")
        # Add validation for other languages