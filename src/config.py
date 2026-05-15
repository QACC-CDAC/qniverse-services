"""Configuration management with environment variables"""

from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SecretStr
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="Transpilation API")
    VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Package Installation Settings
    PACKAGE_BASE_DIR: str = Field(default="/home/qacc/qns-custom-packages")
    MAX_PACKAGES_PER_REQUEST: int = Field(default=20)
    PACKAGE_INSTALL_TIMEOUT: int = Field(default=300)  # 5 minutes
    PACKAGE_CLEANUP_AGE_HOURS: int = Field(default=24)
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8001)
    WORKERS: int = Field(default=4)
    
    # Security
    SECRET_KEY: SecretStr = Field(default=SecretStr(secrets.token_urlsafe(32)))
    API_KEY_HEADER: str = Field(default="X-API-Key")
    API_KEYS: List[str] = Field(default=["my-secret-key","qniverse:Vyvj7SNW4DJXJYRJurqvQSvB7lnM7ouXle0nYZcuJDQ6BC2g9aAnPqlKUhAOav82wYnHaoH2lpABDZ3CYmGiN9LKZJYrgDcbvrDRvgveEJE9vE8BCA63ZvytSPFA3L2d2KtdZCWB8lbmGGRCyFiseLy2FZo4RQ25uWgYY87hiqfnBJdgP60F7fynCWORk0JAJZilHFSUfgbk605LoxOkJADJUfySBWigNa4HujGQYoJsSXEZW6gufS74N6dBWBdK"])
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_PERIOD: int = Field(default=60)
    
    # Redis Configuration
    REDIS_URL: Optional[str] = Field(default=None)
    REDIS_MAX_CONNECTIONS: int = Field(default=10)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    ENABLE_CACHE: bool = Field(default=True)
    CACHE_TTL_SECONDS: int = Field(default=3600)
    
    # Database
    DATABASE_URL: Optional[str] = Field(default=None)
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=40)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default="logs/transpilation_api.log")
    LOG_MAX_SIZE: str = Field(default="500MB")
    LOG_BACKUP_COUNT: int = Field(default=10)
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    ALLOWED_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    ALLOWED_HEADERS: List[str] = Field(default=["*"])
    
    # Transpilation
    MAX_CODE_LENGTH: int = Field(default=50000)
    MAX_TIMEOUT_SECONDS: int = Field(default=30)
    ENABLE_CODE_VALIDATION: bool = Field(default=True)
    
    SUPPORTED_LANGUAGES: Dict[str, List[str]] = Field(default={
        "qasm": ["qiskit","cirq","qasm", "quil", "cudaq", "qulacs", "quest", "qi"],
    })
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True)
    PROMETHEUS_PORT: int = Field(default=9090)
    SENTRY_DSN: Optional[str] = Field(default=None)
    
    # Feature Flags
    ENABLE_ASYNC_TRANSPILATION: bool = Field(default=False)
    ENABLE_PERFORMANCE_METRICS: bool = Field(default=True)
    
    @field_validator("API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v or []
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated allowed origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or ["*"]
    
    @field_validator("SUPPORTED_LANGUAGES", mode="before")
    @classmethod
    def validate_supported_languages(cls, v):
        """Ensure supported languages dict is valid"""
        if isinstance(v, dict):
            return v
        return {}
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()