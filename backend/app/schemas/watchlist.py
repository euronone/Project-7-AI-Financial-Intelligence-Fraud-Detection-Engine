import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.watchlist import WatchlistType


class WatchlistFilters(BaseModel):
    list_type: WatchlistType | None = None
    source: str | None = None
    is_active: bool | None = None
    search: str | None = None


class WatchlistCreate(BaseModel):
    list_name: str = Field(min_length=1, max_length=255)
    list_type: WatchlistType
    entity_name: str = Field(min_length=1, max_length=500)
    entity_identifiers: dict = Field(default_factory=dict)
    source: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    expires_at: datetime | None = None


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    list_name: str
    list_type: WatchlistType
    entity_name: str
    entity_identifiers: dict
    source: str
    match_score: Decimal | None
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WatchlistListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[WatchlistResponse]


class ScreeningRequest(BaseModel):
    entity_name: str = Field(min_length=1)
    entity_type: str | None = None
    country_code: str | None = None


class ScreeningMatch(BaseModel):
    watchlist_id: uuid.UUID
    list_name: str
    list_type: WatchlistType
    entity_name: str
    source: str
    match_score: float


class ScreeningResponse(BaseModel):
    query: str
    matches: list[ScreeningMatch]
    total_matches: int
