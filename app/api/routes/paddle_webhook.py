"""Paddle webhook API routes."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import PLAN_MAX_CONTAINERS
from app.core.paddle_webhook_verify import verify_paddle_signature
from app.db.session import get_db
from app.models.customer import Customer
from app.models.license import License
from app.models.webhook_log import WebhookLog

router = APIRouter()


@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Paddle webhook events.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Success response
    """
    # Verify signature and get body
    body_bytes = await verify_paddle_signature(request)

    # Get signature from header for logging
    paddle_signature = request.headers.get("paddle-signature", "")

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
        # Extract subscription data
        subscription_data = payload.get("data", {})
        subscription_id = subscription_data.get("id")
        
        if subscription_id:
            # Extract customer information
            customer_data = subscription_data.get("customer", {})
            customer_email = customer_data.get("email", "")
            paddle_customer_id = customer_data.get("id")
            
            # Extract plan information
            items = subscription_data.get("items", [])
            plan_name = "basic"  # default
            if items:
                # Try to get plan name from product_id or price_id
                first_item = items[0]
                product_id = first_item.get("price", {}).get("product_id")
                # You may need to map product_id to plan name based on your Paddle setup
                # For now, using a simple mapping or default
                plan_name = first_item.get("price", {}).get("name", "basic").lower()
            
            # Determine allowed containers from plan
            allowed_containers = PLAN_MAX_CONTAINERS.get(plan_name, 1)
            
            # Find or create customer
            customer = None
            if customer_email:
                customer = db.query(Customer).filter(
                    Customer.email == customer_email
                ).first()
                
                if not customer:
                    customer = Customer(
                        email=customer_email,
                        paddle_customer_id=str(paddle_customer_id) if paddle_customer_id else None,
                    )
                    db.add(customer)
                    db.flush()  # Get customer.id
            
            # Find or create license
            license_obj = db.query(License).filter(
                License.paddle_subscription_id == str(subscription_id)
            ).first()

            if not license_obj:
                license_obj = License(
                    paddle_subscription_id=str(subscription_id),
                    email=customer_email,
                    allowed_containers=allowed_containers,
                    customer_id=customer.id if customer else None,
                    status="active",
                )
                db.add(license_obj)
            else:
                # Update license information
                subscription_status = subscription_data.get("status", "active")
                license_obj.status = subscription_status
                license_obj.email = customer_email
                license_obj.allowed_containers = allowed_containers
                if customer:
                    license_obj.customer_id = customer.id
                license_obj.updated_at = datetime.utcnow()

    elif event_type == "subscription.cancelled":
        # Mark license as cancelled
        subscription_data = payload.get("data", {})
        subscription_id = subscription_data.get("id")
        if subscription_id:
            license_obj = db.query(License).filter(
                License.paddle_subscription_id == str(subscription_id)
            ).first()
            if license_obj:
                license_obj.status = "cancelled"
                license_obj.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "success", "event_type": event_type}

