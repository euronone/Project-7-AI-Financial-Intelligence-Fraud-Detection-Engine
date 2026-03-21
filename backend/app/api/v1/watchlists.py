import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.watchlist import (
    ScreeningRequest,
    ScreeningResponse,
    WatchlistCreate,
    WatchlistFilters,
    WatchlistListResponse,
    WatchlistResponse,
)
from app.services import watchlist_service

router = APIRouter()


@router.get("", response_model=WatchlistListResponse)
async def list_watchlist(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    list_type: str | None = None,
    source: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> WatchlistListResponse:
    filters = WatchlistFilters(
        list_type=list_type,
        source=source,
        is_active=is_active,
        search=search,
    )
    return await watchlist_service.list_watchlist(db, page=page, page_size=page_size, filters=filters)


@router.post("", response_model=WatchlistResponse, status_code=201)
async def add_watchlist_entry(
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> WatchlistResponse:
    entry = await watchlist_service.create_watchlist_entry(db, data)
    return WatchlistResponse.model_validate(entry)


@router.delete("/{entry_id}", response_model=MessageResponse)
async def remove_watchlist_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> MessageResponse:
    await watchlist_service.delete_watchlist_entry(db, entry_id)
    return MessageResponse(message="Watchlist entry removed")


@router.post("/screen", response_model=ScreeningResponse)
async def screen_entity(
    request: ScreeningRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> ScreeningResponse:
    return await watchlist_service.screen_entity(db, request)
