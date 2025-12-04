"""Machine binding schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MachineBindingCreate(BaseModel):
    """Machine binding creation schema."""

    license_id: int = Field(..., description="License ID")
    machine_id: str = Field(..., description="Machine ID")


class MachineBindingOut(BaseModel):
    """Machine binding output schema."""

    id: int
    license_id: int
    machine_id: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True




