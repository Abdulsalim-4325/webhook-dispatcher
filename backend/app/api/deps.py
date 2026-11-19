from collections.abc import AsyncGenerator
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.redis import get_redis_client


async def get_database_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for database session."""
    yield session


def get_redis() -> Redis:
    """Dependency provider for Redis async client."""
    return get_redis_client()
