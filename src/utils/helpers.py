"""Helper utility functions"""

import re
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


def sanitize_code(code: str, max_length: int = 50000) -> str:
    """Sanitize source code input"""
    # Trim to max length
    if len(code) > max_length:
        code = code[:max_length]
    
    # Remove null bytes
    code = code.replace('\x00', '')
    
    # Normalize line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    
    return code.strip()


def extract_code_metadata(code: str, language: str) -> Dict[str, Any]:
    """Extract metadata from source code"""
    metadata = {
        "size": len(code),
        "lines": len(code.split('\n')),
        "language": language,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Count functions (language-specific patterns)
    if language == "python":
        metadata["functions"] = len(re.findall(r'^def\s+\w+\s*\(', code, re.MULTILINE))
        metadata["classes"] = len(re.findall(r'^class\s+\w+', code, re.MULTILINE))
        metadata["imports"] = len(re.findall(r'^(?:import|from)\s+\w+', code, re.MULTILINE))
    
    elif language in ["javascript", "typescript"]:
        metadata["functions"] = len(re.findall(r'function\s+\w+\s*\(', code))
        metadata["classes"] = len(re.findall(r'class\s+\w+', code))
        metadata["imports"] = len(re.findall(r'^(?:import|require)', code, re.MULTILINE))
    
    return metadata


def generate_hash(data: str) -> str:
    """Generate SHA256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix