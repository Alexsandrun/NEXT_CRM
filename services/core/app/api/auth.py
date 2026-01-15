from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tenancy import Tenant
from ..models.identity import User
from ..security.passwords import verify_password
from ..security.jwt_tokens import issue_token


async def authenticate(
    db: AsyncSession, *, tenant_slug: str, email: str, password: str
) -> tuple[str | None, dict | None]:
    tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one_or_none()
    if tenant is None:
        return None, {"code": "AUTH.INVALID_TENANT", "message": "Unknown tenant.", "retryable": False}

    user = (
        await db.execute(
            select(User).where(User.tenant_id == tenant.id, User.email == email.lower())
        )
    ).scalar_one_or_none()
    if user is None:
        return None, {"code": "AUTH.INVALID_CREDENTIALS", "message": "Invalid credentials.", "retryable": False}

    if not user.is_active or user.is_locked:
        return None, {"code": "AUTH.USER_LOCKED", "message": "User is locked or inactive.", "retryable": False}

    if not verify_password(password, user.password_hash):
        return None, {"code": "AUTH.INVALID_CREDENTIALS", "message": "Invalid credentials.", "retryable": False}

    token = issue_token(tenant_id=tenant.id, user_id=user.id, email=user.email)
    return token, {"tenant_id": tenant.id, "user_id": user.id, "email": user.email}
