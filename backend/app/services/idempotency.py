from redis.asyncio import Redis


class IdempotencyService:
    """
    Enforces atomic at-most-once ingestion gates using Redis SET NX EX locks.
    Prevents duplicate task generation when clients retry requests due to network timeouts.
    """

    def __init__(self, redis_client: Redis, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds

    async def acquire_lock(self, idempotency_key: str) -> bool:
        """
        Attempts to acquire an idempotency lock for the given key.
        Returns True if acquired (first time seen), False if already processed or in-flight.
        """
        key = f"idemp:{idempotency_key}"
        acquired = await self.redis.set(key, "PROCESSING", nx=True, ex=self.ttl)
        return bool(acquired)

    async def mark_complete(self, idempotency_key: str, event_id: str) -> None:
        key = f"idemp:{idempotency_key}"
        await self.redis.set(key, f"COMPLETED:{event_id}", ex=self.ttl)
