from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if payload.role not in {"customer", "provider"}:
        raise HTTPException(status_code=400, detail="Role must be 'customer' or 'provider'")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        phone=payload.phone,
        role=payload.role,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is suspended")

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current
