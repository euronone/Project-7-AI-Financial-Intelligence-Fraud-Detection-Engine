"""
OTP Service — manages one-time passwords with automatic TTL and cleanup.
Replaces in-memory dict in transactions.py.

For production: use Redis with automatic expiry.
"""
import random
import string
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# For development: in-memory store with manual cleanup
# For production: migrate to Redis
class OTPManager:
    """Simple OTP manager with TTL and background cleanup."""

    def __init__(self, expiry_minutes: int = 5, cleanup_interval_seconds: int = 60):
        """
        Args:
            expiry_minutes: How long OTP is valid
            cleanup_interval_seconds: How often to clean expired entries
        """
        self.expiry_minutes = expiry_minutes
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._store: dict[str, dict] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("OTP cleanup task started")

    async def _cleanup_loop(self):
        """Periodically clean expired OTP entries."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval_seconds)
                self._cleanup_expired()
        except asyncio.CancelledError:
            logger.info("OTP cleanup task cancelled")
            raise

    def _cleanup_expired(self):
        """Remove expired OTP entries."""
        now = datetime.now(timezone.utc)
        expired = [
            txn_id for txn_id, data in self._store.items()
            if now > data["expires"]
        ]
        for txn_id in expired:
            del self._store[txn_id]
        if expired:
            logger.debug(f"OTP cleanup: removed {len(expired)} expired entries")

    def generate(self, transaction_id: str, length: int = 6) -> str:
        """
        Generate and store an OTP for a transaction.

        Args:
            transaction_id: Unique transaction ID
            length: OTP digit length (default 6)

        Returns:
            6-digit OTP string
        """
        otp = "".join(random.choices(string.digits, k=length))
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.expiry_minutes)

        self._store[transaction_id] = {
            "otp": otp,
            "expires": expires,
            "attempts": 0
        }

        logger.info(f"OTP generated for transaction {transaction_id}")
        return otp

    def verify(self, transaction_id: str, otp: str, max_attempts: int = 3) -> bool:
        """
        Verify an OTP for a transaction.

        Args:
            transaction_id: Transaction ID
            otp: OTP to verify
            max_attempts: Max verification attempts before expiry

        Returns:
            True if OTP is valid, False otherwise
        """
        data = self._store.get(transaction_id)

        if not data:
            logger.warning(f"OTP verification: no OTP for {transaction_id}")
            return False

        now = datetime.now(timezone.utc)
        if now > data["expires"]:
            del self._store[transaction_id]
            logger.warning(f"OTP verification: expired for {transaction_id}")
            return False

        data["attempts"] += 1
        if data["attempts"] > max_attempts:
            del self._store[transaction_id]
            logger.warning(f"OTP verification: max attempts exceeded for {transaction_id}")
            return False

        if data["otp"] != otp:
            logger.warning(f"OTP verification: incorrect OTP for {transaction_id}")
            return False

        # Valid! Remove it
        del self._store[transaction_id]
        logger.info(f"OTP verification: success for {transaction_id}")
        return True

    def get_remaining_time(self, transaction_id: str) -> Optional[int]:
        """Get remaining seconds for an OTP, or None if expired/not found."""
        data = self._store.get(transaction_id)
        if not data:
            return None

        remaining = (data["expires"] - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    async def stop_cleanup(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Global singleton
otp_manager = OTPManager()
