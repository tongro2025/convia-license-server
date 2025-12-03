"""License schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LicenseVerifyRequest(BaseModel):
    """License verification request schema."""

    license_key: str = Field(..., description="License key to verify")
    machine_id: str = Field(..., description="Machine ID to bind license to")


class LicenseVerifyResponse(BaseModel):
    """License verification response schema."""

    valid: bool = Field(..., description="Whether the license is valid")
    message: str = Field(..., description="Response message")
    license_id: Optional[int] = Field(None, description="License ID if valid")


class LicenseOut(BaseModel):
    """License output schema."""

    id: int
    paddle_subscription_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

