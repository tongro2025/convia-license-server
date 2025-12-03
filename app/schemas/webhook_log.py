"""Webhook log schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class WebhookLogOut(BaseModel):
    """Webhook log output schema."""

    id: int
    event_type: str
    payload: str
    signature: str | None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

