"""Application configuration — loaded from .env via pydantic-settings."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Search for .env in the project root (../) first, then fall back to
        # the current working directory.  When running from backend/ the root
        # .env is at ../.env.  Docker passes vars via environment, so both
        # paths are tried gracefully with no error if a file is absent.
        env_file=["../.env", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "FinShield AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./finshield_dev.db"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change-this-in-production-use-random-256-bit-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Email — Resend is primary; Brevo is a supported fallback provider
    RESEND_API_KEY: str = ""
    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@finshield.ai"
    EMAIL_FROM_NAME: str = "FinShield AI"

    # SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Fraud alert notification targets
    ALERT_COMPANY_EMAIL: str = ""  # Where company fraud alerts are sent
    ALERT_SMS_ENABLED: bool = True  # Toggle Twilio SMS for fraud alerts

    # Firebase Cloud Messaging (optional — push notifications for Pro/Advanced)
    FIREBASE_SERVER_KEY: str = ""  # Legacy FCM HTTP server key (starts with AAAA...)

    # ML
    ML_MODEL_PATH: str = "app/ml/models"
    ML_FRAUD_MODEL_VERSION: str = "latest"

    # Encryption
    ENCRYPTION_KEY: str = "dev-key-change-in-production-32b"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
