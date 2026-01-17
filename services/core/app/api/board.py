from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Deal, Pipeline, Stage
from app.security import require_bearer_user

router = APIRouter(tags=["board"])


class PipelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pipeline_id: str
    tenant_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class StageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage_id: str
    tenant_id: str
    pipeline_id: str
    name: str
    sort_order: int
    is_won: bool
    is_lost: bool
    created_at: datetime
    updated_at: datetime


class DealOut(BaseModel):
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


class StageColumn(BaseModel):
    stage: StageOut
    deals: list[DealOut]
    count: int
    sum_amount: Decimal


class PipelineBoardOut(BaseModel):
    pipeline: PipelineOut
    columns: list[StageColumn]


@router.get("/pipelines/{pipeline_id}/board", response_model=PipelineBoardOut)
async def get_pipeline_board(
    pipeline_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    include_empty: bool = Query(True),  # <-- ВАЖНО: дефолт через "="
):
    tenant_id, _user = await require_bearer_user(db, request)

    # pipeline
    pq = select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == pipeline_id)
    pipeline = (await db.execute(pq)).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    # stages
    sq = (
        select(Stage)
        .where(Stage.tenant_id == tenant_id, Stage.pipeline_id == pipeline_id)
        .order_by(Stage.sort_order.asc(), Stage.created_at.asc())
    )
    stages = (await db.execute(sq)).scalars().all()

    # deals (for pipeline)
    dq = (
        select(Deal)
        .where(Deal.tenant_id == tenant_id, Deal.pipeline_id == pipeline_id)
        .order_by(Deal.updated_at.desc(), Deal.created_at.desc())
    )
    deals = (await db.execute(dq)).scalars().all()

    deals_by_stage: dict[str, list[Deal]] = {}
    for d in deals:
        deals_by_stage.setdefault(d.stage_id, []).append(d)

    # aggregates per stage
    aq = (
        select(
            Deal.stage_id.label("stage_id"),
            func.count(Deal.deal_id).label("cnt"),
            func.coalesce(func.sum(Deal.amount), 0).label("sum_amount"),
        )
        .where(Deal.tenant_id == tenant_id, Deal.pipeline_id == pipeline_id)
        .group_by(Deal.stage_id)
    )
    agg_rows = (await db.execute(aq)).all()
    agg_map: dict[str, tuple[int, Decimal]] = {}
    for r in agg_rows:
        agg_map[r.stage_id] = (int(r.cnt), Decimal(str(r.sum_amount)))

    columns: list[StageColumn] = []
    for st in stages:
        st_deals = deals_by_stage.get(st.stage_id, [])
        cnt, ssum = agg_map.get(st.stage_id, (0, Decimal("0")))

        if (not include_empty) and cnt == 0:
            continue

        columns.append(
            StageColumn(
                stage=StageOut.model_validate(st),
                deals=[DealOut.model_validate(d) for d in st_deals],
                count=cnt,
                sum_amount=ssum,
            )
        )

    return PipelineBoardOut(
        pipeline=PipelineOut.model_validate(pipeline),
        columns=columns,
    )
