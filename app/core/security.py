"""Security utilities for API key and webhook signature verification."""

import hashlib
import hmac
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_admin_api_key(x_admin_api_key: Optional[str] = Header(None)) -> None:
    """Verify admin API key from request header.

    Args:
        x_admin_api_key: Admin API key from X-Admin-API-Key header

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )


def verify_paddle_signature(
    payload: bytes,
    signature: str,
    secret: Optional[str] = None,
) -> bool:
    """Verify Paddle webhook signature.

    Args:
        payload: Raw request body bytes
        signature: Paddle-Signature header value
        secret: Webhook secret (defaults to settings.paddle_webhook_secret)

    Returns:
        True if signature is valid, False otherwise
    """
    if secret is None:
        secret = settings.paddle_webhook_secret

    # Paddle signature verification
    # Paddle uses SHA256 HMAC with the webhook secret
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)

