from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    gear_id: int
    rental_order_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    gear_id: int
    customer_id: int
    rental_order_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
