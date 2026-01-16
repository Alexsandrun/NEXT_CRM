from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.db import get_db
from app.models import Pipeline
from app.security import require_bearer_user
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["pipelines"])


class PipelineCreate(BaseModel):
    name: str


class PipelineOut(BaseModel):
    # ВАЖНО: чтобы response_model мог читать поля из SQLAlchemy ORM-объекта
    model_config = ConfigDict(from_attributes=True)

    pipeline_id: str
    tenant_id: str
    name: str
    created_at: datetime
    updated_at: datetime


@router.post(
    "/pipelines", response_model=PipelineOut, status_code=status.HTTP_201_CREATED
)
async def create_pipeline(
    payload: PipelineCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    tenant_id, _user = await require_bearer_user(db, request)

    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="name is required"
        )

    obj = Pipeline(
        pipeline_id=f"pl_{uuid4().hex}",
        tenant_id=tenant_id,
        name=name,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/pipelines", response_model=list[PipelineOut])
async def list_pipelines(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    tenant_id, _user = await require_bearer_user(db, request)

    q = (
        select(Pipeline)
        .where(Pipeline.tenant_id == tenant_id)
        .order_by(Pipeline.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


@router.get("/pipelines/{pipeline_id}", response_model=PipelineOut)
async def get_pipeline(
    pipeline_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Pipeline).where(
        Pipeline.tenant_id == tenant_id, Pipeline.pipeline_id == pipeline_id
    )
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    return obj
