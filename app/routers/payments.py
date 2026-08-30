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

    # Idempotency: check existing payment with same idempotency key
    existing = db.get_payment_by_idempotency(q["merchant_id"], payload.idempotency_key)
    if existing:
        return {"payment_id": existing["payment_id"], "status": existing["status"], "razorpay_payment_link_id": existing.get("razorpay_payment_link_id")}

    # Reserve inventory for quote items (TTL 15 minutes)
    # fetch quote items
    items = db.supabase.table("quote_items").select("product_id, quantity").eq("quote_id", payload.quote_id).execute().data or []
    try:
        db.reserve_inventory_for_quote(payload.quote_id, items, ttl_minutes=15)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Create payment with Razorpay
    try:
        resp = create_order_and_payment_link(q["final_amount_cents"])
    except Exception as e:
        # release reservations on failure
        db.release_reservations_by_quote(payload.quote_id)
        raise HTTPException(status_code=502, detail=f"Razorpay error: {e}")

    payment_id = str(uuid4())
    payment_row = {
        "payment_id": payment_id,
        "quote_id": payload.quote_id,
        "merchant_id": q["merchant_id"],
        "razorpay_order_id": resp["order"].get("id"),
        "razorpay_payment_link_id": resp["payment_link"].get("id"),
        "razorpay_payload": {"idempotency_key": payload.idempotency_key, "raw": resp},
        "status": "created",
        "idempotency_key": payload.idempotency_key,
        "created_at": None,
    }
    db.create_payment(payment_row)
    db.create_audit_event({
        "merchant_id": q["merchant_id"],
        "session_id": None,
        "actor": "system",
        "action": "create_payment",
        "payload": {"payment_id": payment_id, "razorpay_order": resp["order"].get("id")}
    })
    # finalize reservations only after payment success webhook. For now, keep reserved until paid.
    return {"payment_id": payment_id, "payment_link": resp["payment_link"].get("short_url")}
