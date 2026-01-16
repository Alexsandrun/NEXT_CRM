from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Tenant, User
from app.security import hash_password

router = APIRouter()

@router.post("/bootstrap")
async def bootstrap(db: AsyncSession = Depends(get_db)):
    # Idempotent demo bootstrap
    tenant_id = "demo"
    admin_email = "admin@demo.local"
    admin_password = "admin123"
    admin_user_id = "u_admin_dev"

    t = (await db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))).scalar_one_or_none()
    if not t:
        t = Tenant(tenant_id=tenant_id, name="Demo Tenant")
        db.add(t)
        await db.commit()

    u = (
        await db.execute(
            select(User).where(User.tenant_id == tenant_id).where(User.email == admin_email)
        )
    ).scalar_one_or_none()

    if not u:
        u = User(
            user_id=admin_user_id,
            tenant_id=tenant_id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="admin",
            is_active=True,
        )
        db.add(u)
        await db.commit()

    return {
        "tenant_id": tenant_id,
        "admin_user_id": admin_user_id,
        "admin_email": admin_email,
        "trace_id": uuid4().hex,
    }