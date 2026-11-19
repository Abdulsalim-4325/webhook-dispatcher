from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=100, example="payment.completed")
    idempotency_key: str = Field(..., min_length=8, max_length=255, example="evt_idemp_9f81a7b")
    payload: dict[str, Any] = Field(..., example={"order_id": "ord_102", "amount": 4999, "currency": "EUR"})


class EventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
