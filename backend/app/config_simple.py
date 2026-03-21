from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    app_name: str = "FinShield AI"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # Database - simplified for demo
    database_url: str = "sqlite+aiosqlite:///./finshield_demo.db"

    # Redis - simplified for demo
    redis_url: str = "memory://"

    # JWT
    jwt_secret: str = "local-dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # ML
    ml_model_path: str = "app/ml/models"
    ml_fraud_model_version: str = "latest"

    # Rate Limiting - disabled for demo
    rate_limit_auth: int = 1000
    rate_limit_data: int = 10000


@lru_cache
def get_settings() -> Settings:
    return Settings()