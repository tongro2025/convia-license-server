"""License usage model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class LicenseUsage(Base):
    """License usage table model - tracks container usage per license."""

    __tablename__ = "license_usages"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    machine_id = Column(String, nullable=False, index=True)
    container_id = Column(String, nullable=True, index=True)  # Optional container identifier
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    license = relationship("License", back_populates="license_usages")
