from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


@dataclass(frozen=True)
class Settings:
    env: str
    log_mode: str
    app_version: str

    pg_host: str
    pg_port: int
    pg_db: str
    pg_user: str
    pg_password: str

    @property
    def database_url(self) -> str:
        # SQLAlchemy async DSN
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"


def get_settings() -> Settings:
    # Prefer APP_ENV, fallback to ENV (fix drift)
    env = _env("APP_ENV", _env("ENV", "dev"))
    log_mode = _env("LOG_MODE", "normal")
    app_version = _env("APP_VERSION", "0.1.0-dev")

    # Defaults should match docker-compose env; override via env if needed
    pg_host = _env("POSTGRES_HOST", "postgres")
    pg_port = int(_env("POSTGRES_PORT", "5432"))
    pg_db = _env("POSTGRES_DB", "nextcrm")
    pg_user = _env("POSTGRES_USER", "nextcrm")
    pg_password = _env("POSTGRES_PASSWORD", "nextcrm")

    return Settings(
        env=env,
        log_mode=log_mode,
        app_version=app_version,
        pg_host=pg_host,
        pg_port=pg_port,
        pg_db=pg_db,
        pg_user=pg_user,
        pg_password=pg_password,
    )


settings = get_settings()
