import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- Product helpers ---

def list_products(merchant_id: str) -> List[Dict[str, Any]]:
    resp = (
        supabase
        .table("products")
        .select("*")
        .eq("merchant_id", merchant_id)
        .execute()
    )
    return resp.data or []


def fetch_product(product_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        supabase
        .table("products")
        .select("*")
        .eq("product_id", product_id)
        .limit(1)
        .execute()
    )
    return (resp.data or [None])[0]


# --- Quote persistence ---

def persist_quote(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = supabase.table("quotes").insert(payload).execute()
    return (resp.data or [None])[0]


def update_quote(
    quote_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    resp = (
        supabase
        .table("quotes")
        .update(updates)
        .eq("quote_id", quote_id)
        .execute()
    )
    return (resp.data or [None])[0]


def insert_quote_items(items: List[Dict[str, Any]]):
    if not items:
        return

    supabase.table("quote_items").insert(items).execute()


# --- Payments ---

def create_payment(payment: Dict[str, Any]):
    resp = supabase.table("payments").insert(payment).execute()
    return (resp.data or [None])[0]


def update_payment(
    payment_id: str,
    updates: Dict[str, Any]
):
    (
        supabase
        .table("payments")
        .update(updates)
        .eq("payment_id", payment_id)
        .execute()
    )


def get_payment_by_idempotency(
    merchant_id: str,
    idempotency_key: str
) -> Optional[Dict[str, Any]]:
    resp = (
        supabase
        .table("payments")
        .select("*")
        .eq("merchant_id", merchant_id)
        .eq("idempotency_key", idempotency_key)
        .limit(1)
        .execute()
    )
    return (resp.data or [None])[0]


def get_payment_by_link(
    payment_link_id: str
) -> Optional[Dict[str, Any]]:
    resp = (
        supabase
        .table("payments")
        .select("*")
        .eq("razorpay_payment_link_id", payment_link_id)
        .limit(1)
        .execute()
    )
    return (resp.data or [None])[0]


# --- Audit, policy, LLM traces ---

def create_audit_event(event: Dict[str, Any]):
    supabase.table("audit_events").insert(event).execute()


def insert_policy_event(event: Dict[str, Any]):
    supabase.table("policy_events").insert(event).execute()


def create_llm_trace(trace: Dict[str, Any]):
    supabase.table("llm_traces").insert(trace).execute()


# --- Inventory reservations ---

def reserve_inventory_for_quote(
    quote_id: str,
    items: List[Dict[str, Any]],
    ttl_minutes: int = 15
) -> List[Dict[str, Any]]:
    """
    Try to reserve inventory for each item.

    items format:
        [
            {
                "product_id": "...",
                "quantity": 2
            }
        ]

    Returns:
        List of reservation rows created.
    """

    now = datetime.utcnow()
    expires_at = (
        now + timedelta(minutes=ttl_minutes)
    ).isoformat()

    reservations_created = []

    # Check and reserve each item
    for item in items:
        product_id = item["product_id"]
        quantity = int(item["quantity"])

        # Fetch product
        product = fetch_product(product_id)

        if not product:
            raise ValueError(
                f"product {product_id} not found"
            )

        inventory = int(
            product.get("inventory_count") or 0
        )

        # Get existing reservations
        resp = (
            supabase
            .table("inventory_reservations")
            .select("*")
            .eq("product_id", product_id)
            .execute()
        )

        active_reservations = []

        for reservation in resp.data or []:
            try:
                expires = datetime.fromisoformat(
                    reservation.get("expires_at")
                )
            except Exception:
                # If expiration format is invalid,
                # treat it as active for safety.
                expires = now

            if expires > now:
                active_reservations.append(reservation)

        reserved_quantity = sum(
            int(reservation.get("quantity") or 0)
            for reservation in active_reservations
        )

        available = inventory - reserved_quantity

        # Not enough inventory
        if available < quantity:

            # Roll back reservations created
            # earlier in this operation.
            for created in reservations_created:
                (
                    supabase
                    .table("inventory_reservations")
                    .delete()
                    .eq(
                        "reservation_id",
                        created["reservation_id"]
                    )
                    .execute()
                )

            raise ValueError(
                f"insufficient inventory for product "
                f"{product_id}: available {available}, "
                f"requested {quantity}"
            )

        # Create reservation
        reservation = {
            "reservation_id": str(uuid4()),
            "product_id": product_id,
            "quantity": quantity,
            "quote_id": quote_id,
            "expires_at": expires_at,
            "created_at": now.isoformat(),
        }

        (
            supabase
            .table("inventory_reservations")
            .insert(reservation)
            .execute()
        )

        reservations_created.append(reservation)

    return reservations_created


def release_reservations_by_quote(quote_id: str):
    (
        supabase
        .table("inventory_reservations")
        .delete()
        .eq("quote_id", quote_id)
        .execute()
    )


def finalize_reservations(quote_id: str):
    """
    Consume reservations:
    - decrement product inventory_count
    - remove reservations
    """

    resp = (
        supabase
        .table("inventory_reservations")
        .select("*")
        .eq("quote_id", quote_id)
        .execute()
    )

    rows = resp.data or []

    for reservation in rows:
        product_id = reservation.get("product_id")
        quantity = int(
            reservation.get("quantity") or 0
        )

        # Fetch current product
        product = fetch_product(product_id)

        if not product:
            continue

        current_inventory = int(
            product.get("inventory_count") or 0
        )

        new_inventory = max(
            0,
            current_inventory - quantity
        )

        (
            supabase
            .table("products")
            .update({
                "inventory_count": new_inventory
            })
            .eq("product_id", product_id)
            .execute()
        )

    # Delete reservations after finalizing
    (
        supabase
        .table("inventory_reservations")
        .delete()
        .eq("quote_id", quote_id)
        .execute()
    )