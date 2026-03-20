import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WatchlistType(str, enum.Enum):
    SANCTIONS = "sanctions"
    PEP = "pep"
    ADVERSE_MEDIA = "adverse_media"
    INTERNAL_BLACKLIST = "internal_blacklist"
    CUSTOM = "custom"


class Watchlist(BaseModel):
    __tablename__ = "watchlists"

    list_name: Mapped[str] = mapped_column(String(255), nullable=False)
    list_type: Mapped[WatchlistType] = mapped_column(
        Enum(WatchlistType, name="watchlist_type", create_constraint=True), nullable=False
    )
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_identifiers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
