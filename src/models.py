"""Pydantic models for request/response validation"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


class Language(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"
    QASM = "qasm"
    QISKIT = "qiskit"
    
    @classmethod
    def list_all(cls) -> List[str]:
        """Get list of all supported languages"""
        return [lang.value for lang in cls]


class TranspileOptions(BaseModel):
    """Additional transpilation options"""
    format_code: bool = Field(default=True, description="Format the output code")
    include_comments: bool = Field(default=True, description="Include comments in output")
    strict_mode: bool = Field(default=False, description="Enable strict transpilation mode")
    optimization_level: int = Field(default=1, ge=0, le=3, description="Optimization level (0-3)")
    custom_mappings: Optional[Dict[str, str]] = Field(default=None, description="Custom language mappings")
    
    model_config = ConfigDict(extra="allow")


class TranspileRequest(BaseModel):
    """Transpilation request model"""
    
    source_code: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="Source code to transpile"
    )
    source_lang: Language = Field(
        ..., 
        description="Source programming language"
    )
    target_lang: Language = Field(
        ..., 
        description="Target programming language"
    )
    options: TranspileOptions = Field(
        default_factory=TranspileOptions,
        description="Additional transpilation options"
    )
    
    @field_validator("source_code")
    @classmethod
    def validate_source_code(cls, v: str) -> str:
        """Validate and sanitize source code"""
        if not v or not v.strip():
            raise ValueError("Source code cannot be empty")
        
        # Check for potentially harmful content (basic)
        dangerous_patterns = ["__import__", "eval(", "exec(", "compile("]
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                raise ValueError(f"Source code contains potentially unsafe pattern: {pattern}")
        
        return v.strip()
    
    @model_validator(mode="after")
    def validate_language_pair(self) -> "TranspileRequest":
        """Validate that the language pair is supported"""
        if self.source_lang == self.target_lang:
            raise ValueError("Source and target languages must be different")
        return self
    
    model_config = ConfigDict(use_enum_values=True, json_schema_extra={
        "example": {
            "source_code": "def hello(name):\n    return f'Hello {name}'",
            "source_lang": "python",
            "target_lang": "javascript",
            "options": {
                "format_code": True,
                "optimization_level": 1
            }
        }
    })


class TranspileResponse(BaseModel):
    """Transpilation response model"""
    
    request_id: str = Field(..., description="Unique request identifier")
    source_lang: str = Field(..., description="Source language")
    target_lang: str = Field(..., description="Target language")
    transpiled_code: str = Field(..., description="Transpiled code output")
    warnings: List[str] = Field(default_factory=list, description="Non-critical issues")
    errors: List[str] = Field(default_factory=list, description="Critical errors")
    execution_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    success: bool = Field(..., description="Whether transpilation succeeded")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    cached: bool = Field(default=False, description="Whether response was from cache")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "request_id": "123e4567-e89b-12d3-a456-426614174000",
            "source_lang": "python",
            "target_lang": "javascript",
            "transpiled_code": "function hello(name) {\n    return `Hello ${name}`;\n}",
            "warnings": [],
            "errors": [],
            "execution_time_ms": 45.2,
            "timestamp": "2024-01-15T10:30:00Z",
            "success": True,
            "metadata": {
                "source_length": 42,
                "target_length": 56
            },
            "cached": False
        }
    })


class ErrorResponse(BaseModel):
    """Standard error response model"""
    
    request_id: Optional[str] = Field(None, description="Request ID if available")
    error_code: str = Field(..., description="Error code for identification")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: str = Field(..., description="Request path that caused error")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "request_id": "123e4567-e89b-12d3-a456-426614174000",
            "error_code": "VALIDATION_ERROR",
            "error_message": "Request validation failed",
            "details": {
                "errors": [
                    {
                        "loc": ["body", "source_code"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "path": "/api/v1/transpile"
        }
    })


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    services: Dict[str, bool] = Field(..., description="Status of dependent services")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "version": "1.0.0",
            "environment": "production",
            "timestamp": "2024-01-15T10:30:00Z",
            "uptime_seconds": 86400.5,
            "services": {
                "api": True,
                "transpiler": True,
                "redis": True,
                "database": True
            }
        }
    })


class LanguageInfo(BaseModel):
    """Information about supported languages"""
    
    name: str = Field(..., description="Language name")
    version: Optional[str] = Field(None, description="Language version")
    targets: List[str] = Field(..., description="Supported target languages")
    features: List[str] = Field(default_factory=list, description="Supported features")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "python",
            "version": "3.11",
            "targets": ["javascript", "typescript", "go", "java", "rust", "csharp"],
            "features": ["functions", "classes", "async/await", "type hints"]
        }
    })
    
class LanguagesResponse(BaseModel):
    languages: List[LanguageInfo]
    total_count: int
    
# Request/Response Models
class PackageInstallRequest(BaseModel):
    """Request model for package installation"""
    
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Username for the virtual environment"
    )
    packages: List[str] = Field(
        ..., 
        min_length=1,
        max_length=20,
        description="List of packages to install"
    )
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        # Prevent path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Username contains invalid characters")
        return v.strip()
    
    @field_validator("packages")
    @classmethod
    def validate_packages(cls, v: List[str]) -> List[str]:
        """Validate package names"""
        for package in v:
            # Basic validation to prevent command injection
            if any(char in package for char in [';', '|', '&', '$', '`', '>', '<', '!']):
                raise ValueError(f"Invalid package name: {package}")
        return [p.strip() for p in v]
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "packages": ["requests", "numpy", "pandas"]
            }
        }


class PackageInstallResponse(BaseModel):
    """Response model for package installation"""
    
    job_id: str
    status: str
    username: str
    packages: List[str]
    created_at: str
    message: str = "Installation started"


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    
    job_id: str
    status: str
    username: str
    packages: List[str]
    created_at: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None


class PackageListResponse(BaseModel):
    """Response for listing installed packages"""
    
    username: str
    packages: List[Dict[str, str]]
    environment_path: str
