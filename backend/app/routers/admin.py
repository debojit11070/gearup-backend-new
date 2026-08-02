from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.gear import GearItem
from app.models.rental import RentalOrder
from app.models.user import User
from app.schemas.auth import UserOut, UserStatusUpdate
from app.schemas.gear import CategoryCreate, CategoryOut, GearOut
from app.schemas.rental import RentalOrderOut

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = payload.status
    db.commit()
    db.refresh(user)
    return user


@router.get("/gear", response_model=List[GearOut])
def list_all_gear(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return (
        db.query(GearItem)
        .options(joinedload(GearItem.category))
        .order_by(GearItem.created_at.desc())
        .all()
    )


@router.get("/rentals", response_model=List[RentalOrderOut])
def list_all_rentals(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .order_by(RentalOrder.created_at.desc())
        .all()
    )


@router.get("/categories", response_model=List[CategoryOut])
def list_categories_admin(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return db.query(Category).order_by(Category.name.asc()).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    if db.query(Category).filter(Category.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="Slug already exists")
    cat = Category(name=payload.name, slug=payload.slug, description=payload.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
