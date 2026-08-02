from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    rental_order_id = Column(Integer, ForeignKey("rental_orders.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    method = Column(String(30), nullable=False)  # stripe | sslcommerz
    provider = Column(String(30), nullable=False)  # stripe | sslcommerz
    status = Column(String(20), nullable=False, default="pending")  # pending | completed | failed | cancelled
    transaction_id = Column(String(120), nullable=True, index=True)
    gateway_url = Column(String(800), nullable=True)  # for redirect-based flows (SSLCommerz)
    payload = Column(String, nullable=True)  # raw response json
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("RentalOrder", back_populates="payments")
