import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- product helpers ---
def list_products(merchant_id: str) -> List[Dict[str, Any]]:
    resp = supabase.table("products").select("*").eq("merchant_id", merchant_id).execute()
    return resp.data or []


def fetch_product(product_id: str) -> Optional[Dict[str, Any]]:
    resp = supabase.table("products").select("*").eq("product_id", product_id).limit(1).execute()
    return (resp.data or [None])[0]


# --- quote persistence ---
def persist_quote(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = supabase.table("quotes").insert(payload).execute()
    return (resp.data or [None])[0]


def update_quote(quote_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    resp = supabase.table("quotes").update(updates).eq("quote_id", quote_id).execute()
    return (resp.data or [None])[0]


def insert_quote_items(items: List[Dict[str, Any]]):
    if not items:
        return
    supabase.table("quote_items").insert(items).execute()


# --- payments ---
def create_payment(payment: Dict[str, Any]):
    resp = supabase.table("payments").insert(payment).execute()
    return (resp.data or [None])[0]


def update_payment(payment_id: str, updates: Dict[str, Any]):
    supabase.table("payments").update(updates).eq("payment_id", payment_id).execute()


def get_payment_by_idempotency(merchant_id: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
    resp = supabase.table("payments").select("*").eq("merchant_id", merchant_id).eq("idempotency_key", idempotency_key).limit(1).execute()
    return (resp.data or [None])[0]


def get_payment_by_link(payment_link_id: str) -> Optional[Dict[str, Any]]:
    resp = supabase.table("payments").select("*").eq("razorpay_payment_link_id", payment_link_id).limit(1).execute()
    return (resp.data or [None])[0]


# --- audit, policy, llm traces ---
def create_audit_event(event: Dict[str, Any]):
    supabase.table("audit_events").insert(event).execute()


def insert_policy_event(event: Dict[str, Any]):
    supabase.table("policy_events").insert(event).execute()


def create_llm_trace(trace: Dict[str, Any]):
    supabase.table("llm_traces").insert(trace).execute()


# --- inventory reservations ---
def reserve_inventory_for_quote(quote_id: str, items: List[Dict[str, Any]], ttl_minutes: int = 15) -> List[Dict[str, Any]]:
    """Try to reserve inventory for each item. Returns list of reservation rows inserted.
    items: [{product_id, quantity}]
    """
    now = datetime.utcnow()
    expires_at = (now + timedelta(minutes=ttl_minutes)).isoformat()
    reservations_created = []

    # naive per-item check
    for it in items:
        pid = it["product_id"]
        qty = int(it["quantity"])
        prod = fetch_product(pid)
        if not prod:
            raise ValueError(f"product {pid} not found")
        inventory = int(prod.get("inventory_count") or 0)

        # sum active reservations for this product
        resp = supabase.table("inventory_reservations").select("*").eq("product_id", pid).execute()
        active = []
        for r in (resp.data or []):
            # simple isoformat comparison; assume stored string is ISO
            try:
                expires = datetime.fromisoformat(r.get("expires_at"))
            except Exception:
                # if format unknown, treat as active
                expires = now
            if expires > now:
                active.append(r)
        reserved_qty = sum([int(r.get("quantity")) for r in active])
        available = inventory - reserved_qty
        if available < qty:
            # rollback previously created reservations for this quote
            for rc in reservations_created:
                supabase.table("inventory_reservations").delete().eq("reservation_id", rc["reservation_id"]).execute()
            raise ValueError(f"insufficient inventory for product {pid}: available {available}, requested {qty}")

        res = {
            "reservation_id": str(uuid4()),
            "product_id": pid,
            "quantity": qty,
            "quote_id": quote_id,
            "expires_at": expires_at,
            "created_at": now.isoformat()
        }
        supabase.table("inventory_reservations").insert(res).execute()
        reservations_created.append(res)

    return reservations_created


def release_reservations_by_quote(quote_id: str):
    supabase.table("inventory_reservations").delete().eq("quote_id", quote_id).execute()


def finalize_reservations(quote_id: str):
    """Consume reservations: decrement product inventory_count and remove reservations"""
    resp = supabase.table("inventory_reservations").select("*").eq("quote_id", quote_id).execute()
    rows = resp.data or []
    for r in rows:
        pid = r.get("product_id")
        qty = int(r.get("quantity") or 0)
        # fetch current product
        prod = fetch_product(pid)
        if not prod:
            continue
        current = int(prod.get("inventory_count") or 0)
        new = max(0, current - qty)
        supabase.table("products").update({"inventory_count": new}).eq("product_id", pid).execute()
    # delete reservations
    supabase.table("inventory_reservations").delete().eq("quote_id", quote_id).execute()
