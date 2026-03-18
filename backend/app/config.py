"""Application configuration using pydantic-settings.

All secrets and environment-specific values are read from environment variables.
Never hardcode credentials or URLs in this file.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://finshield:localdev123@localhost:5432/finshield"
    )
    db_pool_min_size: int = Field(default=10)
    db_pool_max_size: int = Field(default=100)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_pool_size: int = Field(default=20)

    # JWT
    jwt_secret: str = Field(default="local-dev-secret-change-in-prod")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Azure Event Hub (Kafka-compatible)
    event_hub_connection_string: str = Field(default="")
    event_hub_namespace: str = Field(default="")
    event_hub_transactions_name: str = Field(default="transactions")
    event_hub_alerts_name: str = Field(default="alerts")
    event_hub_consumer_group: str = Field(default="fraud-processor")

    # Azure Storage
    azure_storage_connection_string: str = Field(default="")
    azure_storage_container_exports: str = Field(default="exports")

    # ML
    ml_model_path: str = Field(default="app/ml/models")
    ml_fraud_model_version: str = Field(default="latest")

    # Email (MailHog in dev, SendGrid/Azure in prod)
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=1025)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")

    # Rate limiting
    rate_limit_auth_per_minute: int = Field(default=100)
    rate_limit_api_per_minute: int = Field(default=1000)

    # Fraud pipeline
    fraud_pipeline_timeout_ms: int = Field(default=180)
    batch_ingest_chunk_size: int = Field(default=500)
    batch_ingest_max_size: int = Field(default=10000)

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
