from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.security import create_session, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    tenant: str
    email: str
    password: str


@router.post("/auth/login")
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # ищем активного юзера в tenant
    q = select(User).where(
        User.tenant_id == payload.tenant,
        User.email == payload.email.lower(),
        User.is_active == True,  # noqa: E712
    )
    user = (await db.execute(q)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = await create_session(db, payload.tenant, user, request)

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": payload.tenant,
        "user_id": user.user_id,
        "trace_id": uuid.uuid4().hex,
    }


@router.get("/auth/whoami")
async def whoami(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    # В security.require_bearer_user мы читаем request.headers, так что Header-параметр
    # тут нужен только чтобы OpenAPI явно показывал, что хедер используется.
    _ = authorization

    tenant_id, user = await __require(db, request)

    return {
        "tenant_id": tenant_id,
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "trace_id": uuid.uuid4().hex,
    }


async def __require(db: AsyncSession, request: Request):
    # обёртка, чтобы не тащить require_bearer_user в OpenAPI как dependency
    from app.security import require_bearer_user

    return await require_bearer_user(db, request)
