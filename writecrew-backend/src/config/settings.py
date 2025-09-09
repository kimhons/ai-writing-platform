"""
WriteCrew Backend Configuration Settings
Environment-based configuration with Pydantic
"""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "WriteCrew Backend"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    
    # AI Providers
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, env="OPENAI_API_BASE")
    openai_organization: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")
    
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    
    together_api_key: str = Field(..., env="TOGETHER_API_KEY")
    
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # CrewAI Configuration
    crewai_max_agents: int = Field(default=19, env="CREWAI_MAX_AGENTS")
    crewai_max_concurrent_tasks: int = Field(default=10, env="CREWAI_MAX_CONCURRENT_TASKS")
    crewai_task_timeout: int = Field(default=300, env="CREWAI_TASK_TIMEOUT")  # 5 minutes
    
    # Agent Configuration
    agent_response_timeout: int = Field(default=30, env="AGENT_RESPONSE_TIMEOUT")
    agent_retry_attempts: int = Field(default=3, env="AGENT_RETRY_ATTEMPTS")
    agent_retry_delay: float = Field(default=1.0, env="AGENT_RETRY_DELAY")
    
    # WebSocket Configuration
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    websocket_max_connections: int = Field(default=1000, env="WEBSOCKET_MAX_CONNECTIONS")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst_size: int = Field(default=10, env="RATE_LIMIT_BURST_SIZE")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    
    # File Storage
    upload_max_size: int = Field(default=10 * 1024 * 1024, env="UPLOAD_MAX_SIZE")  # 10MB
    upload_allowed_types: List[str] = Field(
        default=["docx", "doc", "txt", "md", "pdf"],
        env="UPLOAD_ALLOWED_TYPES"
    )
    
    # Task Queue
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("upload_allowed_types", pre=True)
    def parse_upload_types(cls, v):
        """Parse upload types from string or list"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format"""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"
    
    # Development AI API keys (if different)
    openai_api_key: str = Field(default="sk-dev-key", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="dev-key", env="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="dev-key", env="GOOGLE_API_KEY")
    together_api_key: str = Field(default="dev-key", env="TOGETHER_API_KEY")


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "INFO"
    
    # Production security
    allowed_origins: List[str] = Field(
        default=["https://writecrew.com", "https://app.writecrew.com"],
        env="ALLOWED_ORIGINS"
    )


class TestSettings(Settings):
    """Test environment settings"""
    debug: bool = True
    database_url: str = Field(default="sqlite:///./test.db", env="TEST_DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/15", env="TEST_REDIS_URL")
    
    # Test API keys
    openai_api_key: str = "test-key"
    anthropic_api_key: str = "test-key"
    google_api_key: str = "test-key"
    together_api_key: str = "test-key"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Export settings instance
settings = get_settings()

