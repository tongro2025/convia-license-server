"""License schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LicenseVerifyRequest(BaseModel):
    """License verification request schema."""

    license_key: str = Field(..., description="License key to verify")
    machine_id: str = Field(..., description="Machine ID to bind license to")
    container_id: Optional[str] = Field(None, description="Container ID (optional)")


class LicenseVerifyResponse(BaseModel):
    """License verification response schema."""

    valid: bool = Field(..., description="Whether the license is valid")
    message: str = Field(..., description="Response message")
    license_id: Optional[int] = Field(None, description="License ID if valid")
    allowed_containers: Optional[int] = Field(None, description="Maximum allowed containers (-1 for unlimited)")
    current_usage: Optional[int] = Field(None, description="Current number of containers in use")


class LicenseOut(BaseModel):
    """License output schema."""

    id: int
    paddle_subscription_id: str
    email: Optional[str] = None
    allowed_containers: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True




