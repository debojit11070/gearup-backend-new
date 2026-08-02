from typing import Optional

import requests

from app.core.config import settings


def create_sslcommerz_session(
    *,
    amount: float,
    currency: str,
    tran_id: str,
    success_url: str,
    fail_url: str,
    cancel_url: str,
    product_name: str,
    cus_name: str,
    cus_email: str,
) -> Optional[str]:
    if not settings.SSLCOMMERZ_STORE_ID or not settings.SSLCOMMERZ_STORE_PASSWORD:
        return None

    payload = {
        "store_id": settings.SSLCOMMERZ_STORE_ID,
        "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
        "total_amount": str(amount),
        "currency": currency,
        "tran_id": tran_id,
        "success_url": success_url,
        "fail_url": fail_url,
        "cancel_url": cancel_url,
        "ipn_url": "",
        "product_name": product_name,
        "product_category": "Sports & Outdoor",
        "product_profile": "general",
        "cus_name": cus_name,
        "cus_email": cus_email,
        "cus_add1": "N/A",
        "cus_city": "Dhaka",
        "cus_state": "Dhaka",
        "cus_postcode": "1000",
        "cus_country": "Bangladesh",
        "cus_phone": "01711111111",
        "shipping_method": "NO",
        "num_of_item": 1,
    }

    try:
        resp = requests.post(settings.SSLCOMMERZ_SESSION_API, data=payload, timeout=15)
        data = resp.json()
    except Exception:
        return None

    if data.get("status") == "SUCCESS":
        return data.get("GatewayPageURL")
    return None


def validate_sslcommerz_transaction(*, tran_id: str, amount: str) -> dict:
    params = {
        "val_id": tran_id,
        "store_id": settings.SSLCOMMERZ_STORE_ID,
        "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
        "format": "json",
        "v": 1,
    }
    try:
        resp = requests.get(settings.SSLCOMMERZ_VALIDATION_API, params=params, timeout=15)
        return resp.json()
    except Exception:
        return {"status": "FAILED"}
