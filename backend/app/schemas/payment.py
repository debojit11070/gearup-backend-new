from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    rental_order_id: int
    method: Literal["stripe", "sslcommerz"]


class PaymentOut(BaseModel):
    id: int
    rental_order_id: int
    customer_id: int
    amount: Decimal
    currency: str
    method: str
    provider: str
    status: str
    transaction_id: Optional[str] = None
    gateway_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentConfirmIn(BaseModel):
    payment_id: Optional[int] = None
    transaction_id: Optional[str] = None
    status: Optional[Literal["completed", "failed", "cancelled"]] = None
    payload: Optional[dict] = None
