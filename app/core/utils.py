"""Utility functions."""

import secrets
from datetime import datetime, timedelta


def generate_magic_token(length: int = 32) -> str:
    """Generate a random magic token.

    Args:
        length: Token length in bytes (default: 32)

    Returns:
        URL-safe base64 encoded token string
    """
    return secrets.token_urlsafe(length)


def get_token_expiry(hours: int = 24) -> datetime:
    """Get expiry datetime for a token.

    Args:
        hours: Hours until expiry (default: 24)

    Returns:
        Datetime object representing expiry time
    """
    return datetime.utcnow() + timedelta(hours=hours)












