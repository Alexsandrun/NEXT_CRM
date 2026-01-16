from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Session
from app.security import require_bearer_user

router = APIRouter()

def now_utc():
    return datetime.now(timezone.utc)

@router.post("/auth/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    # валидируем токен и получаем user
    tenant_id, user = await require_bearer_user(db, request)

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    q = select(Session).where(Session.token == token)
    sess = (await db.execute(q)).scalar_one()

    sess.revoked_at = now_utc()
    await db.commit()

    return {"ok": True, "tenant_id": tenant_id, "user_id": user.user_id}
