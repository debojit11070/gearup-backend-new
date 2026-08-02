from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RentalItemIn(BaseModel):
    gear_id: int
    quantity: int = Field(1, ge=1)


class RentalCreate(BaseModel):
    items: List[RentalItemIn] = Field(..., min_length=1)
    start_date: date
    end_date: date
    notes: Optional[str] = None


class RentalItemOut(BaseModel):
    id: int
    gear_id: Optional[int]
    gear_name_snapshot: str
    unit_price: Decimal
    quantity: int
    days: int
    line_total: Decimal

    class Config:
        from_attributes = True


class RentalOrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    start_date: date
    end_date: date
    total_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[RentalItemOut] = []

    class Config:
        from_attributes = True


class RentalStatusUpdate(BaseModel):
    status: Literal["PLACED", "CONFIRMED", "PAID", "PICKED_UP", "RETURNED", "CANCELLED"]