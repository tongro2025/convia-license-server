"""Machine binding model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class MachineBinding(Base):
    """Machine binding table model - maps licenses to machine IDs."""

    __tablename__ = "machine_bindings"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    machine_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    license = relationship("License", back_populates="machine_bindings")





