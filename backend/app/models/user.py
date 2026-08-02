from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    phone = Column(String(40), nullable=True)
    role = Column(String(20), nullable=False)  # customer | provider | admin
    status = Column(String(20), nullable=False, default="active")  # active | suspended
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gear_items = relationship("GearItem", back_populates="provider", cascade="all, delete-orphan")
    rental_orders = relationship("RentalOrder", back_populates="customer", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="customer", cascade="all, delete-orphan")
