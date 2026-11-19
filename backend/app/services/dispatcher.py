import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.subscription import Subscription
from backend.app.workers.tasks import dispatch_webhook_task

logger = logging.getLogger("dispatcher_service")


class DispatcherService:
    """Coordinates fan-out of ingested events to active webhook subscribers."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def fan_out_event(self, event_id: uuid.UUID, event_type: str, payload: dict) -> int:
        stmt = select(Subscription).where(
            Subscription.event_type == event_type,
            Subscription.is_active == True,
        )
        result = await self.db.execute(stmt)
        subscriptions = result.scalars().all()

        dispatched_count = 0
        for sub in subscriptions:
            # Enqueue Celery task for asynchronous outbound dispatch
            dispatch_webhook_task.delay(
                event_id=str(event_id),
                subscription_id=str(sub.id),
                target_url=sub.target_url,
                secret=sub.secret_key,
                payload=payload,
                attempt=1,
            )
            dispatched_count += 1

        logger.info("Fanned out event %s to %d active subscribers", event_id, dispatched_count)
        return dispatched_count
