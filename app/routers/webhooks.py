from fastapi import APIRouter, Request, HTTPException, Header
from ..utils.razorpay_client import verify_webhook_signature
from .. import db

router = APIRouter()


@router.post("/razorpay")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    body = await request.body()
    # verify signature
    if not verify_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()

    # persist raw webhook for traceability
    try:
        db.supabase.table("raw_webhooks").insert({"source": "razorpay", "payload": payload}).execute()
    except Exception:
        # best-effort: if raw_webhooks table not present, skip
        pass

    event = payload.get("event")

    # helper to safely find payment by payment_link_id
    def _find_payment_by_link_id(pl_id: str):
        if not pl_id:
            return None
        try:
            return db.get_payment_by_link(pl_id)
        except Exception:
            return None

    if event == "payment.link.paid":
        data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        pl_id = data.get("payment_link_id")
        payment = _find_payment_by_link_id(pl_id)
        if payment:
            # mark payment paid and persist payload
            try:
                db.update_payment(payment["payment_id"], {"status": "paid", "razorpay_payload": payload})
            except Exception:
                pass

            # finalize reservations and settle quote
            quote_id = payment.get("quote_id")
            if quote_id:
                try:
                    db.finalize_reservations(quote_id)
                except Exception:
                    pass
                try:
                    db.update_quote(quote_id, {"status": "settled"})
                except Exception:
                    pass

            # audit event
            try:
                db.create_audit_event({
                    "merchant_id": payment.get("merchant_id"),
                    "session_id": None,
                    "actor": "razorpay_webhook",
                    "action": "payment_link_paid",
                    "payload": {"payment_id": payment.get("payment_id"), "payment_link_id": pl_id, "raw": payload}
                })
            except Exception:
                pass

            # policy event: record successful settlement
            try:
                db.insert_policy_event({
                    "quote_id": quote_id,
                    "rule_name": "payment_settlement",
                    "result": "pass",
                    "rationale": {"payment_link_id": pl_id, "note": "payment confirmed by razorpay webhook"}
                })
            except Exception:
                pass

    elif event in ("payment.link.expired", "payment.failed"):
        data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        pl_id = data.get("payment_link_id")
        payment = _find_payment_by_link_id(pl_id)
        if payment:
            new_status = "expired" if event == "payment.link.expired" else "failed"
            try:
                db.update_payment(payment["payment_id"], {"status": new_status, "razorpay_payload": payload})
            except Exception:
                pass
            # release reservations and cancel quote
            quote_id = payment.get("quote_id")
            if quote_id:
                try:
                    db.release_reservations_by_quote(quote_id)
                except Exception:
                    pass
                try:
                    db.update_quote(quote_id, {"status": "cancelled"})
                except Exception:
                    pass
            # audit
            try:
                db.create_audit_event({
                    "merchant_id": payment.get("merchant_id"),
                    "session_id": None,
                    "actor": "razorpay_webhook",
                    "action": new_status,
                    "payload": {"payment_id": payment.get("payment_id"), "payment_link_id": pl_id, "raw": payload}
                })
            except Exception:
                pass

    return {"ok": True}
