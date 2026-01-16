from __future__ import annotations

import os
from fastapi import FastAPI

from app.api.router import router as api_router

APP_VERSION = os.getenv("APP_VERSION", "0.1.0-dev")

app = FastAPI(title="NextCRM Core", version=APP_VERSION)
app.include_router(api_router)
