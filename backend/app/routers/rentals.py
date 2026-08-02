from datetime import date
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.gear import GearItem
from app.models.rental import RentalOrder, RentalOrderItem
from app.models.user import User
from app.schemas.rental import RentalCreate, RentalOrderOut, RentalStatusUpdate

router = APIRouter(prefix="/api/rentals", tags=["Rentals"])


@router.post("", response_model=RentalOrderOut, status_code=status.HTTP_201_CREATED)
def create_rental(
    payload: RentalCreate,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    days = (payload.end_date - payload.start_date).days + 1
    if days < 1:
        raise HTTPException(status_code=400, detail="Invalid rental period")

    order = RentalOrder(
        customer_id=customer.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="PLACED",
        notes=payload.notes,
        total_amount=Decimal("0"),
    )
    db.add(order)
    db.flush()

    total = Decimal("0")
    for item_in in payload.items:
        gear = db.query(GearItem).filter(GearItem.id == item_in.gear_id).first()
        if not gear:
            raise HTTPException(status_code=404, detail=f"Gear {item_in.gear_id} not found")
        if not gear.is_available or gear.stock < item_in.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{gear.name}' is out of stock for requested quantity",
            )
        line_total = Decimal(str(gear.price_per_day)) * item_in.quantity * days
        total += line_total
        order.items.append(
            RentalOrderItem(
                gear_id=gear.id,
                gear_name_snapshot=gear.name,
                unit_price=Decimal(str(gear.price_per_day)),
                quantity=item_in.quantity,
                days=days,
                line_total=line_total,
            )
        )
        gear.stock -= item_in.quantity
        if gear.stock <= 0:
            gear.is_available = False

    order.total_amount = total
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=List[RentalOrderOut])
def list_my_rentals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(RentalOrder).options(joinedload(RentalOrder.items))
    if user.role == "customer":
        query = query.filter(RentalOrder.customer_id == user.id)
    return query.order_by(RentalOrder.created_at.desc()).all()


@router.get("/{order_id}", response_model=RentalOrderOut)
def get_rental(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .filter(RentalOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Rental order not found")
    if user.role == "customer" and order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if user.role == "provider":
        owns = any(
            item.gear_id is not None
            and db.query(GearItem).filter(GearItem.id == item.gear_id, GearItem.provider_id == user.id).first()
            for item in order.items
        )
        if not owns:
            raise HTTPException(status_code=403, detail="Not allowed")
    return order


@router.post("/{order_id}/cancel", response_model=RentalOrderOut)
def cancel_my_rental(
    order_id: int,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    order = (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .filter(RentalOrder.id == order_id, RentalOrder.customer_id == customer.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Rental order not found")
    if order.status not in {"PLACED", "CONFIRMED"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order in status {order.status}",
        )
    for item in order.items:
        if item.gear_id:
            gear = db.query(GearItem).filter(GearItem.id == item.gear_id).first()
            if gear:
                gear.stock += item.quantity
                if gear.stock > 0:
                    gear.is_available = True
    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)
    return order
