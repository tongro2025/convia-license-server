"""API routes."""

from app.api.routes import (
    admin_license,
    admin_webhook,
    paddle_webhook,
    public_license,
)

__all__ = [
    "public_license",
    "paddle_webhook",
    "admin_license",
    "admin_webhook",
]





