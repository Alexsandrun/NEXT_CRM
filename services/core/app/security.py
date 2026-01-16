from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Session, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def new_token() -> str:
    return f"tok_{uuid4().hex}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def require_bearer_user(db: AsyncSession, request: Request) -> tuple[str, User]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.removeprefix("Bearer ").strip()

    q = select(Session, User).join(User, User.user_id == Session.user_id).where(Session.token == token)
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sess, user = row
    if sess.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    if sess.expires_at <= now_utc():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    return sess.tenant_id, user


async def create_session(db: AsyncSession, tenant_id: str, user: User, request: Request, ttl_hours: int = 12) -> str:
    token = new_token()
    ip = request.client.host if request.client else ""
    ua = request.headers.get("User-Agent", "")

    sess = Session(
        token=token,
        tenant_id=tenant_id,
        user_id=user.user_id,
        expires_at=now_utc() + timedelta(hours=ttl_hours),
        ip=ip,
        user_agent=ua,
    )
    db.add(sess)
    await db.commit()
    return token
