from __future__ import annotations

import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

TENANT = os.getenv("BOOTSTRAP_TENANT", "demo")
ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@demo.local")
ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123")

def trace_id() -> str:
    return uuid.uuid4().hex

class LoginIn(BaseModel):
    tenant: str = Field(..., description="Tenant slug")
    email: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    trace_id: str

@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    tid = trace_id()

    if body.tenant != TENANT:
        raise HTTPException(status_code=404, detail={"code": "AUTH.INVALID_TENANT", "trace_id": tid})

    if body.email != ADMIN_EMAIL or body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail={"code": "AUTH.INVALID_CREDENTIALS", "trace_id": tid})

    return LoginOut(
        access_token=f"devtoken.{uuid.uuid4().hex}",
        tenant_id=TENANT,
        user_id="u_admin_dev",
        trace_id=tid,
    )
# END_FILE
