from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Company
from app.security import require_bearer_user

router = APIRouter()


class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: str
    tenant_id: str
    name: str
    domain: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("/companies", response_model=CompanyOut)
async def create_company(payload: CompanyCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    obj = Company(tenant_id=tenant_id, name=payload.name, domain=payload.domain)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/companies", response_model=List[CompanyOut])
async def list_companies(request: Request, db: AsyncSession = Depends(get_db), limit: int = 100):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Company).where(Company.tenant_id == tenant_id).order_by(Company.created_at.desc()).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


@router.get("/companies/{company_id}", response_model=CompanyOut)
async def get_company(company_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Company).where(Company.tenant_id == tenant_id, Company.company_id == company_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return obj


@router.patch("/companies/{company_id}", response_model=CompanyOut)
async def update_company(company_id: str, payload: CompanyUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Company).where(Company.tenant_id == tenant_id, Company.company_id == company_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.domain is not None:
        obj.domain = payload.domain

    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Company).where(Company.tenant_id == tenant_id, Company.company_id == company_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    await db.delete(obj)
    await db.commit()
    return {"ok": True, "company_id": company_id}
