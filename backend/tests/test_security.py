"""Unit tests for JWT token creation/verification and password hashing."""

import pytest
import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    def test_hash_returns_string(self):
        hashed = hash_password("mysecret")
        assert isinstance(hashed, str)

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"

    def test_hash_starts_with_bcrypt_prefix(self):
        hashed = hash_password("password123")
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """Bcrypt uses random salt — same input produces different hashes."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True


class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_returns_payload(self):
        token = create_access_token({"sub": "user-abc", "tenant_id": "t-1"})
        payload = decode_token(token)
        assert payload["sub"] == "user-abc"
        assert payload["tenant_id"] == "t-1"

    def test_access_token_type_field(self):
        token = create_access_token({"sub": "u1"})
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_type_field(self):
        token = create_refresh_token({"sub": "u1"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_access_token_has_exp(self):
        token = create_access_token({"sub": "u1"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_token("this.is.not.a.valid.jwt")

    def test_tampered_token_raises(self):
        token = create_access_token({"sub": "u1"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decode_token(tampered)

    def test_wrong_secret_raises(self):
        """Token signed with a different secret should not verify."""
        bad_token = jwt.encode(
            {"sub": "u1", "type": "access"},
            "completely-different-secret",
            algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(Exception):
            decode_token(bad_token)
