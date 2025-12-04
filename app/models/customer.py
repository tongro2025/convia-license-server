"""Customer model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Customer(Base):
    """Customer table model."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    paddle_customer_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    licenses = relationship("License", back_populates="customer", cascade="all, delete-orphan")


