"""Magic token model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class MagicToken(Base):
    """Magic token table model - for magic link activation."""

    __tablename__ = "magic_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    license = relationship("License", back_populates="magic_tokens")










