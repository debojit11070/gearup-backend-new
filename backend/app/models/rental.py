from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RentalOrder(Base):
    __tablename__ = "rental_orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="PLACED")
    # PLACED | CONFIRMED | PAID | PICKED_UP | RETURNED | CANCELLED
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("User", back_populates="rental_orders")
    items = relationship("RentalOrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class RentalOrderItem(Base):
    __tablename__ = "rental_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("rental_orders.id", ondelete="CASCADE"), nullable=False)
    gear_id = Column(Integer, ForeignKey("gear_items.id", ondelete="SET NULL"))
    gear_name_snapshot = Column(String(180), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    days = Column(Integer, nullable=False, default=1)
    line_total = Column(Numeric(10, 2), nullable=False)

    order = relationship("RentalOrder", back_populates="items")
