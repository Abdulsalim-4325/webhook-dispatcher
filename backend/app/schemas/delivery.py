from datetime import datetime
import uuid
from pydantic import BaseModel


class DeliveryAttemptResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    subscription_id: uuid.UUID
    attempt_number: int
    status_code: int | None
    execution_time_ms: float | None
    error_message: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DLQResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    subscription_id: uuid.UUID
    exhausted_attempts: int
    last_error: str | None
    is_replayed: bool
    created_at: datetime

    class Config:
        from_attributes = True
