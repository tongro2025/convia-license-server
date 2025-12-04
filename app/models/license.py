"""License model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class License(Base):
    """License table model."""

    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    paddle_subscription_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True, nullable=True)  # Customer email
    allowed_containers = Column(Integer, default=1, nullable=False)  # -1 means unlimited
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    status = Column(String, default="active", nullable=False)  # active, cancelled, expired
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="licenses")
    machine_bindings = relationship("MachineBinding", back_populates="license", cascade="all, delete-orphan")
    magic_tokens = relationship("MagicToken", back_populates="license", cascade="all, delete-orphan")
    license_usages = relationship("LicenseUsage", back_populates="license", cascade="all, delete-orphan")




