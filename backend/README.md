# GearUp Backend

FastAPI + SQLAlchemy backend for the **GearUp** sports & outdoor gear rental platform, backed by a **Neon PostgreSQL** database.

## Tech Stack

- **FastAPI** + **Uvicorn** (Python 3.11+)
- **SQLAlchemy 2.x** ORM
- **Neon PostgreSQL** (via `psycopg2`)
- **JWT** auth (python-jose) with **bcrypt** password hashing (passlib)
- **Stripe Checkout** (`stripe` SDK)
- **SSLCommerz** hosted checkout (REST via `requests`)
- **Pydantic v2** validation

## Roles

- `customer` – browse gear, place rentals, pay, review
- `provider` – manage own gear inventory and incoming orders
- `admin` – manage users, categories, oversee rentals

> ⚠️ Role `admin` is **not** created via `/api/auth/register`. It is seeded automatically on first boot using `ADMIN_SEED_EMAIL` / `ADMIN_SEED_PASSWORD` from `.env`.

## Project Layout

```
backend/
├── app/
│   ├── core/        # config, database, security, deps
│   ├── models/      # SQLAlchemy models
│   ├── schemas/     # Pydantic schemas
│   ├── services/    # Stripe + SSLCommerz integrations
│   ├── routers/     # API endpoints
│   └── main.py
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then fill in values
```

### Required `.env` Values

| Key | Purpose |
|-----|---------|
| `DATABASE_URL` | Neon Postgres connection string (must include `?sslmode=require`) |
| `JWT_SECRET` | Long random string |
| `STRIPE_SECRET_KEY` | Stripe test secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) |
| `SSLCOMMERZ_STORE_ID` / `SSLCOMMERZ_STORE_PASSWORD` | Sandbox credentials from SSLCommerz |
| `FRONTEND_URL` | Used for Stripe/SSLCommerz success/cancel redirect URLs |
| `ADMIN_SEED_EMAIL` / `ADMIN_SEED_PASSWORD` | Created on first boot |

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API root: <http://localhost:8000>
- Interactive docs (Swagger): <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

Tables are auto-created (`Base.metadata.create_all`) on startup. Default categories and the admin user are seeded automatically.

## API Endpoints

### Auth
- `POST /api/auth/register` – Register a `customer` or `provider`
- `POST /api/auth/login` – Returns `{ access_token, user }`
- `GET  /api/auth/me` – Current user (Bearer token)

### Public Gear
- `GET  /api/categories`
- `GET  /api/gear?q&category_id&brand&min_price&max_price&available_only&limit&offset`
- `GET  /api/gear/{id}`

### Rentals (customer)
- `POST /api/rentals`
- `GET  /api/rentals`
- `GET  /api/rentals/{id}`
- `POST /api/rentals/{id}/cancel`

### Payments (customer)
- `POST /api/payments/create` – body: `{ rental_order_id, method: "stripe" | "sslcommerz" }`
- `POST /api/payments/confirm` – manual confirmation fallback
- `POST /api/payments/webhook/stripe` – Stripe webhook
- `POST /api/payments/webhook/sslcommerz` – SSLCommerz IPN/callback
- `GET  /api/payments`
- `GET  /api/payments/{id}`

### Provider
- `GET  /api/provider/gear` – list own gear
- `POST /api/provider/gear` – create
- `PUT  /api/provider/gear/{id}` – update
- `DELETE /api/provider/gear/{id}`
- `GET  /api/provider/orders` – incoming orders
- `PATCH /api/provider/orders/{id}` – update status

### Reviews
- `POST /api/reviews` – only after rental is `RETURNED`
- `GET  /api/reviews/gear/{gearId}` – list

### Admin
- `GET  /api/admin/users`
- `PATCH /api/admin/users/{id}` – `{ status: "active" | "suspended" }`
- `GET  /api/admin/gear`
- `GET  /api/admin/rentals`
- `GET  /api/admin/categories`
- `POST /api/admin/categories`

## Order Status Flow

```
PLACED ──(provider confirms)──▶ CONFIRMED ──(payment completed)──▶ PAID
   │                                  │
   └──(customer cancels)──▶ CANCELLED  └──(pickup)──▶ PICKED_UP ──▶ RETURNED
```

## Frontend Webhook / Redirect URLs

Set `FRONTEND_URL` to your deployed frontend. Stripe success URLs are
`{FRONTEND_URL}/payments/stripe/success?session_id={CHECKOUT_SESSION_ID}` and
SSLCommerz success is `{FRONTEND_URL}/payments/sslcommerz/success?order_id={id}`.
On your frontend, after success, call `POST /api/payments/confirm` with the
`payment_id` to force-complete the record (or rely on the webhook in production).
