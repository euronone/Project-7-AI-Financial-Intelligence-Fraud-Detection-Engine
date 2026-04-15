"""CustomerPaymentMethod model — stores payment instruments linked to a customer.

Tracks UPI VPAs, credit cards, and debit cards associated with each customer.
Card numbers are NEVER stored — only last-4 digits and metadata.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


UPI_PROVIDERS = ("gpay", "phonepe", "paytm", "oksbi", "ybl", "ibl", "axl", "airtel")
CARD_NETWORKS = ("visa", "mastercard", "rupay", "amex")
CARD_BANKS = (
    "HDFC Bank",
    "SBI",
    "ICICI Bank",
    "Axis Bank",
    "Kotak Bank",
    "Punjab National Bank",
    "Bank of Baroda",
    "Canara Bank",
    "IndusInd Bank",
    "Yes Bank",
    "IDFC First Bank",
    "Federal Bank",
)


class CustomerPaymentMethod(Base):
    """One payment instrument belonging to one customer."""

    __tablename__ = "customer_payment_methods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # ── What kind of payment instrument ──────────────────────────────────
    payment_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'upi' | 'credit_card' | 'debit_card'

    # ── UPI-specific (null for card types) ───────────────────────────────
    upi_vpa: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upi_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # ── Card-specific (null for UPI) ─────────────────────────────────────
    # We NEVER store actual card numbers.  Only last-4 and metadata.
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_network: Mapped[str | None] = mapped_column(String(20), nullable=True)
    card_expiry_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_expiry_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Ordering ──────────────────────────────────────────────────────────
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Computed display helpers ──────────────────────────────────────────
    def display_label(self) -> str:
        """Human-readable label for UI display."""
        if self.payment_type == "upi":
            return self.upi_vpa or "UPI"
        kind = "Credit" if self.payment_type == "credit_card" else "Debit"
        net = (self.card_network or "Card").title()
        last = self.card_last4 or "****"
        bank = f" ({self.card_bank_name})" if self.card_bank_name else ""
        return f"{kind} {net} •••• {last}{bank}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "payment_type": self.payment_type,
            "upi_vpa": self.upi_vpa,
            "upi_provider": self.upi_provider,
            "card_last4": self.card_last4,
            "card_network": self.card_network,
            "card_expiry_month": self.card_expiry_month,
            "card_expiry_year": self.card_expiry_year,
            "card_bank_name": self.card_bank_name,
            "is_primary": self.is_primary,
            "display_label": self.display_label(),
        }
