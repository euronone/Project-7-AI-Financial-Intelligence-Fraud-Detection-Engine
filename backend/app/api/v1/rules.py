import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.rule import (
    RuleCreate,
    RuleListResponse,
    RulePerformance,
    RuleResponse,
    RuleTestRequest,
    RuleTestResult,
    RuleToggleRequest,
    RuleUpdate,
)
from app.services import rules_engine_service

router = APIRouter()


@router.get("", response_model=RuleListResponse)
async def list_rules(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    is_active: bool | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RuleListResponse:
    return await rules_engine_service.list_rules(
        db, page=page, page_size=page_size, is_active=is_active, category=category
    )


@router.get("/templates")
async def get_templates(
    _user: User = Depends(require_viewer),
) -> list[dict]:
    return rules_engine_service.get_rule_templates()


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RuleResponse:
    rule = await rules_engine_service.get_rule(db, rule_id)
    return RuleResponse.model_validate(rule)


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> RuleResponse:
    rule = await rules_engine_service.create_rule(db, data, user.id)
    return RuleResponse.model_validate(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> RuleResponse:
    rule = await rules_engine_service.update_rule(db, rule_id, data)
    return RuleResponse.model_validate(rule)


@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    rule_id: uuid.UUID,
    body: RuleToggleRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> RuleResponse:
    rule = await rules_engine_service.toggle_rule(db, rule_id, body.is_active)
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> MessageResponse:
    await rules_engine_service.delete_rule(db, rule_id)
    return MessageResponse(message="Rule deleted")


@router.post("/{rule_id}/test", response_model=RuleTestResult)
async def test_rule(
    rule_id: uuid.UUID,
    body: RuleTestRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RuleTestResult:
    return await rules_engine_service.test_rule(db, rule_id, body.transaction)


@router.get("/{rule_id}/performance", response_model=RulePerformance)
async def get_performance(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RulePerformance:
    return await rules_engine_service.get_rule_performance(db, rule_id)
