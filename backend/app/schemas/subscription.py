from datetime import datetime
import uuid
from pydantic import BaseModel, Field, HttpUrl


class SubscriptionCreate(BaseModel):
    target_url: str = Field(..., example="https://api.merchant.com/webhooks")
    secret_key: str = Field(..., min_length=16, example="whsec_99a8b7c6d5e4f3a2b1")
    event_type: str = Field(..., example="payment.completed")
    max_retries: int = Field(default=5, ge=1, le=10)
    timeout_seconds: int = Field(default=5, ge=1, le=30)


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    target_url: str
    event_type: str
    is_active: bool
    max_retries: int
    timeout_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True
