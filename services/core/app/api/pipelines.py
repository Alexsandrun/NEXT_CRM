from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Pipeline, Stage
from app.security import require_bearer_user

router = APIRouter(tags=["pipelines"])


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sort_order: int | None = Field(default=None, ge=1)
    is_won: bool = False
    is_lost: bool = False


@router.post("/pipelines")
async def create_pipeline(payload: PipelineCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    obj = Pipeline(
        pipeline_id=f"pl_{uuid4().hex}",
        tenant_id=tenant_id,
        name=payload.name,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/pipelines")
async def list_pipelines(request: Request, db: AsyncSession = Depends(get_db), limit: int = 50, offset: int = 0):
    tenant_id, _user = await require_bearer_user(db, request)
    limit = max(1, min(200, limit))
    offset = max(0, offset)

    q = (
        select(Pipeline)
        .where(Pipeline.tenant_id == tenant_id)
        .order_by(Pipeline.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await db.execute(q)).scalars().all()


@router.post("/pipelines/{pipeline_id}/stages")
async def create_stage(pipeline_id: str, payload: StageCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    pipe = (await db.execute(
        select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == pipeline_id)
    )).scalar_one_or_none()
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if payload.sort_order is None:
        q = select(sa.func.coalesce(sa.func.max(Stage.sort_order), 0)).where(
            Stage.tenant_id == tenant_id,
            Stage.pipeline_id == pipeline_id,
        )
        max_so = (await db.execute(q)).scalar_one()
        sort_order = int(max_so) + 1
    else:
        sort_order = payload.sort_order

    obj = Stage(
        stage_id=f"st_{uuid4().hex}",
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        name=payload.name,
        sort_order=sort_order,
        is_won=payload.is_won,
        is_lost=payload.is_lost,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/pipelines/{pipeline_id}/stages")
async def list_stages(pipeline_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = (
        select(Stage)
        .where(Stage.tenant_id == tenant_id, Stage.pipeline_id == pipeline_id)
        .order_by(Stage.sort_order.asc(), Stage.created_at.asc())
    )
    return (await db.execute(q)).scalars().all()
