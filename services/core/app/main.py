from __future__ import annotations

import os

from app.api.router import api_router as api_router
from fastapi import FastAPI

APP_ENV = os.getenv("ENV", "dev")
LOG_MODE = os.getenv("LOG_MODE", "normal")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0-dev")
GIT_SHA = os.getenv("GIT_SHA", "dev")

app = FastAPI(title="NextCRM Core", version=APP_VERSION)
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "core", "env": APP_ENV, "log_mode": LOG_MODE}


@app.get("/version")
def version():
    return {
        "service": "core",
        "env": APP_ENV,
        "version": APP_VERSION,
        "git_sha": GIT_SHA,
    }
