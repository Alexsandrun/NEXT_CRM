from __future__ import annotations

from pydantic import BaseModel
import os


class Settings(BaseModel):
    # env
    env: str = os.getenv("ENV", "dev")
    log_mode: str = os.getenv("LOG_MODE", "normal")

    # database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://nextcrm:nextcrm@postgres:5432/nextcrm",
    )

    # auth
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-insecure-change-me")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "nextcrm")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "nextcrm")
    jwt_ttl_seconds: int = int(os.getenv("JWT_TTL_SECONDS", "3600"))

    # bootstrap
    bootstrap_enabled: bool = os.getenv("BOOTSTRAP_ENABLED", "1") == "1"
    bootstrap_tenant_slug: str = os.getenv("BOOTSTRAP_TENANT_SLUG", "demo")
    bootstrap_admin_email: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@demo.local")
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123")


settings = Settings()
