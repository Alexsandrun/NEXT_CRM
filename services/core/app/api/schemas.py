from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ErrorOut(BaseModel):
    error: dict
    trace_id: str


class LoginIn(BaseModel):
    tenant: str = Field(..., description="Tenant slug")
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    trace_id: str


class BootstrapOut(BaseModel):
    tenant_id: str
    admin_user_id: str
    admin_email: EmailStr
    trace_id: str
