from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GearBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    brand: Optional[str] = Field(None, max_length=80)
    description: Optional[str] = None
    price_per_day: float = Field(..., ge=0)
    stock: int = Field(1, ge=0)
    image_url: Optional[str] = None
    specs: Optional[str] = None
    is_available: bool = True
    category_id: Optional[int] = None


class GearCreate(GearBase):
    pass


class GearUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=160)
    brand: Optional[str] = None
    description: Optional[str] = None
    price_per_day: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    specs: Optional[str] = None
    is_available: Optional[bool] = None
    category_id: Optional[int] = None


class GearOut(GearBase):
    id: int
    provider_id: int
    category: Optional[CategoryOut] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
