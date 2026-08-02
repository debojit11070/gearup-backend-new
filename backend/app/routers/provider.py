from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.gear import GearItem
from app.models.user import User
from app.schemas.gear import GearCreate, GearOut, GearUpdate

router = APIRouter(prefix="/api/provider", tags=["Provider"])


@router.post("/gear", response_model=GearOut, status_code=status.HTTP_201_CREATED)
def add_gear(
    payload: GearCreate,
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    gear = GearItem(
        provider_id=provider.id,
        name=payload.name,
        brand=payload.brand,
        description=payload.description,
        price_per_day=payload.price_per_day,
        stock=payload.stock,
        image_url=payload.image_url,
        specs=payload.specs,
        is_available=payload.is_available,
        category_id=payload.category_id,
    )
    db.add(gear)
    db.commit()
    db.refresh(gear)
    return gear


@router.put("/gear/{gear_id}", response_model=GearOut)
def update_gear(
    gear_id: int,
    payload: GearUpdate,
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    gear = (
        db.query(GearItem)
        .filter(GearItem.id == gear_id, GearItem.provider_id == provider.id)
        .first()
    )
    if not gear:
        raise HTTPException(status_code=404, detail="Gear not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(gear, key, value)
    db.commit()
    db.refresh(gear)
    return gear


@router.delete("/gear/{gear_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gear(
    gear_id: int,
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    gear = (
        db.query(GearItem)
        .filter(GearItem.id == gear_id, GearItem.provider_id == provider.id)
        .first()
    )
    if not gear:
        raise HTTPException(status_code=404, detail="Gear not found")
    db.delete(gear)
    db.commit()


@router.get("/gear", response_model=List[GearOut])
def list_my_gear(
    db: Session = Depends(get_db),
    provider: User = Depends(require_roles("provider")),
):
    return (
        db.query(GearItem)
        .options(joinedload(GearItem.category))
        .filter(GearItem.provider_id == provider.id)
        .order_by(GearItem.created_at.desc())
        .all()
    )
