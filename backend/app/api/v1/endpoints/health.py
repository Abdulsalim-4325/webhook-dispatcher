import logging
from typing import Any
from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_database_session, get_redis

logger = logging.getLogger("health_api")
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> dict[str, str]:
    """Kubernetes / cloud orchestrator liveness probe."""
    return {"status": "alive", "service": "sentinel-dispatcher"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(
    db: AsyncSession = Depends(get_database_session),
    redis_client: Redis = Depends(get_redis),
) -> dict[str, Any]:
    """Checks database and Redis connectivity before routing traffic."""
    health_status: dict[str, Any] = {
        "status": "ready",
        "database": "unknown",
        "redis": "unknown",
    }

    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as db_err:
        logger.error("Database health check failed: %s", db_err)
        health_status["database"] = f"error: {str(db_err)}"
        health_status["status"] = "degraded"

    try:
        await redis_client.ping()
        health_status["redis"] = "connected"
    except Exception as redis_err:
        logger.error("Redis health check failed: %s", redis_err)
        health_status["redis"] = f"error: {str(redis_err)}"
        health_status["status"] = "degraded"

    return health_status
