from __future__ import annotations

import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/version")
def version():
    return {
        "service": os.getenv("SERVICE_NAME", "core"),
        "env": os.getenv("ENV", "dev"),
        "version": os.getenv("APP_VERSION", "0.1.0-dev"),
        "git_sha": os.getenv("GIT_SHA", "dev"),
    }
