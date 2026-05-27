"""
Configuración de la aplicación usando Pydantic Settings.
"""
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Incapacidades API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6389/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Storage Configuration
    STORAGE_BACKEND: str = "filesystem"  # "filesystem" | "minio"
    
    # Filesystem Storage (cuando STORAGE_BACKEND=filesystem)
    FILESYSTEM_BASE_PATH: str = "/app/storage"
    FILESYSTEM_SERVE_FILES: bool = True
    
    # MinIO/S3 Storage (cuando STORAGE_BACKEND=minio)
    STORAGE_ENDPOINT: str = "localhost:9010"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "incapacidades"
    STORAGE_SECURE: bool = False
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5682//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6389/1"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAIL_FROM: str = "noreply@incapacidades.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # External APIs
    API_RRHH_BASE_URL: Optional[str] = None
    API_RRHH_API_KEY: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]
    
    # Business Rules
    SLA_RADICADA_DIAS: int = 1
    SLA_EN_AUDITORIA_DIAS: int = 5
    SLA_OBSERVADA_DIAS: int = 10
    SLA_APROBADA_DIAS: int = 3
    SLA_EN_PAGO_DIAS: int = 10


# Create settings instance
settings = Settings()
