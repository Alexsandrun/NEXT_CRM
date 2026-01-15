from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, bootstrap

api_router = APIRouter()
api_router.include_router(bootstrap.router, tags=["bootstrap"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# END_FILE
