import os
from typing import Dict, Any, Tuple

import razorpay
from fastapi import HTTPException
from hashlib import sha256
import hmac

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set")

_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_order_and_payment_link(amount_cents: int, currency: str = "INR", idempotency_key: str = None) -> Dict[str, Any]:
    # amount expected in paise (cents): Razorpay uses INR paise
    payload = {"amount": amount_cents, "currency": currency, "accept_partial": False}
    # Create order
    order = _client.order.create(data={
        "amount": amount_cents,
        "currency": currency,
        "receipt": idempotency_key or "receipt_auto",
        "payment_capture": 1
    })
    # Create payment link referencing order
    pl_payload = {
        "amount": amount_cents,
        "currency": currency,
        "reference_id": order.get("id"),
        "description": "Agentic Commerce Payment",
        "customer": {"name": "B2B Buyer"},
        "notifications": {"sms": False, "email": False},
        "callback_method": "get"
    }
    payment_link = _client.payment_link.create(pl_payload)
    return {"order": order, "payment_link": payment_link}


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    generated = hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(), body, sha256).hexdigest()
    # Razorpay signature uses sha256 HMAC, provided as hexdigest in headers
    return hmac.compare_digest(generated, signature)