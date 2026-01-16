from __future__ import annotations

import uuid
from fastapi import APIRouter

router = APIRouter()

_BOOTSTRAPPED = False


def _trace_id() -> str:
    return uuid.uuid4().hex


@router.post("/bootstrap")
def bootstrap():
    global _BOOTSTRAPPED
    _BOOTSTRAPPED = True  # dev-idempotent marker

    return {
        "tenant_id": "demo",
        "admin_user_id": "u_admin_dev",
        "admin_email": "admin@demo.local",
        "trace_id": _trace_id(),
    }
