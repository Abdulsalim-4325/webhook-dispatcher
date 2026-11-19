from typing import List
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    PROJECT_NAME: str = "Sentinel Webhook & Event Dispatch Engine"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production-12345678"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/sentinel_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # Outbound Dispatch Policies
    MAX_DISPATCH_RETRIES: int = 5
    INITIAL_RETRY_DELAY_SECONDS: float = 2.0
    MAX_RETRY_DELAY_SECONDS: float = 60.0
    HTTP_CONNECT_TIMEOUT_SECONDS: float = 2.0
    HTTP_READ_TIMEOUT_SECONDS: float = 5.0
    SSRF_PROTECTION_ENABLED: bool = True


settings = Settings()
