from fastapi import APIRouter, Request, HTTPException, Header
from ..utils.razorpay_client import verify_webhook_signature
from .. import db

router = APIRouter()


@router.post("/razorpay")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    body = await request.body()
    if not verify_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    payload = await request.json()
    # persist raw webhook for traceability
    db.supabase.table("payments").insert({"razorpay_payload": payload}).execute()
    # handle event types minimally
    event = payload.get("event")
    if event == "payment.link.paid":
        data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        # find payment by payment_link id
        pl_id = data.get("payment_link_id")
        if pl_id:
            # update payments table
            db.supabase.table("payments").update({"status": "paid"}).eq("razorpay_payment_link_id", pl_id).execute()
    return {"ok": True}