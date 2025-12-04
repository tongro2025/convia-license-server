"""Admin webhook API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.security import verify_admin_api_key
from app.db.session import get_db
from app.models.webhook_log import WebhookLog
from app.schemas.webhook_log import WebhookLogOut

router = APIRouter()


@router.get("", response_model=List[WebhookLogOut])
async def list_webhook_logs(
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """List webhook logs (admin only).

    Args:
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        List of webhook logs
    """
    verify_admin_api_key(x_admin_api_key)

    logs = db.query(WebhookLog).order_by(
        WebhookLog.created_at.desc()
    ).offset(offset).limit(limit).all()

    return logs











