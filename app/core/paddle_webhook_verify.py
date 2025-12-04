"""Paddle Webhook signature verification utilities."""

import hashlib
import hmac

from fastapi import HTTPException, Request

from app.core.config import settings


def _parse_paddle_signature_header(header: str) -> tuple[str, str]:
    """Parse Paddle-Signature header to extract ts and h1 values.

    Args:
        header: Paddle-Signature header value (e.g., 'ts=1234567890;h1=abcdef...')

    Returns:
        Tuple of (ts, h1) strings

    Raises:
        HTTPException: If header format is invalid
    """
    parts = header.split(";")
    values = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            values[k.strip()] = v.strip()

    if "ts" not in values or "h1" not in values:
        raise HTTPException(
            status_code=400, detail="Malformed Paddle-Signature header"
        )

    return values["ts"], values["h1"]


async def verify_paddle_signature(request: Request) -> bytes:
    """Verify Paddle Webhook v2 signature using Secret-based HMAC.

    Paddle v2 signature format:
    - Header: Paddle-Signature: 'ts=1234567890;h1=abcdef...'
    - signed_payload = f"{ts}:{raw_body}"
    - HMAC-SHA256(secret, signed_payload) -> hex string
    - Compare hex string with h1

    Args:
        request: FastAPI request object

    Returns:
        Raw request body bytes (for further processing)

    Raises:
        HTTPException: If signature is missing or invalid
    """
    # Get signature from header (support both cases)
    header = request.headers.get("Paddle-Signature") or request.headers.get(
        "paddle-signature"
    )
    if not header:
        raise HTTPException(
            status_code=400, detail="Missing Paddle-Signature header"
        )

    # Parse ts and h1 from header
    ts, h1 = _parse_paddle_signature_header(header)

    # Read raw body (must be done before any JSON parsing)
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # Create signed payload: "ts:body"
    signed_payload = f"{ts}:{body_str}"

    # Get secret from settings
    secret = settings.paddle_webhook_secret.encode("utf-8")

    # Calculate HMAC SHA256 and convert to hex string
    digest = hmac.new(
        secret, signed_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Safe comparison to prevent timing attacks
    if not hmac.compare_digest(digest, h1):
        raise HTTPException(
            status_code=401, detail="Invalid webhook signature"
        )

    # Return body for further processing
    return body_bytes




