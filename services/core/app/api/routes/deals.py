from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.security import require_bearer_user

# IMPORTANT: эти модели должны существовать в app.models
from app.models import Deal, Pipeline, Stage, Company, Contact  # type: ignore

router = APIRouter(tags=["deals"])


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: Optional[Decimal] = Field(default=None)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    pipeline_id: str
    stage_id: str

    company_id: Optional[str] = None
    contact_id: Optional[str] = None

    close_date: Optional[datetime] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount: Optional[Decimal] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    stage_id: Optional[str] = None
    company_id: Optional[str] = None
    contact_id: Optional[str] = None

    close_date: Optional[datetime] = None
    notes: Optional[str] = None


class DealOut(BaseModel):
    deal_id: str
    tenant_id: str
    title: str
    amount: Optional[Decimal]
    currency: str
    pipeline_id: str
    stage_id: str
    company_id: Optional[str]
    contact_id: Optional[str]
    close_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


async def _get_pipeline(db: AsyncSession, tenant_id: str, pipeline_id: str) -> Pipeline:
    q = select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == pipeline_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return obj


async def _get_stage(db: AsyncSession, tenant_id: str, stage_id: str) -> Stage:
    q = select(Stage).where(Stage.tenant_id == tenant_id, Stage.stage_id == stage_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Stage not found")
    return obj


async def _get_deal(db: AsyncSession, tenant_id: str, deal_id: str) -> Deal:
    q = select(Deal).where(Deal.tenant_id == tenant_id, Deal.deal_id == deal_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Deal not found")
    return obj


async def _ensure_company_contact_belong_tenant(db: AsyncSession, tenant_id: str, company_id: Optional[str], contact_id: Optional[str]):
    if company_id:
        q = select(Company.company_id).where(Company.tenant_id == tenant_id, Company.company_id == company_id)
        if (await db.execute(q)).first() is None:
            raise HTTPException(status_code=404, detail="Company not found")
    if contact_id:
        q = select(Contact.contact_id).where(Contact.tenant_id == tenant_id, Contact.contact_id == contact_id)
        if (await db.execute(q)).first() is None:
            raise HTTPException(status_code=404, detail="Contact not found")


@router.post("/deals", response_model=DealOut)
async def create_deal(payload: DealCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    pipe = await _get_pipeline(db, tenant_id, payload.pipeline_id)
    st = await _get_stage(db, tenant_id, payload.stage_id)
    if st.pipeline_id != pipe.pipeline_id:
        raise HTTPException(status_code=400, detail="Stage does not belong to the pipeline")

    await _ensure_company_contact_belong_tenant(db, tenant_id, payload.company_id, payload.contact_id)

    obj = Deal(
        deal_id=f"d_{uuid4().hex}",
        tenant_id=tenant_id,
        title=payload.title,
        amount=payload.amount,
        currency=payload.currency.upper(),
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        close_date=payload.close_date,
        notes=payload.notes,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return DealOut.model_validate(obj)


@router.get("/deals", response_model=list[DealOut])
async def list_deals(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    pipeline_id: Optional[str] = None,
    stage_id: Optional[str] = None,
):
    tenant_id, _user = await require_bearer_user(db, request)
    limit = max(1, min(200, limit))
    offset = max(0, offset)

    q = select(Deal).where(Deal.tenant_id == tenant_id)
    if pipeline_id:
        q = q.where(Deal.pipeline_id == pipeline_id)
    if stage_id:
        q = q.where(Deal.stage_id == stage_id)

    q = q.order_by(Deal.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    return [DealOut.model_validate(x) for x in rows]


@router.get("/deals/{deal_id}", response_model=DealOut)
async def get_deal(deal_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_deal(db, tenant_id, deal_id)
    return DealOut.model_validate(obj)


@router.patch("/deals/{deal_id}", response_model=DealOut)
async def update_deal(deal_id: str, payload: DealUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_deal(db, tenant_id, deal_id)

    if payload.stage_id is not None:
        st = await _get_stage(db, tenant_id, payload.stage_id)
        # stage должна быть в том же pipeline что и deal
        if st.pipeline_id != obj.pipeline_id:
            raise HTTPException(status_code=400, detail="Stage does not belong to deal pipeline")
        obj.stage_id = payload.stage_id

    if payload.title is not None:
        obj.title = payload.title
    if payload.amount is not None:
        obj.amount = payload.amount
    if payload.currency is not None:
        obj.currency = payload.currency.upper()

    if payload.company_id is not None or payload.contact_id is not None:
        await _ensure_company_contact_belong_tenant(db, tenant_id, payload.company_id, payload.contact_id)
        if payload.company_id is not None:
            obj.company_id = payload.company_id
        if payload.contact_id is not None:
            obj.contact_id = payload.contact_id

    if payload.close_date is not None:
        obj.close_date = payload.close_date
    if payload.notes is not None:
        obj.notes = payload.notes

    await db.commit()
    await db.refresh(obj)
    return DealOut.model_validate(obj)


@router.delete("/deals/{deal_id}")
async def delete_deal(deal_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_deal(db, tenant_id, deal_id)
    await db.delete(obj)
    await db.commit()
    return {"ok": True}
