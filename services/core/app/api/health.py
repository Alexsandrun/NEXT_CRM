from __future__ import annotations

from fastapi import APIRouter

from app.settings import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "service": "core", "env": settings.env, "log_mode": settings.log_mode}
