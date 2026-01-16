from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.db import get_db
from app.models import Pipeline, Stage
from app.security import require_bearer_user
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["stages"])


class StageCreate(BaseModel):
    pipeline_id: str
    name: str
    sort_order: int = 0
    is_won: bool = False
    is_lost: bool = False


class StageOut(BaseModel):
    # чтобы response_model мог читать поля из ORM (SQLAlchemy) объекта
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


@router.post("/stages", response_model=StageOut, status_code=status.HTTP_201_CREATED)
async def create_stage(
    payload: StageCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    tenant_id, _user = await require_bearer_user(db, request)

    # pipeline must exist and belong to tenant
    pq = select(Pipeline).where(
        Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == payload.pipeline_id
    )
    pipeline = (await db.execute(pq)).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )

    if payload.is_won and payload.is_lost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stage cannot be both won and lost",
        )

    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="name is required"
        )

    obj = Stage(
        stage_id=f"st_{uuid4().hex}",
        tenant_id=tenant_id,
        pipeline_id=payload.pipeline_id,
        name=name,
        sort_order=payload.sort_order,
        is_won=payload.is_won,
        is_lost=payload.is_lost,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/stages", response_model=list[StageOut])
async def list_stages(
    request: Request,
    db: AsyncSession = Depends(get_db),
    pipeline_id: str | None = None,
    limit: int = Query(200, ge=1, le=500),
):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Stage).where(Stage.tenant_id == tenant_id)
    if pipeline_id:
        q = q.where(Stage.pipeline_id == pipeline_id)

    q = q.order_by(Stage.pipeline_id.asc(), Stage.sort_order.asc()).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return list(rows)
