import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import get_current_user_id
from app.dependencies import get_db
from app.models.user import User, UserRole


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolves the full User object from the JWT subject."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias for get_current_user with active check (already handled)."""
    return current_user


class RequireRole:
    """Dependency that enforces one or more allowed roles.

    Usage in a route:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(RequireRole(UserRole.ADMIN))):
            ...
    """

    def __init__(self, *allowed_roles: UserRole) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(
                f"Role '{current_user.role.value}' is not authorized for this resource"
            )
        return current_user


require_admin = RequireRole(UserRole.ADMIN)
require_analyst = RequireRole(UserRole.ADMIN, UserRole.ANALYST)
require_investigator = RequireRole(UserRole.ADMIN, UserRole.ANALYST, UserRole.INVESTIGATOR)
require_viewer = RequireRole(UserRole.ADMIN, UserRole.ANALYST, UserRole.INVESTIGATOR, UserRole.VIEWER)
