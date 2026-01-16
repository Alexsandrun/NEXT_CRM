from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Company, Contact, Deal, Pipeline, Stage
from app.security import require_bearer_user

router = APIRouter(tags=["deals"])


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    amount: Decimal | None = None
    currency: str = Field(default="USD", min_length=1, max_length=10)

    company_id: str | None = None
    contact_id: str | None = None

    pipeline_id: str
    stage_id: str


@router.post("/deals")
async def create_deal(payload: DealCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    pipe = (await db.execute(
        select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == payload.pipeline_id)
    )).scalar_one_or_none()
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    st = (await db.execute(
        select(Stage).where(Stage.tenant_id == tenant_id, Stage.stage_id == payload.stage_id)
    )).scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=404, detail="Stage not found")

    if st.pipeline_id != payload.pipeline_id:
        raise HTTPException(status_code=400, detail="Stage does not belong to the pipeline")

    if payload.company_id:
        exists = (await db.execute(
            select(Company.company_id).where(Company.tenant_id == tenant_id, Company.company_id == payload.company_id)
        )).first()
        if not exists:
            raise HTTPException(status_code=404, detail="Company not found")

    if payload.contact_id:
        exists = (await db.execute(
            select(Contact.contact_id).where(Contact.tenant_id == tenant_id, Contact.contact_id == payload.contact_id)
        )).first()
        if not exists:
            raise HTTPException(status_code=404, detail="Contact not found")

    obj = Deal(
        deal_id=f"d_{uuid4().hex}",
        tenant_id=tenant_id,
        title=payload.title,
        amount=payload.amount,
        currency=payload.currency.upper(),
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/deals")
async def list_deals(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    tenant_id, _user = await require_bearer_user(db, request)
    limit = max(1, min(200, limit))
    offset = max(0, offset)

    q = (
        select(Deal)
        .where(Deal.tenant_id == tenant_id)
        .order_by(Deal.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await db.execute(q)).scalars().all()
