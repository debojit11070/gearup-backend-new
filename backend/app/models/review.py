from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    gear_id = Column(Integer, ForeignKey("gear_items.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rental_order_id = Column(Integer, ForeignKey("rental_orders.id", ondelete="SET NULL"))
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gear_item = relationship("GearItem", back_populates="reviews")
    customer = relationship("User", back_populates="reviews")
