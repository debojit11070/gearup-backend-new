from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = Field(None, max_length=40)
    role: Literal["customer", "provider"] = "customer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]
