"""Custom validators for request data"""

import re
from typing import Tuple, List


class CodeValidator:
    """Validate source code for different languages"""
    
    @staticmethod
    def validate_python(code: str) -> Tuple[bool, List[str]]:
        """Validate Python code syntax"""
        errors = []
        try:
            compile(code, '<string>', 'exec')
            return True, errors
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
            return False, errors
    
    @staticmethod
    def validate_javascript(code: str) -> Tuple[bool, List[str]]:
        """Validate JavaScript code syntax (basic)"""
        errors = []
        # Check for basic syntax issues
        if re.search(r'function\s*\([^)]*\)\s*{[^}]*$', code, re.MULTILINE):
            errors.append("Possible missing closing brace in function")
        
        if code.count('(') != code.count(')'):
            errors.append("Mismatched parentheses")
        
        if code.count('{') != code.count('}'):
            errors.append("Mismatched curly braces")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_code(code: str, language: str) -> Tuple[bool, List[str]]:
        """Validate code for specified language"""
        validators = {
            "python": CodeValidator.validate_python,
            "javascript": CodeValidator.validate_javascript,
            "typescript": CodeValidator.validate_javascript,
        }
        
        validator = validators.get(language)
        if validator:
            return validator(code)
        
        # No validator for this language
        return True, []