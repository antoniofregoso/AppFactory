from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        case_sensitive=True,
    )

    # App Config
    APP_NAME: str = "API"
    APP_VERSION: str = "0.0.1"
    DEFAULT_TIMEZONE: str = "UTC"
    SEARCH_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0)
    SEARCH_AUDIT_RETENTION_DAYS: int = Field(default=30, gt=0)
    SEARCH_AI_PROVIDER: str = ""
    SEARCH_AI_API_KEY: SecretStr = SecretStr("")
    SEARCH_AI_MODEL: str = ""
    SEARCH_AI_BASE_URL: str = "https://api.openai.com/v1"
    SEARCH_AI_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0)

    # Database Config
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=20, gt=0)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0)

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security / JWT Config
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_ABSOLUTE_EXPIRE_DAYS: int = 30
    MCP_TOKEN_EXPIRE_DAYS: int = 30
    USER_LOG_STALE_TIMEOUT_SECONDS: int = 300
    USER_LOG_SWEEP_INTERVAL_SECONDS: int = 60
    TASK_REMINDER_EARLY_MINUTES: int = 30
    TASK_REMINDER_FINAL_MINUTES: int = 5
    TASK_REMINDER_SWEEP_INTERVAL_SECONDS: int = 60

    # Web Push (browser notifications while the app/tab is closed)
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"
    JWT_ISSUER: str = "webapp-api"
    JWT_AUDIENCE: str = "webapp-client"
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_CSRF_COOKIE_NAME: str = "refresh_csrf"
    REFRESH_CSRF_HEADER_NAME: str = "X-CSRF-Token"
    REFRESH_COOKIE_SECURE: bool = True
    REFRESH_COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_PATH: str = "/graphql"

    # CORS Config
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["GET", "POST", "OPTIONS"]
    CORS_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
    ]

    # Attachment filestore
    FILESTORE_ROOT: Path = Path("data/filestore")
    FILESTORE_NAMESPACE: Optional[str] = None
    ATTACHMENT_MAX_SIZE_BYTES: int = 25 * 1024 * 1024
    ATTACHMENT_ALLOWED_CONTENT_TYPES: list[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/webp",
        "text/csv",
        "text/plain",
    ]


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
