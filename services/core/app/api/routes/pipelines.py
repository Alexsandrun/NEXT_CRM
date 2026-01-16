from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.security import require_bearer_user

# IMPORTANT: эти модели должны существовать в app.models
from app.models import Pipeline, Stage  # type: ignore

router = APIRouter(tags=["pipelines"])


# ---------- Schemas ----------

class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class PipelineUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class PipelineOut(BaseModel):
    pipeline_id: str
    tenant_id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    position: Optional[int] = Field(default=None, ge=1)


class StageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    position: Optional[int] = Field(default=None, ge=1)


class StageOut(BaseModel):
    stage_id: str
    tenant_id: str
    pipeline_id: str
    name: str
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Helpers ----------

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


# ---------- Pipelines ----------

@router.post("/pipelines", response_model=PipelineOut)
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
    return PipelineOut.model_validate(obj)


@router.get("/pipelines", response_model=list[PipelineOut])
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
    rows = (await db.execute(q)).scalars().all()
    return [PipelineOut.model_validate(x) for x in rows]


@router.get("/pipelines/{pipeline_id}", response_model=PipelineOut)
async def get_pipeline(pipeline_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_pipeline(db, tenant_id, pipeline_id)
    return PipelineOut.model_validate(obj)


@router.patch("/pipelines/{pipeline_id}", response_model=PipelineOut)
async def update_pipeline(pipeline_id: str, payload: PipelineUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_pipeline(db, tenant_id, pipeline_id)

    obj.name = payload.name
    await db.commit()
    await db.refresh(obj)
    return PipelineOut.model_validate(obj)


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_pipeline(db, tenant_id, pipeline_id)

    await db.delete(obj)
    await db.commit()
    return {"ok": True}


# ---------- Stages (nested under pipeline) ----------

@router.post("/pipelines/{pipeline_id}/stages", response_model=StageOut)
async def create_stage(pipeline_id: str, payload: StageCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    _pipe = await _get_pipeline(db, tenant_id, pipeline_id)

    if payload.position is None:
        q = select(sa.func.coalesce(sa.func.max(Stage.position), 0)).where(
            Stage.tenant_id == tenant_id,
            Stage.pipeline_id == pipeline_id,
        )
        max_pos = (await db.execute(q)).scalar_one()
        position = int(max_pos) + 1
    else:
        position = payload.position

    obj = Stage(
        stage_id=f"st_{uuid4().hex}",
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        name=payload.name,
        position=position,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return StageOut.model_validate(obj)


@router.get("/pipelines/{pipeline_id}/stages", response_model=list[StageOut])
async def list_stages(pipeline_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    _pipe = await _get_pipeline(db, tenant_id, pipeline_id)

    q = (
        select(Stage)
        .where(Stage.tenant_id == tenant_id, Stage.pipeline_id == pipeline_id)
        .order_by(Stage.position.asc(), Stage.created_at.asc())
    )
    rows = (await db.execute(q)).scalars().all()
    return [StageOut.model_validate(x) for x in rows]


@router.patch("/stages/{stage_id}", response_model=StageOut)
async def update_stage(stage_id: str, payload: StageUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_stage(db, tenant_id, stage_id)

    if payload.name is not None:
        obj.name = payload.name
    if payload.position is not None:
        obj.position = payload.position

    await db.commit()
    await db.refresh(obj)
    return StageOut.model_validate(obj)


@router.delete("/stages/{stage_id}")
async def delete_stage(stage_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)
    obj = await _get_stage(db, tenant_id, stage_id)

    await db.delete(obj)
    await db.commit()
    return {"ok": True}
