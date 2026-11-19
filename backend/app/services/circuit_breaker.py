from urllib.parse import urlparse
from redis.asyncio import Redis


class CircuitBreaker:
    """
    Per-destination domain circuit breaker backed by Redis sliding counters.
    Prevents worker pool starvation when an external tenant or customer endpoint goes down.
    """

    def __init__(self, redis_client: Redis, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def can_dispatch(self, target_url: str) -> bool:
        domain = self._get_domain(target_url)
        state = await self.redis.get(f"cb:{domain}:state")
        return state != "OPEN"

    async def record_success(self, target_url: str) -> None:
        domain = self._get_domain(target_url)
        await self.redis.delete(f"cb:{domain}:failures")
        await self.redis.delete(f"cb:{domain}:state")

    async def record_failure(self, target_url: str) -> bool:
        domain = self._get_domain(target_url)
        failures = await self.redis.incr(f"cb:{domain}:failures")
        if failures >= self.failure_threshold:
            # Trip the circuit to OPEN with TTL
            await self.redis.set(f"cb:{domain}:state", "OPEN", ex=self.recovery_timeout)
            return True
        return False
