import os
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def list_products(merchant_id: str) -> List[Dict[str, Any]]:
    resp = supabase.table("products").select("*").eq("merchant_id", merchant_id).execute()
    return resp.data or []


def fetch_product(product_id: str) -> Optional[Dict[str, Any]]:
    resp = supabase.table("products").select("*").eq("product_id", product_id).limit(1).execute()
    return (resp.data or [None])[0]


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


def create_audit_event(event: Dict[str, Any]):
    supabase.table("audit_events").insert(event).execute()


def insert_policy_event(event: Dict[str, Any]):
    supabase.table("policy_events").insert(event).execute()


def create_llm_trace(trace: Dict[str, Any]):
    supabase.table("llm_traces").insert(trace).execute()


def create_payment(payment: Dict[str, Any]):
    resp = supabase.table("payments").insert(payment).execute()
    return (resp.data or [None])[0]


def update_payment(payment_id: str, updates: Dict[str, Any]):
    supabase.table("payments").update(updates).eq("payment_id", payment_id).execute()