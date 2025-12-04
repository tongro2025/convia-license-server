"""API routes."""

from app.api.routes import (
    admin_license,
    admin_page,
    admin_webhook,
    auth,
    license_pages,
    paddle_webhook,
    public_license,
)

__all__ = [
    "public_license",
    "paddle_webhook",
    "admin_license",
    "admin_webhook",
    "admin_page",
    "auth",
    "license_pages",
]








