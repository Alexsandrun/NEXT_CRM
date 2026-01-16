from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Contact, Company
from app.security import require_bearer_user

router = APIRouter()


class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contact_id: str
    tenant_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company_id: Optional[str]
    created_at: datetime
    updated_at: datetime


async def _validate_company(db: AsyncSession, tenant_id: str, company_id: str) -> None:
    q = select(Company.company_id).where(Company.tenant_id == tenant_id, Company.company_id == company_id)
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid company_id")


@router.post("/contacts", response_model=ContactOut)
async def create_contact(payload: ContactCreate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    if payload.company_id:
        await _validate_company(db, tenant_id, payload.company_id)

    obj = Contact(
        tenant_id=tenant_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        company_id=payload.company_id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/contacts", response_model=List[ContactOut])
async def list_contacts(request: Request, db: AsyncSession = Depends(get_db), limit: int = 100):
    tenant_id, _user = await require_bearer_user(db, request)

    q = (
        select(Contact)
        .where(Contact.tenant_id == tenant_id)
        .order_by(Contact.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


@router.get("/contacts/{contact_id}", response_model=ContactOut)
async def get_contact(contact_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Contact).where(Contact.tenant_id == tenant_id, Contact.contact_id == contact_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return obj


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
async def update_contact(contact_id: str, payload: ContactUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Contact).where(Contact.tenant_id == tenant_id, Contact.contact_id == contact_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.company_id is not None and payload.company_id != "":
        await _validate_company(db, tenant_id, payload.company_id)
        obj.company_id = payload.company_id
    elif payload.company_id == "":
        obj.company_id = None

    if payload.name is not None:
        obj.name = payload.name
    if payload.email is not None:
        obj.email = payload.email
    if payload.phone is not None:
        obj.phone = payload.phone

    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id, _user = await require_bearer_user(db, request)

    q = select(Contact).where(Contact.tenant_id == tenant_id, Contact.contact_id == contact_id)
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    await db.delete(obj)
    await db.commit()
    return {"ok": True, "contact_id": contact_id}
