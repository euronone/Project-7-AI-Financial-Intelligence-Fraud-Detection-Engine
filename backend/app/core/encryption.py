"""
API Key Encryption Module — Secures sensitive credentials at rest.

Uses Fernet (symmetric encryption) to encrypt/decrypt API keys and secrets
before storing/retrieving from the database.
"""

import logging
from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

logger = logging.getLogger(__name__)


class APIKeyEncryptor:
    """Encrypts and decrypts sensitive API keys for secure storage."""

    # Fields that should be encrypted before storage
    SENSITIVE_FIELDS = {
        # Supabase
        "supabase_anon_key",
        "supabase_service_key",
        # PostgreSQL / MySQL
        "db_password",
        "password",
        # Generic API keys
        "api_key",
        "secret_key",
        "access_token",
        "refresh_token",
        # AWS
        "aws_secret_access_key",
        "aws_access_key_id",
        # Twilio
        "twilio_auth_token",
        "twilio_account_sid",
        # Email services
        "resend_api_key",
        "sendgrid_api_key",
        "smtp_password",
        # Firebase
        "firebase_service_account_json",
        # Payment gateways
        "stripe_secret_key",
        "razorpay_secret",
        # Other
        "webhook_secret",
        "encryption_key",
        "planetscale_password",
        "mongodb_connection_string",
    }

    def __init__(self):
        """Initialize encryptor with encryption key from settings."""
        settings = get_settings()

        if not settings.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY not set in environment. "
                'Generate with: python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            )

        try:
            # ENCRYPTION_KEY should be a URL-safe base64-encoded 32-byte key
            self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception as exc:
            logger.error("Failed to initialize encryption cipher: %s", exc)
            raise ValueError("Invalid ENCRYPTION_KEY format") from exc

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext secret.

        Args:
            plaintext: Raw secret to encrypt

        Returns:
            Encrypted secret (base64-encoded)
        """
        if not plaintext:
            return plaintext

        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as exc:
            logger.error("Encryption failed: %s", exc)
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted secret.

        Args:
            ciphertext: Encrypted secret (base64-encoded)

        Returns:
            Decrypted plaintext secret

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not ciphertext:
            return ciphertext

        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken as exc:
            logger.error("Decryption failed: invalid token or corrupted data")
            raise ValueError("Failed to decrypt secret - wrong encryption key?") from exc
        except Exception as exc:
            logger.error("Decryption error: %s", exc)
            raise

    def encrypt_config(self, config: dict) -> dict:
        """
        Encrypt all sensitive fields in a configuration dict.

        Args:
            config: Dict with potential sensitive values

        Returns:
            Copy of config with sensitive fields encrypted
        """
        encrypted_config = config.copy()

        for field in self.SENSITIVE_FIELDS:
            if field in encrypted_config and encrypted_config[field]:
                try:
                    encrypted_config[field] = self.encrypt(encrypted_config[field])
                except Exception as exc:
                    logger.error("Failed to encrypt field %s: %s", field, exc)
                    raise

        return encrypted_config

    def decrypt_config(self, config: dict) -> dict:
        """
        Decrypt all sensitive fields in a configuration dict.

        Args:
            config: Dict with encrypted sensitive values

        Returns:
            Copy of config with sensitive fields decrypted
        """
        decrypted_config = config.copy()

        for field in self.SENSITIVE_FIELDS:
            if field in decrypted_config and decrypted_config[field]:
                try:
                    decrypted_config[field] = self.decrypt(decrypted_config[field])
                except Exception as exc:
                    logger.warning(
                        "Failed to decrypt field %s: %s (may be plaintext from old data)",
                        field,
                        exc,
                    )
                    # Don't fail hard — field might be plaintext from before encryption was added
                    # This allows gradual migration of existing data

        return decrypted_config


# Global singleton instance
encryptor = APIKeyEncryptor()
