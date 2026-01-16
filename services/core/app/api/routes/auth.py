from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


@dataclass(frozen=True)
class TokenInfo:
    tenant_id: str
    user_id: str
    email: str


_TOKENS: Dict[str, TokenInfo] = {}


def _trace_id() -> str:
    return uuid.uuid4().hex


def _make_token() -> str:
    return f"devtoken.{uuid.uuid4().hex}"


class LoginRequest(BaseModel):
    tenant: str
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    trace_id: str


class WhoAmIResponse(BaseModel):
    tenant_id: str
    user_id: str
    email: EmailStr
    trace_id: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # DEV-ONLY: demo creds
    if payload.tenant != "demo" or payload.email.lower() != "admin@demo.local" or payload.password != "admin123":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _make_token()
    info = TokenInfo(tenant_id="demo", user_id="u_admin_dev", email="admin@demo.local")
    _TOKENS[token] = info

    return LoginResponse(
        access_token=token,
        tenant_id=info.tenant_id,
        user_id=info.user_id,
        trace_id=_trace_id(),
    )


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]


@router.get("/whoami", response_model=WhoAmIResponse)
def whoami(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    token = _extract_bearer(authorization)
    info = _TOKENS.get(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid token")

    return WhoAmIResponse(
        tenant_id=info.tenant_id,
        user_id=info.user_id,
        email=info.email,
        trace_id=_trace_id(),
    )
