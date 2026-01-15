from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.errors import http_error, new_trace_id
from ..db import get_db_session
from ..models.identity import User
from .jwt_tokens import decode_token


@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    user_id: str
    email: str


async def require_auth(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = next(get_db_session()),  # overwritten by FastAPI Depends below
) -> AuthContext:
    # NOTE: this function is wired via Depends(require_auth_dep) below
    raise RuntimeError("Use require_auth_dep (FastAPI Depends wrapper).")


async def require_auth_dep(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = None,
) -> AuthContext:
    """
    FastAPI dependency:
    - validates Bearer token
    - loads user
    - returns AuthContext(tenant_id, user_id, email)
    """
    trace_id = new_trace_id()

    if not authorization or not authorization.lower().startswith("bearer "):
        raise http_error(status_code=401, code="AUTH.MISSING_TOKEN", message="Missing Bearer token.", trace_id=trace_id)

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception:
        raise http_error(status_code=401, code="AUTH.INVALID_TOKEN", message="Invalid or expired token.", trace_id=trace_id)

    tenant_id = payload.get("tenant_id")
    user_id = payload.get("sub")
    email = payload.get("email")

    if not tenant_id or not user_id:
        raise http_error(status_code=401, code="AUTH.INVALID_TOKEN", message="Token missing required claims.", trace_id=trace_id)

    # DB check: user exists + active + not locked
    if db is None:
        # fallback safety: resolve session manually
        async for s in get_db_session():
            db = s
            break

    user = (await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))).scalar_one_or_none()
    if user is None:
        raise http_error(status_code=401, code="AUTH.INVALID_TOKEN", message="Unknown user.", trace_id=trace_id)
    if not user.is_active or user.is_locked:
        raise http_error(status_code=403, code="AUTH.USER_LOCKED", message="User is locked or inactive.", trace_id=trace_id)

    return AuthContext(tenant_id=tenant_id, user_id=user_id, email=email or user.email)


# END_FILE
