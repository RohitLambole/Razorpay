from fastapi import APIRouter, HTTPException, Body
from ..schemas import PaymentCreateRequest
from .. import db
from ..utils.razorpay_client import create_order_and_payment_link
from uuid import uuid4

router = APIRouter()


# Try to import a typed Postgrest/Postgres client exception for robust handling.
# This is optional and will silently fall back if the package is not available.
PostgrestError = None
try:
    from postgrest import PostgrestError as _PostgrestError  # type: ignore
    PostgrestError = _PostgrestError
except Exception:
    try:
        from postgrest_py import PostgrestError as _PostgrestError  # type: ignore
        PostgrestError = _PostgrestError
    except Exception:
        PostgrestError = None


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

    # Insert payment with DB-level idempotency race handling.
    try:
        db.create_payment(payment_row)
    except Exception as e:
        # Determine if this is a Postgres unique-violation (SQLSTATE 23505) on the
        # payments (merchant_id, idempotency_key) constraint. Prefer typed exception
        # inspection if a PostgrestError is available; otherwise fall back to
        # inspecting common attributes/messages for the SQLSTATE or constraint name.
        is_unique_violation = False

        # Typed exception path
        try:
            if PostgrestError is not None and isinstance(e, PostgrestError):
                code = getattr(e, "code", None) or getattr(e, "status_code", None) or None
                constraint = getattr(e, "constraint", None)
                if code == "23505" or constraint == "uq_payments_merchant_idempotency":
                    is_unique_violation = True
        except Exception:
            # in case accessing attributes fails, continue to fallback checks
            is_unique_violation = False

        # Fallback inspection
        if not is_unique_violation:
            code = getattr(e, "code", None)
            msg = str(e).lower()
            if code == "23505" or "23505" in msg or "uq_payments_merchant_idempotency" in msg or "unique constraint" in msg or "duplicate key" in msg:
                is_unique_violation = True

        if is_unique_violation:
            # Recovery: find the winning payment row and return it.
            try:
                winner = db.get_payment_by_idempotency(q["merchant_id"], payload.idempotency_key)
            except Exception:
                raise HTTPException(status_code=500, detail="Idempotency conflict: failed to query existing payment after unique constraint violation")

            if winner:
                # Do NOT create audit events from the losing request.
                return {"payment_id": winner["payment_id"], "status": winner.get("status"), "razorpay_payment_link_id": winner.get("razorpay_payment_link_id")}

            # If winner row not found, return 500: we cannot safely continue.
            raise HTTPException(status_code=500, detail="Idempotency conflict: unique constraint violation but existing payment not found")

        # Not an idempotency-related DB error; surface as 500
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {e}")

    db.create_audit_event({
        "merchant_id": q["merchant_id"],
        "session_id": None,
        "actor": "system",
        "action": "create_payment",
        "payload": {"payment_id": payment_id, "razorpay_order": resp["order"].get("id")}
    })
    # finalize reservations only after payment success webhook. For now, keep reserved until paid.
    return {"payment_id": payment_id, "payment_link": resp["payment_link"].get("short_url")}
