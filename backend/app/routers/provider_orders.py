from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.gear import GearItem
from app.models.rental import RentalOrder, RentalOrderItem
from app.models.user import User
from app.schemas.rental import RentalOrderOut, RentalStatusUpdate

router = APIRouter(prefix="/api/provider/orders", tags=["Provider Orders"])


@router.get("", response_model=List[RentalOrderOut])
def list_incoming_orders(
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    my_gear_ids = [
        g.id for g in db.query(GearItem.id).filter(GearItem.provider_id == provider.id).all()
    ]
    if not my_gear_ids:
        return []
    order_ids = (
        db.query(RentalOrder.id)
        .join(RentalOrder.items)
        .filter(RentalOrderItem.gear_id.in_(my_gear_ids))
        .distinct()
        .all()
    )
    ids = [r[0] for r in order_ids]
    if not ids:
        return []
    return (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .filter(RentalOrder.id.in_(ids))
        .order_by(RentalOrder.created_at.desc())
        .all()
    )


@router.patch("/{order_id}", response_model=RentalOrderOut)
def update_order_status(
    order_id: int,
    payload: RentalStatusUpdate,
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    order = (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .filter(RentalOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Rental order not found")

    owns = False
    for item in order.items:
        if item.gear_id is None:
            continue
        gear = db.query(GearItem).filter(GearItem.id == item.gear_id).first()
        if gear and gear.provider_id == provider.id:
            owns = True
            break
    if not owns:
        raise HTTPException(status_code=403, detail="Not allowed for this provider")

    if payload.status == "CANCELLED":
        for item in order.items:
            if item.gear_id:
                gear = db.query(GearItem).filter(GearItem.id == item.gear_id).first()
                if gear:
                    gear.stock += item.quantity
                    if gear.stock > 0:
                        gear.is_available = True
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
