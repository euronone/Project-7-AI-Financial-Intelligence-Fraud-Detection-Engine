import math
import uuid
from difflib import SequenceMatcher

import structlog
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.watchlist import Watchlist
from app.schemas.watchlist import (
    ScreeningMatch,
    ScreeningRequest,
    ScreeningResponse,
    WatchlistCreate,
    WatchlistFilters,
    WatchlistListResponse,
    WatchlistResponse,
)

logger = structlog.get_logger()


async def get_watchlist_entry(db: AsyncSession, entry_id: uuid.UUID) -> Watchlist:
    result = await db.execute(select(Watchlist).where(Watchlist.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundException("Watchlist entry", str(entry_id))
    return entry


async def list_watchlist(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    filters: WatchlistFilters | None = None,
) -> WatchlistListResponse:
    query = select(Watchlist)
    count_query = select(func.count()).select_from(Watchlist)

    if filters:
        conditions = _build_filter_conditions(filters)
        if conditions:
            combined = and_(*conditions)
            query = query.where(combined)
            count_query = count_query.where(combined)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Watchlist.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return WatchlistListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[WatchlistResponse.model_validate(w) for w in items],
    )


async def create_watchlist_entry(db: AsyncSession, data: WatchlistCreate) -> Watchlist:
    entry = Watchlist(
        list_name=data.list_name,
        list_type=data.list_type,
        entity_name=data.entity_name,
        entity_identifiers=data.entity_identifiers,
        source=data.source,
        is_active=data.is_active,
        expires_at=data.expires_at,
    )
    db.add(entry)
    await db.flush()
    logger.info("watchlist_entry_created", entry_id=str(entry.id), entity_name=entry.entity_name)
    return entry


async def delete_watchlist_entry(db: AsyncSession, entry_id: uuid.UUID) -> None:
    entry = await get_watchlist_entry(db, entry_id)
    await db.delete(entry)
    await db.flush()
    logger.info("watchlist_entry_deleted", entry_id=str(entry_id))


async def screen_entity(db: AsyncSession, request: ScreeningRequest) -> ScreeningResponse:
    """Fuzzy-match an entity name against active watchlist entries."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.is_active == True)  # noqa: E712
    )
    entries = result.scalars().all()

    matches: list[ScreeningMatch] = []
    query_lower = request.entity_name.lower()

    for entry in entries:
        score = SequenceMatcher(None, query_lower, entry.entity_name.lower()).ratio()
        if score >= 0.6:
            matches.append(
                ScreeningMatch(
                    watchlist_id=entry.id,
                    list_name=entry.list_name,
                    list_type=entry.list_type,
                    entity_name=entry.entity_name,
                    source=entry.source,
                    match_score=round(score, 4),
                )
            )

    matches.sort(key=lambda m: m.match_score, reverse=True)
    logger.info("screening_completed", query=request.entity_name, matches=len(matches))

    return ScreeningResponse(
        query=request.entity_name,
        matches=matches[:50],
        total_matches=len(matches),
    )


def _build_filter_conditions(filters: WatchlistFilters) -> list:
    conditions = []
    if filters.list_type:
        conditions.append(Watchlist.list_type == filters.list_type)
    if filters.source:
        conditions.append(Watchlist.source == filters.source)
    if filters.is_active is not None:
        conditions.append(Watchlist.is_active == filters.is_active)
    if filters.search:
        conditions.append(Watchlist.entity_name.ilike(f"%{filters.search}%"))
    return conditions
