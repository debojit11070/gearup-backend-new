import json
from decimal import Decimal
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.payment import Payment
from app.models.rental import RentalOrder
from app.models.user import User
from app.schemas.payment import PaymentConfirmIn, PaymentCreate, PaymentOut
from app.services.sslcommerz_service import (
    create_sslcommerz_session,
    validate_sslcommerz_transaction,
)
from app.services.stripe_service import create_stripe_checkout_session, retrieve_stripe_session

router = APIRouter(prefix="/api/payments", tags=["Payments"])


def _get_order_for_customer(db: Session, order_id: int, user: User) -> RentalOrder:
    order = (
        db.query(RentalOrder)
        .options(joinedload(RentalOrder.items))
        .filter(RentalOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Rental order not found")
    if order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    return order


@router.post("/create", response_model=PaymentOut)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    order = _get_order_for_customer(db, payload.rental_order_id, customer)
    if order.status in {"CANCELLED", "RETURNED"}:
        raise HTTPException(status_code=400, detail="Order cannot be paid in current status")
    if order.status == "PAID":
        raise HTTPException(status_code=400, detail="Order is already paid")

    amount = float(order.total_amount)
    currency = "USD" if payload.method == "stripe" else "BDT"
    tran_id = f"GU-{uuid4().hex[:16].upper()}"

    payment = Payment(
        rental_order_id=order.id,
        customer_id=customer.id,
        amount=Decimal(str(amount)),
        currency=currency,
        method=payload.method,
        provider=payload.method,
        status="pending",
        transaction_id=tran_id,
    )

    if payload.method == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(status_code=500, detail="Stripe is not configured")
        try:
            session = create_stripe_checkout_session(
                amount=amount,
                currency=currency,
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel?order_id={order.id}",
                metadata={"rental_order_id": str(order.id), "transaction_id": tran_id},
                product_name=f"GearUp Rental Order #{order.id}",
            )
            payment.gateway_url = session["url"]
            payment.transaction_id = session["id"]
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Stripe error: {exc}") from exc
    else:
        url = create_sslcommerz_session(
            amount=amount,
            currency=currency,
            tran_id=tran_id,
            success_url=f"{settings.FRONTEND_URL}/payment/success?order_id={order.id}",
            fail_url=f"{settings.FRONTEND_URL}/payment/cancel?order_id={order.id}",
            cancel_url=f"{settings.FRONTEND_URL}/payment/cancel?order_id={order.id}",
            product_name=f"GearUp Rental Order #{order.id}",
            cus_name=customer.name,
            cus_email=customer.email,
        )
        if not url:
            raise HTTPException(
                status_code=502,
                detail="Failed to initialize SSLCommerz session (check credentials)",
            )
        payment.gateway_url = url

    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/confirm", response_model=PaymentOut)
def confirm_payment(
    payload: PaymentConfirmIn,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    payment = None
    if payload.payment_id:
        payment = db.query(Payment).filter(Payment.id == payload.payment_id).first()
    elif payload.transaction_id:
        payment = (
            db.query(Payment)
            .filter(Payment.transaction_id == payload.transaction_id)
            .first()
        )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.customer_id != customer.id:
        raise HTTPException(status_code=403, detail="Not your payment")

    target_status = (payload.status or "completed").lower()
    payment.status = target_status
    if payload.payload is not None:
        payment.payload = json.dumps(payload.payload)
    if target_status == "completed":
        from datetime import datetime, timezone

        payment.paid_at = datetime.now(timezone.utc)
        order = db.query(RentalOrder).filter(RentalOrder.id == payment.rental_order_id).first()
        if order:
            order.status = "PAID"

    db.commit()
    db.refresh(payment)
    return payment


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        session_id = session_obj["id"]
        payment = (
            db.query(Payment)
            .filter(Payment.transaction_id == session_id)
            .first()
        )
        if payment and payment.status != "completed":
            payment.status = "completed"
            payment.payload = json.dumps({"stripe_event": event["type"], "id": session_id})
            from datetime import datetime, timezone

            payment.paid_at = datetime.now(timezone.utc)
            order = db.query(RentalOrder).filter(RentalOrder.id == payment.rental_order_id).first()
            if order:
                order.status = "PAID"
            db.commit()
    return {"received": True}


@router.post("/webhook/sslcommerz")
async def sslcommerz_webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    tran_id = form.get("tran_id")
    val_id = form.get("val_id")
    if not tran_id:
        raise HTTPException(status_code=400, detail="Missing tran_id")
    validation = validate_sslcommerz_transaction(
        tran_id=val_id or tran_id, amount=form.get("amount", "")
    )
    payment = (
        db.query(Payment).filter(Payment.transaction_id == tran_id).first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if validation.get("status") in {"VALID", "VALIDATED"}:
        payment.status = "completed"
        payment.payload = json.dumps(dict(form))
        from datetime import datetime, timezone

        payment.paid_at = datetime.now(timezone.utc)
        order = db.query(RentalOrder).filter(RentalOrder.id == payment.rental_order_id).first()
        if order:
            order.status = "PAID"
    else:
        payment.status = "failed"
        payment.payload = json.dumps(dict(form))
    db.commit()
    return {"received": True}


@router.get("", response_model=List[PaymentOut])
def list_my_payments(
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    return (
        db.query(Payment)
        .filter(Payment.customer_id == customer.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles("customer")),
):
    payment = (
        db.query(Payment).filter(Payment.id == payment_id, Payment.customer_id == customer.id).first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
