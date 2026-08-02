import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_checkout_session(
    *,
    amount: float,
    currency: str,
    success_url: str,
    cancel_url: str,
    metadata: dict,
    product_name: str,
) -> dict:
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": product_name},
                    "unit_amount": int(round(amount * 100)),
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    return {
        "id": session.id,
        "url": session.url,
        "amount": amount,
        "currency": currency,
    }


def retrieve_stripe_session(session_id: str) -> dict:
    return stripe.checkout.Session.retrieve(session_id)
