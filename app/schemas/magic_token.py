"""Magic token schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class MagicLinkRequest(BaseModel):
    """Magic link request schema."""

    license_key: str = Field(..., description="License key to generate magic link for")
    email: Optional[str] = Field(None, description="Email address (optional)")


class MagicLinkClaimResponse(BaseModel):
    """Magic link claim response schema."""

    success: bool = Field(..., description="Whether the claim was successful")
    message: str = Field(..., description="Response message")
    license_id: Optional[int] = Field(None, description="License ID if successful")

