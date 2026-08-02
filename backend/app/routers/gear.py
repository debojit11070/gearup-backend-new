from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.category import Category
from app.models.gear import GearItem
from app.schemas.gear import CategoryOut, GearOut

router = APIRouter(tags=["Gear (Public)"])


@router.get("/api/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name.asc()).all()


@router.get("/api/gear", response_model=List[GearOut])
def list_gear(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search by name/brand/description"),
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = True,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(GearItem).options(joinedload(GearItem.category))
    if available_only:
        query = query.filter(GearItem.is_available.is_(True), GearItem.stock > 0)
    if category_id:
        query = query.filter(GearItem.category_id == category_id)
    if brand:
        query = query.filter(GearItem.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(GearItem.price_per_day >= min_price)
    if max_price is not None:
        query = query.filter(GearItem.price_per_day <= max_price)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                GearItem.name.ilike(like),
                GearItem.brand.ilike(like),
                GearItem.description.ilike(like),
            )
        )
    return (
        query.order_by(GearItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/api/gear/{gear_id}", response_model=GearOut)
def get_gear(gear_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(GearItem)
        .options(joinedload(GearItem.category))
        .filter(GearItem.id == gear_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Gear not found")
    return item
