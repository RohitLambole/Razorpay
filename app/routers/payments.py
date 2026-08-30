from fastapi import APIRouter, HTTPException, Body
from ..schemas import PaymentCreateRequest
from .. import db
from ..utils.razorpay_client import create_order_and_payment_link
from uuid import uuid4

router = APIRouter()


@router.post("/create", status_code=201)
def create_payment(payload: PaymentCreateRequest):
    # Fetch quote
    q = db.supabase.table("quotes").select("*").eq("quote_id", payload.quote_id).limit(1).execute().data
    if not q:
        raise HTTPException(status_code=404, detail="quote not found")
    q = q[0]
    # Idempotency: check existing payment with same idempotency key stored in payments.razorpay_payload->'idempotency_key'
    existing = db.supabase.table("payments").select("*").execute().data or []
    for p in existing:
        rpl = p.get("razorpay_payload") or {}
        if rpl.get("idempotency_key") == payload.idempotency_key:
            return {"payment_id": p["payment_id"], "status": p["status"], "razorpay_payment_link_id": p.get("razorpay_payment_link_id")}

    # Create payment with Razorpay
    resp = create_order_and_payment_link(q["final_amount_cents"])
    payment_id = str(uuid4())
    payment_row = {
        "payment_id": payment_id,
        "quote_id": payload.quote_id,
        "merchant_id": q["merchant_id"],
        "razorpay_order_id": resp["order"].get("id"),
        "razorpay_payment_link_id": resp["payment_link"].get("id"),
        "razorpay_payload": {"idempotency_key": payload.idempotency_key, "raw": resp},
        "status": "created"
    }
    db.create_payment(payment_row)
    db.create_audit_event({
        "merchant_id": q["merchant_id"],
        "session_id": None,
        "actor": "system",
        "action": "create_payment",
        "payload": {"payment_id": payment_id, "razorpay_order": resp["order"].get("id")}
    })
    return {"payment_id": payment_id, "payment_link": resp["payment_link"].get("short_url")}