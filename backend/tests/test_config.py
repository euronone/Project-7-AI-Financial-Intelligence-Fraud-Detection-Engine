"""Unit tests for application Settings / configuration."""

from app.config import get_settings, Settings


class TestSettingsDefaults:
    def test_app_name(self):
        s = get_settings()
        assert s.APP_NAME == "FinShield AI"

    def test_app_version(self):
        s = get_settings()
        assert s.APP_VERSION == "1.0.0"

    def test_jwt_algorithm_is_hs256(self):
        s = get_settings()
        assert s.JWT_ALGORITHM == "HS256"

    def test_access_token_expire_minutes_positive(self):
        s = get_settings()
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_refresh_token_expire_days_positive(self):
        s = get_settings()
        assert s.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0


class TestSettingsProperties:
    def test_cors_origins_list_single(self):
        s = Settings(CORS_ORIGINS="http://localhost:3000")
        result = s.cors_origins_list
        assert result == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self):
        s = Settings(CORS_ORIGINS="http://localhost:3000,https://app.example.com")
        result = s.cors_origins_list
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "https://app.example.com" in result

    def test_cors_origins_list_strips_spaces(self):
        s = Settings(CORS_ORIGINS="http://a.com , http://b.com")
        result = s.cors_origins_list
        assert "http://a.com" in result
        assert "http://b.com" in result

    def test_is_development_true(self):
        s = Settings(APP_ENV="development")
        assert s.is_development is True

    def test_is_development_false_for_production(self):
        s = Settings(APP_ENV="production")
        assert s.is_development is False

    def test_is_development_false_for_staging(self):
        s = Settings(APP_ENV="staging")
        assert s.is_development is False

    def test_is_sqlite_true(self):
        s = Settings(DATABASE_URL="sqlite+aiosqlite:///./dev.db")
        assert s.is_sqlite is True

    def test_is_sqlite_false_for_postgres(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host/db")
        assert s.is_sqlite is False


class TestEncryptionKeyPresence:
    def test_encryption_key_is_set(self):
        """ENCRYPTION_KEY must always be configured (set by conftest for tests)."""
        s = get_settings()
        assert s.ENCRYPTION_KEY != ""

    def test_jwt_secret_is_set(self):
        s = get_settings()
        assert s.JWT_SECRET != ""
