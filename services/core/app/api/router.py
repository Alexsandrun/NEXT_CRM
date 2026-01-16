from __future__ import annotations

from app.api import (
    auth,
    bootstrap,
    companies,
    contacts,
    deals,
    health,
    logout,
    pipelines, stages,
    version,
)
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(version.router)
api_router.include_router(bootstrap.router)

api_router.include_router(auth.router)
api_router.include_router(logout.router)

api_router.include_router(companies.router)
api_router.include_router(contacts.router)

api_router.include_router(pipelines.router)
api_router.include_router(stages.router)
api_router.include_router(deals.router)

router = api_router
