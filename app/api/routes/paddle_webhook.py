"""Paddle webhook API routes."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import verify_paddle_signature
from app.db.session import get_db
from app.models.license import License
from app.models.webhook_log import WebhookLog

router = APIRouter()


@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    paddle_signature: str = Header(..., alias="Paddle-Signature"),
    db: Session = Depends(get_db),
):
    """Handle Paddle webhook events.

    Args:
        request: FastAPI request object
        paddle_signature: Paddle webhook signature header
        db: Database session

    Returns:
        Success response
    """
    # Read raw body for signature verification
    body_bytes = await request.body()

    # Verify signature
    if not verify_paddle_signature(body_bytes, paddle_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse JSON payload
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = payload.get("event_type", "unknown")

    # Log webhook event
    webhook_log = WebhookLog(
        event_type=event_type,
        payload=json.dumps(payload),
        signature=paddle_signature,
    )
    db.add(webhook_log)

    # Handle different event types
    if event_type == "subscription.created" or event_type == "subscription.updated":
        # Create or update license
        subscription_id = payload.get("data", {}).get("id")
        if subscription_id:
            license_obj = db.query(License).filter(
                License.paddle_subscription_id == str(subscription_id)
            ).first()

            if not license_obj:
                license_obj = License(
                    paddle_subscription_id=str(subscription_id),
                    status="active",
                )
                db.add(license_obj)
            else:
                # Update status based on subscription status
                subscription_status = payload.get("data", {}).get("status", "active")
                license_obj.status = subscription_status
                license_obj.updated_at = datetime.utcnow()

    elif event_type == "subscription.cancelled":
        # Mark license as cancelled
        subscription_id = payload.get("data", {}).get("id")
        if subscription_id:
            license_obj = db.query(License).filter(
                License.paddle_subscription_id == str(subscription_id)
            ).first()
            if license_obj:
                license_obj.status = "cancelled"
                license_obj.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "success", "event_type": event_type}

