from redis.asyncio import ConnectionPool, Redis
from backend.app.core.config import settings

pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    decode_responses=True,
)


def get_redis_client() -> Redis:
    """Returns an asynchronous Redis client instance from the shared connection pool."""
    return Redis(connection_pool=pool)
