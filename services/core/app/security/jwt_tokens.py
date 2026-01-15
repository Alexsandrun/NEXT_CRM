from __future__ import annotations

import time
from typing import Any

import jwt

from ..settings import settings


def issue_token(*, tenant_id: str, user_id: str, email: str) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + int(settings.jwt_ttl_seconds),
        "tenant_id": tenant_id,
        "sub": user_id,
        "email": email,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
