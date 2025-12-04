"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import (
    admin_license,
    admin_webhook,
    paddle_webhook,
    public_license,
)

# ----------------------------------------------------
# Application Setup
# ----------------------------------------------------

app = FastAPI(
    title="Convia License Server",
    description="License verification and management server with Paddle integration",
    version="0.1.0",
)

# ----------------------------------------------------
# CORS (optional but recommended for web debugging)
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 필요 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Routers
# ----------------------------------------------------

# Public license routes
app.include_router(
    public_license.router,
    prefix="/api/license",
    tags=["license"],
)

# Paddle webhook routes
app.include_router(
    paddle_webhook.router,
    prefix="/api/paddle",
    tags=["paddle"],
)

# Admin license routes
app.include_router(
    admin_license.router,
    prefix="/api/admin/licenses",
    tags=["admin"],
)

# Admin webhook routes
app.include_router(
    admin_webhook.router,
    prefix="/api/admin/webhooks",
    tags=["admin"],
)

# ----------------------------------------------------
# Startup Log (very important for prod debugging)
# ----------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Startup diagnostics."""
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info(
        f"[STARTUP] ENV={settings.app_env} | DB={settings.database_url}"
    )

# ----------------------------------------------------
# Health + Root
# ----------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Convia License Server", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}