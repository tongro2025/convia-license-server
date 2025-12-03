"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import (
    admin_license,
    admin_webhook,
    paddle_webhook,
    public_license,
)

app = FastAPI(
    title="Convia License Server",
    description="License verification and management server with Paddle integration",
    version="0.1.0",
)

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Convia License Server", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

