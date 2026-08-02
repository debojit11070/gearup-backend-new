from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.gear import GearItem
from app.models.rental import RentalOrder
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    gear = db.query(GearItem).filter(GearItem.id == payload.gear_id).first()
    if not gear:
        raise HTTPException(status_code=404, detail="Gear not found")

    if payload.rental_order_id:
        order = (
            db.query(RentalOrder)
            .filter(
                RentalOrder.id == payload.rental_order_id,
                RentalOrder.customer_id == customer.id,
            )
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Rental order not found")
        if order.status != "RETURNED":
            raise HTTPException(
                status_code=400, detail="Reviews allowed only after rental return"
            )

    review = Review(
        gear_id=payload.gear_id,
        customer_id=customer.id,
        rental_order_id=payload.rental_order_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/gear/{gear_id}", response_model=list[ReviewOut])
def list_reviews_for_gear(
    gear_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return (
        db.query(Review)
        .filter(Review.gear_id == gear_id)
        .order_by(Review.created_at.desc())
        .all()
    )
