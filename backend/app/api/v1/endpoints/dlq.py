import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_database_session
from backend.app.models.delivery import DeadLetterQueue
from backend.app.models.event import Event
from backend.app.models.subscription import Subscription
from backend.app.schemas.delivery import DLQResponse
from backend.app.workers.tasks import dispatch_webhook_task

router = APIRouter(prefix="/dlq", tags=["Dead-Letter Queue"])


@router.get("/", response_model=list[DLQResponse])
async def list_dlq_messages(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_database_session),
):
    """Retrieve dead-lettered payloads that exhausted retries."""
    stmt = (
        select(DeadLetterQueue)
        .where(DeadLetterQueue.is_replayed == False)
        .order_by(DeadLetterQueue.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{dlq_id}/replay", status_code=status.HTTP_202_ACCEPTED)
async def replay_dlq_message(
    dlq_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
):
    """Manually replay a dead-letter message back into the dispatch pipeline."""
    dlq_item = await db.get(DeadLetterQueue, dlq_id)
    if not dlq_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DLQ item not found")

    event = await db.get(Event, dlq_item.event_id)
    subscription = await db.get(Subscription, dlq_item.subscription_id)

    if not event or not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated event or subscription has been deleted",
        )

    # Re-queue task to the worker pool
    dispatch_webhook_task.delay(
        event_id=str(event.id),
        subscription_id=str(subscription.id),
        target_url=subscription.target_url,
        secret=subscription.secret_key,
        payload=event.payload,
        attempt=1,
    )

    dlq_item.is_replayed = True
    await db.commit()
    return {"status": "requeued", "dlq_id": dlq_id, "event_id": event.id}
