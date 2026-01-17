from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    auth,
    bootstrap,
    companies,
    contacts,
    deals,
    health,
    logout,
    pipelines,
    stages,
    version,
    board,
)

api_router = APIRouter()

# base endpoints
api_router.include_router(health.router)
api_router.include_router(version.router)
api_router.include_router(bootstrap.router)

# auth endpoints
api_router.include_router(auth.router)
api_router.include_router(logout.router)

# domain endpoints
api_router.include_router(companies.router)
api_router.include_router(contacts.router)
api_router.include_router(pipelines.router)
api_router.include_router(stages.router)
api_router.include_router(deals.router)

# board endpoint
api_router.include_router(board.router)

router = api_router
