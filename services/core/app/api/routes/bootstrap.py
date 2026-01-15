from __future__ import annotations

import os
import uuid
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

TENANT = os.getenv("BOOTSTRAP_TENANT", "demo")
ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@demo.local")

def trace_id() -> str:
    return uuid.uuid4().hex

class BootstrapOut(BaseModel):
    tenant_id: str
    admin_user_id: str
    admin_email: str
    trace_id: str

@router.post("/bootstrap", response_model=BootstrapOut)
def bootstrap() -> BootstrapOut:
    return BootstrapOut(
        tenant_id=TENANT,
        admin_user_id="u_admin_dev",
        admin_email=ADMIN_EMAIL,
        trace_id=trace_id(),
    )
# END_FILE
