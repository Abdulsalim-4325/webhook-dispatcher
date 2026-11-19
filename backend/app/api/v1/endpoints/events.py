import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_database_session, get_redis
from backend.app.models.event import Event
from backend.app.schemas.event import EventCreate, EventResponse
from backend.app.services.dispatcher import DispatcherService
from backend.app.services.idempotency import IdempotencyService

router = APIRouter(prefix="/events", tags=["Events Ingestion"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    event_in: EventCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_database_session),
    redis_client: Redis = Depends(get_redis),
):
    """
    Ingest an incoming API event, validates idempotency, persists event state,
    and offloads asynchronous outbound webhook dispatch to worker pool.
    """
    key = idempotency_key or event_in.idempotency_key
    idemp_service = IdempotencyService(redis_client)

    acquired = await idemp_service.acquire_lock(key)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate request detected for Idempotency-Key: '{key}'",
        )

    # Persist event
    event = Event(
        id=uuid.uuid4(),
        event_type=event_in.event_type,
        idempotency_key=key,
        payload=event_in.payload,
        status="ACCEPTED",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Fan out to subscribers via background task
    dispatcher = DispatcherService(db)
    await dispatcher.fan_out_event(event.id, event.event_type, event.payload)

    await idemp_service.mark_complete(key, str(event.id))
    return event
