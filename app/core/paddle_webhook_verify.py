"""Paddle Webhook signature verification utilities."""

import base64
import hashlib
import hmac

from fastapi import HTTPException, Request

from app.core.config import settings


async def verify_paddle_signature(request: Request) -> bytes:
    """Verify Paddle Webhook v2 signature using Secret-based HMAC.

    Args:
        request: FastAPI request object

    Returns:
        Raw request body bytes (for further processing)

    Raises:
        HTTPException: If signature is missing or invalid
    """
    # Get signature from header
    signature = request.headers.get("paddle-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Paddle signature header")

    # Read raw body
    body = await request.body()

    # Get secret from settings
    secret = settings.paddle_webhook_secret.encode("utf-8")

    # Calculate HMAC SHA256
    digest = hmac.new(secret, body, hashlib.sha256).digest()

    # Base64 encode
    expected = base64.b64encode(digest).decode("utf-8")

    # Safe comparison to prevent timing attacks
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid Paddle signature")

    # Return body for further processing
    return body
