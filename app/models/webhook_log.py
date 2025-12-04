"""Webhook log model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.db.base import Base


class WebhookLog(Base):
    """Webhook log table model - stores Paddle webhook events."""

    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON string
    signature = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)







