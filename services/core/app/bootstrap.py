from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models.tenancy import Tenant
from .models.identity import User
from .security.passwords import hash_password
from .settings import settings


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


async def ensure_bootstrap(db: AsyncSession) -> tuple[str, str, str]:
    """
    Create demo tenant + admin user if missing.
    Returns (tenant_id, admin_user_id, admin_email)
    """
    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == settings.bootstrap_tenant_slug))
    ).scalar_one_or_none()

    if tenant is None:
        tenant = Tenant(
            id=_id("tnt"),
            slug=settings.bootstrap_tenant_slug,
            name=f"{settings.bootstrap_tenant_slug.title()} Tenant",
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)

    admin_email = settings.bootstrap_admin_email.lower()

    user = (
        await db.execute(
            select(User).where(User.tenant_id == tenant.id, User.email == admin_email)
        )
    ).scalar_one_or_none()

    if user is None:
        user = User(
            id=_id("usr"),
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            is_active=True,
            is_locked=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return tenant.id, user.id, user.email
