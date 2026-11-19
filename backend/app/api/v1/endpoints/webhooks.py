import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_database_session
from backend.app.core.security import SecurityEngine, SSRFSecurityException
from backend.app.models.subscription import Subscription
from backend.app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/webhooks", tags=["Webhook Subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    sub_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_database_session),
):
    """Register a new webhook destination with security verification and HMAC secret."""
    try:
        SecurityEngine.validate_and_resolve_url(sub_in.target_url)
    except SSRFSecurityException as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target URL: {str(err)}",
        )

    subscription = Subscription(
        id=uuid.uuid4(),
        target_url=sub_in.target_url,
        secret_key=sub_in.secret_key,
        event_type=sub_in.event_type,
        max_retries=sub_in.max_retries,
        timeout_seconds=sub_in.timeout_seconds,
        is_active=True,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.get("/", response_model=list[SubscriptionResponse])
async def list_webhook_subscriptions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_database_session),
):
    """List registered webhook destination endpoints."""
    stmt = select(Subscription).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
