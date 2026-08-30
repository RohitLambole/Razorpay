from fastapi import APIRouter, HTTPException
from ..schemas import CreateQuote, ApproveRequest
from .. import db, policy
from uuid import uuid4
from decimal import Decimal

router = APIRouter()


@router.post("/", status_code=201)
def create_quote(payload: CreateQuote):
    # very small pricing compute: fetch product unit_price -> subtotal
    items_payload = []
    subtotal = 0
    for it in payload.items:
        prod = db.fetch_product(it.product_id)
        if not prod:
            raise HTTPException(status_code=404, detail=f"product {it.product_id} not found")
        unit = prod.get("base_price_cents")
        line = unit * it.quantity
        items_payload.append({
            "quote_item_id": str(uuid4()),
            "product_id": it.product_id,
            "sku": prod.get("sku"),
            "quantity": it.quantity,
            "unit_price_cents": unit,
            "line_total_cents": line
        })
        subtotal += line

    # For demo, agent requests a discount% derived heuristically; here fixed placeholder 15%
    requested_discount_percent = float(15.0)

    policy_result = policy.evaluate_discount(subtotal, requested_discount_percent)
    db.insert_policy_event({
        "quote_id": None,
        "rule_name": "discount_cap",
        "result": policy_result["result"],
        "rationale": policy_result["rationale"],
    })

    if policy_result["result"] == "fail":
        raise HTTPException(status_code=403, detail="Requested discount exceeds allowed maximum")

    discount_cents = int(round(subtotal * (policy_result["effective_discount_percent"] / 100.0)))
    final_amount = subtotal - discount_cents

    quote_id = str(uuid4())
    quote_obj = {
        "quote_id": quote_id,
        "merchant_id": payload.merchant_id,
        "created_by": payload.created_by,
        "status": "pending_approval" if policy_result["result"] == "requires_approval" else "approved",
        "subtotal_cents": subtotal,
        "tax_cents": 0,
        "discount_cents": discount_cents,
        "final_amount_cents": final_amount,
    }
    persisted = db.persist_quote(quote_obj)
    # insert items linking to persisted quote
    for it in items_payload:
        it["quote_id"] = quote_id
    db.insert_quote_items(items_payload)
    db.create_audit_event({
        "merchant_id": payload.merchant_id,
        "session_id": None,
        "actor": "agent",
        "action": "create_quote",
        "payload": {"quote_id": quote_id, "policy": policy_result},
    })
    return {"quote_id": quote_id, "status": quote_obj["status"], "final_amount_cents": final_amount}


@router.post("/{quote_id}/approve")
def approve_quote(quote_id: str, req: ApproveRequest):
    # Minimal approve flow
    q = db.supabase.table("quotes").select("*").eq("quote_id", quote_id).limit(1).execute().data
    if not q:
        raise HTTPException(status_code=404, detail="quote not found")
    q = q[0]
    if q["status"] != "pending_approval":
        raise HTTPException(status_code=400, detail=f"quote not in pending_approval state: {q['status']}")
    new_status = "approved" if req.approve else "cancelled"
    db.update_quote(quote_id, {"status": new_status, "approved_by": req.approver_id})
    db.create_audit_event({
        "merchant_id": q["merchant_id"],
        "session_id": None,
        "actor": req.approver_id,
        "action": "approve_quote" if req.approve else "deny_quote",
        "payload": {"quote_id": quote_id}
    })
    return {"quote_id": quote_id, "status": new_status}