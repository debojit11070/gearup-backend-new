import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.all import Category, GearItem, User
from app.routers import admin, auth, gear, payments, provider, provider_orders, rentals, reviews

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gearup")


def _ensure_schema():
    Base.metadata.create_all(bind=engine)


def _seed_defaults():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == settings.ADMIN_SEED_EMAIL).first():
            admin_user = User(
                name="Admin",
                email=settings.ADMIN_SEED_EMAIL,
                password=hash_password(settings.ADMIN_SEED_PASSWORD),
                role="admin",
                status="active",
            )
            db.add(admin_user)
            db.commit()
            logger.info("Seeded admin: %s", settings.ADMIN_SEED_EMAIL)

        default_categories = [
            ("Cycling", "cycling", "Bikes, helmets, accessories"),
            ("Camping", "camping", "Tents, sleeping bags, cookware"),
            ("Fitness", "fitness", "Dumbbells, mats, bands"),
            ("Water Sports", "water-sports", "Kayaks, paddles, life vests"),
            ("Winter Sports", "winter-sports", "Skis, snowboards, boots"),
            ("Hiking", "hiking", "Backpacks, trekking poles, boots"),
        ]
        for name, slug, desc in default_categories:
            if not db.query(Category).filter(Category.slug == slug).first():
                db.add(Category(name=name, slug=slug, description=desc))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_schema()
    _seed_defaults()
    yield


app = FastAPI(
    title="GearUp API",
    version="1.0.0",
    description="Backend API for the GearUp sports & outdoor gear rental platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {"service": "GearUp API", "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(gear.router)
app.include_router(provider.router)
app.include_router(provider_orders.router)
app.include_router(rentals.router)
app.include_router(payments.router)
app.include_router(reviews.router)
app.include_router(admin.router)
