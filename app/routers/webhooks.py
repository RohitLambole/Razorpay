from fastapi import APIRouter, Request, HTTPException, Header
from ..utils.razorpay_client import verify_webhook_signature
from .. import db

router = APIRouter()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
):
    body = await request.body()

    # Verify Razorpay signature
    if not verify_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")

    print(f"[WEBHOOK] Received event: {event}")

    # Best-effort raw webhook persistence.
    # raw_webhooks may not exist in this database.
    try:
        db.supabase.table("raw_webhooks").insert(
            {
                "source": "razorpay",
                "payload": payload,
            }
        ).execute()
    except Exception as exc:
        print(f"[WEBHOOK] raw_webhooks unavailable/skipped: {exc}")

    # ---------------------------------------------------------
    # Extract identifiers from Razorpay webhook payload
    # ---------------------------------------------------------

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    payment_link_entity = (
        payload
        .get("payload", {})
        .get("payment_link", {})
        .get("entity", {})
    )

    order_entity = (
        payload
        .get("payload", {})
        .get("order", {})
        .get("entity", {})
    )

    # Payment Link webhook:
    # payload.payment_link.entity.id
    payment_link_id = payment_link_entity.get("id")

    # Payment webhook:
    # payload.payment.entity.order_id
    order_id = payment_entity.get("order_id")

    print(
        f"[WEBHOOK] event={event} "
        f"payment_link_id={payment_link_id} "
        f"order_id={order_id}"
    )

    # ---------------------------------------------------------
    # Find our local payment
    # ---------------------------------------------------------

    payment = None

    if payment_link_id:
        try:
            payment = db.get_payment_by_link(payment_link_id)
        except Exception as exc:
            print(
                f"[WEBHOOK] Error finding payment by link "
                f"{payment_link_id}: {exc}"
            )

    # Fallback: find by Razorpay order ID
    if payment is None and order_id:
        try:
            response = (
                db.supabase
                .table("payments")
                .select("*")
                .eq("razorpay_order_id", order_id)
                .limit(1)
                .execute()
            )

            if response.data:
                payment = response.data[0]

        except Exception as exc:
            print(
                f"[WEBHOOK] Error finding payment by order "
                f"{order_id}: {exc}"
            )

    if payment is None:
        print(
            f"[WEBHOOK] No local payment found for "
            f"payment_link_id={payment_link_id}, "
            f"order_id={order_id}"
        )

        # Return 200 so Razorpay doesn't endlessly retry
        # an event that does not belong to a local payment.
        return {"ok": True}

    print(
        f"[WEBHOOK] Matched local payment: "
        f"{payment.get('payment_id')}"
    )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    if event in ("payment_link.paid","payment.link.paid", "payment.captured"):
        payment_id = payment["payment_id"]
        quote_id = payment.get("quote_id")

        # Update payment
        try:
            db.update_payment(
                payment_id,
                {
                    "status": "paid",
                    "razorpay_payload": payload,
                },
            )

            print(
                f"[WEBHOOK] Payment {payment_id} marked paid"
            )

        except Exception as exc:
            print(
                f"[WEBHOOK] FAILED updating payment "
                f"{payment_id}: {exc}"
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to update payment",
            )

        # Finalize reservation
        if quote_id:
            try:
                db.finalize_reservations(quote_id)

                print(
                    f"[WEBHOOK] Reservations finalized "
                    f"for quote {quote_id}"
                )

            except Exception as exc:
                print(
                    f"[WEBHOOK] FAILED finalizing reservations "
                    f"for quote {quote_id}: {exc}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to finalize reservations",
                )

            # Settle quote
            try:
                db.update_quote(
                    quote_id,
                    {"status": "settled"},
                )

                print(
                    f"[WEBHOOK] Quote {quote_id} settled"
                )

            except Exception as exc:
                print(
                    f"[WEBHOOK] FAILED settling quote "
                    f"{quote_id}: {exc}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to settle quote",
                )

        # Audit event
        try:
            db.create_audit_event(
                {
                    "merchant_id": payment.get("merchant_id"),
                    "session_id": None,
                    "actor": "razorpay_webhook",
                    "action": "payment_link_paid",
                    "payload": {
                        "payment_id": payment_id,
                        "payment_link_id": payment_link_id,
                        "raw": payload,
                    },
                }
            )
        except Exception as exc:
            print(
                f"[WEBHOOK] Audit event failed: {exc}"
            )

        # Policy event
        try:
            db.insert_policy_event(
                {
                    "quote_id": quote_id,
                    "rule_name": "payment_settlement",
                    "result": "pass",
                    "rationale": {
                        "payment_link_id": payment_link_id,
                        "order_id": order_id,
                        "note": "payment confirmed by Razorpay webhook",
                    },
                }
            )
        except Exception as exc:
            print(
                f"[WEBHOOK] Policy event failed: {exc}"
            )

        return {
            "ok": True,
            "event": event,
            "payment_id": payment_id,
        }

    # ---------------------------------------------------------
    # FAILED / EXPIRED
    # ---------------------------------------------------------

    if event in ("payment_link.expirted","payment.link.expired", "payment.failed"):
        payment_id = payment["payment_id"]
        quote_id = payment.get("quote_id")

        new_status = (
            "expired"
            if event == "payment.link.expired"
            else "failed"
        )

        try:
            db.update_payment(
                payment_id,
                {
                    "status": new_status,
                    "razorpay_payload": payload,
                },
            )

            print(
                f"[WEBHOOK] Payment {payment_id} marked "
                f"{new_status}"
            )

        except Exception as exc:
            print(
                f"[WEBHOOK] Failed updating payment: {exc}"
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to update payment",
            )

        if quote_id:
            try:
                db.release_reservations_by_quote(
                    quote_id
                )
            except Exception as exc:
                print(
                    f"[WEBHOOK] Failed releasing reservations: "
                    f"{exc}"
                )

            try:
                db.update_quote(
                    quote_id,
                    {"status": "cancelled"},
                )
            except Exception as exc:
                print(
                    f"[WEBHOOK] Failed cancelling quote: "
                    f"{exc}"
                )

        try:
            db.create_audit_event(
                {
                    "merchant_id": payment.get("merchant_id"),
                    "session_id": None,
                    "actor": "razorpay_webhook",
                    "action": new_status,
                    "payload": {
                        "payment_id": payment_id,
                        "payment_link_id": payment_link_id,
                        "raw": payload,
                    },
                }
            )
        except Exception as exc:
            print(
                f"[WEBHOOK] Audit event failed: {exc}"
            )

        return {
            "ok": True,
            "event": event,
            "payment_id": payment_id,
            "status": new_status,
        }

    # ---------------------------------------------------------
    # Unhandled event
    # ---------------------------------------------------------

    print(
        f"[WEBHOOK] Event received but not handled: {event}"
    )

    return {
        "ok": True,
        "event": event,
        "handled": False,
    }