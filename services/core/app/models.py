from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="admin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    ip: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, default="", nullable=False)


# -------------------------
# Contacts
# -------------------------
import uuid

import sqlalchemy as sa
from sqlalchemy.sql import func


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        sa.Index("ix_contacts_tenant_company", "tenant_id", "company_id"),
        sa.Index("ix_contacts_tenant_created", "tenant_id", "created_at"),
    )

    contact_id = sa.Column(
        sa.String(64), primary_key=True, default=lambda: f"c_{uuid.uuid4().hex}"
    )
    tenant_id = sa.Column(sa.String(64), nullable=False, index=True)

    name = sa.Column(sa.String(200), nullable=False)
    email = sa.Column(sa.String(320), nullable=True)
    phone = sa.Column(sa.String(50), nullable=True)

    company_id = sa.Column(
        sa.String(64),
        sa.ForeignKey("companies.company_id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = sa.Column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# -------------------------
# Companies
# -------------------------
import sqlalchemy as sa
from sqlalchemy.sql import func


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        sa.Index("ix_companies_tenant_created", "tenant_id", "created_at"),
    )

    company_id = sa.Column(
        sa.String(64), primary_key=True, default=lambda: f"co_{uuid.uuid4().hex}"
    )
    tenant_id = sa.Column(sa.String(64), nullable=False, index=True)

    name = sa.Column(sa.String(200), nullable=False)
    domain = sa.Column(sa.String(200), nullable=True)

    created_at = sa.Column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# -------------------------
# Pipelines / Stages / Deals
# -------------------------

# -------------------------
# Pipelines / Stages / Deals
# -------------------------
from decimal import Decimal

from sqlalchemy import Integer, Numeric


class Pipeline(Base):
    __tablename__ = "pipelines"

    pipeline_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Stage(Base):
    __tablename__ = "stages"

    stage_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    pipeline_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("pipelines.pipeline_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # в миграции поле называется sort_order
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Deal(Base):
    __tablename__ = "deals"

    deal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(250), nullable=False)

    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)

    company_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("companies.company_id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    contact_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("contacts.contact_id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    pipeline_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("pipelines.pipeline_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    stage_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("stages.stage_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
