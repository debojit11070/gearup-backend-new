from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class GearItem(Base):
    __tablename__ = "gear_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False, index=True)
    brand = Column(String(80), nullable=True, index=True)
    description = Column(Text, nullable=True)
    price_per_day = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=1)
    image_url = Column(String(500), nullable=True)
    specs = Column(Text, nullable=True)  # free-form JSON string
    is_available = Column(Boolean, nullable=False, default=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="gear_items")
    provider = relationship("User", back_populates="gear_items")
    reviews = relationship("Review", back_populates="gear_item", cascade="all, delete-orphan")
