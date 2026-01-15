from __future__ import annotations

import asyncio

from ..db import Base, get_engine
from ..models.tenancy import Tenant  # noqa: F401
from ..models.identity import User  # noqa: F401


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    asyncio.run(init_db())


if __name__ == "__main__":
    main()
