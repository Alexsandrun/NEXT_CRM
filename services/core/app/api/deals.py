from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.db import get_db
from app.models import Company, Contact, Deal, Pipeline, Stage
from app.security import require_bearer_user
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["deals"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# -------------------------
# Schemas
# -------------------------
class DealCreate(BaseModel):
    title: str
    amount: Decimal | None = None
    currency: str = "USD"

    company_id: str | None = None
    contact_id: str | None = None

    pipeline_id: str
    stage_id: str


class DealPatch(BaseModel):
    # patch: всё опционально, меняем только присланное
    title: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    stage_id: str | None = None

    company_id: str | None = None
    contact_id: str | None = None


class DealOut(BaseModel):
    # важно для Pydantic v2: чтение ORM-объектов по атрибутам
    model_config = ConfigDict(from_attributes=True)

    deal_id: str
    tenant_id: str

    title: str
    amount: Decimal | None
    currency: str

    company_id: str | None
    contact_id: str | None

    pipeline_id: str
    stage_id: str

    created_at: datetime
    updated_at: datetime


# -------------------------
# Helpers
# -------------------------
async def _require_pipeline(db: AsyncSession, tenant_id: str, pipeline_id: str) -> None:
    q = select(Pipeline).where(
        Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == pipeline_id
    )
    if (await db.execute(q)).scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )


async def _require_stage_in_pipeline(
    db: AsyncSession, tenant_id: str, pipeline_id: str, stage_id: str
) -> None:
    q = select(Stage).where(
        Stage.tenant_id == tenant_id,
        Stage.pipeline_id == pipeline_id,
        Stage.stage_id == stage_id,
    )
    if (await db.execute(q)).scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found (or not in pipeline)",
        )


async def _optional_fk_checks(
    db: AsyncSession, tenant_id: str, company_id: str | None, contact_id: str | None
) -> None:
    if company_id:
        q = select(Company).where(
            Company.tenant_id == tenant_id, Company.company_id == company_id
        )
        if (await db.execute(q)).scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

    if contact_id:
        q = select(Contact).where(
            Contact.tenant_id == tenant_id, Contact.contact_id == contact_id
        )
        if (await db.execute(q)).scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
            )


async def _get_deal(db: AsyncSession, tenant_id: str, deal_id: str) -> Deal:
    q = select(Deal).where(Deal.tenant_id == tenant_id, Deal.deal_id == deal_id)
    deal = (await db.execute(q)).scalar_one_or_none()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found"
        )
    return deal


def _norm_currency(cur: str | None) -> str | None:
    if cur is None:
        return None
    cur = cur.strip()
    if not cur:
        return None
    return cur.upper()


# -------------------------
# Routes
# -------------------------
@router.post("/deals", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    tenant_id, _user = await require_bearer_user(db, request)

    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="title must not be empty",
        )

    currency = _norm_currency(payload.currency) or "USD"

    # валидируем pipeline + stage
    await _require_pipeline(db, tenant_id, payload.pipeline_id)
    await _require_stage_in_pipeline(
        db, tenant_id, payload.pipeline_id, payload.stage_id
    )

    # валидируем company/contact если переданы
    await _optional_fk_checks(db, tenant_id, payload.company_id, payload.contact_id)

    deal = Deal(
        deal_id=f"d_{uuid4().hex}",
        tenant_id=tenant_id,
        title=title,
        amount=payload.amount,
        currency=currency,
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
        created_at=now_utc(),
        updated_at=now_utc(),
    )

    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return deal


@router.get("/deals", response_model=list[DealOut])
async def list_deals(
    request: Request,
    db: AsyncSession = Depends(get_db),
    pipeline_id: str | None = Query(default=None),
    stage_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Deal).where(Deal.tenant_id == tenant_id)

    if pipeline_id:
        q = q.where(Deal.pipeline_id == pipeline_id)
    if stage_id:
        q = q.where(Deal.stage_id == stage_id)

    q = q.order_by(Deal.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


@router.get("/deals/{deal_id}", response_model=DealOut)
async def get_deal(deal_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    return await _get_deal(db, tenant_id, deal_id)


@router.patch("/deals/{deal_id}", response_model=DealOut)
async def patch_deal(
    deal_id: str,
    payload: DealPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id, _user = await require_bearer_user(db, request)
    deal = await _get_deal(db, tenant_id, deal_id)

    data = payload.model_dump(exclude_unset=True)

    # FK checks (если пришли)
    await _optional_fk_checks(
        db,
        tenant_id,
        data.get("company_id"),
        data.get("contact_id"),
    )

    # stage_id: разрешаем менять только в рамках pipeline сделки
    if "stage_id" in data:
        new_stage_id = data["stage_id"]
        if new_stage_id is not None:
            await _require_stage_in_pipeline(
                db, tenant_id, deal.pipeline_id, new_stage_id
            )
        deal.stage_id = new_stage_id

    if "title" in data:
        if data["title"] is None:
            deal.title = deal.title
        else:
            t = data["title"].strip()
            if not t:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="title must not be empty",
                )
            deal.title = t

    if "amount" in data:
        deal.amount = data["amount"]

    if "currency" in data:
        cur = _norm_currency(data["currency"])
        if cur is not None:
            deal.currency = cur

    if "company_id" in data:
        deal.company_id = data["company_id"]

    if "contact_id" in data:
        deal.contact_id = data["contact_id"]

    deal.updated_at = now_utc()

    await db.commit()
    await db.refresh(deal)
    return deal


@router.delete("/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    tenant_id, _user = await require_bearer_user(db, request)
    deal = await _get_deal(db, tenant_id, deal_id)

    await db.delete(deal)
    await db.commit()
    return None
