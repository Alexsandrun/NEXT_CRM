from __future__ import annotations

import os
from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="NEXT_CRM Core", version="0.1.0-dev")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "core",
        "env": os.getenv("APP_ENV", "dev"),
        "log_mode": os.getenv("LOG_MODE", "normal"),
    }

# core internal routes (no /api prefix here; gateway strips /api/)
app.include_router(api_router)
# END_FILE
