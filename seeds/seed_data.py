"""Seed sample data into Supabase for local testing.
Usage: python seeds/seed_data.py
Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in your environment.
"""
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
import os
import uuid

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in env")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

MERCHANT_ID = str(uuid.uuid4())

merchant = {
    "merchant_id": MERCHANT_ID,
    "name": "Demo Merchant",
    "admin_email": "admin@example.com",
}

print("Seeding merchant...", MERCHANT_ID)
sb.table("merchants").insert(merchant).execute()

products = []
for i in range(1, 11):
    pid = str(uuid.uuid4())
    prod = {
        "product_id": pid,
        "merchant_id": MERCHANT_ID,
        "sku": f"SKU-{1000 + i}",
        "name": f"Demo Product {i}",
        "description": f"This is demo product {i}",
        "base_price_cents": 1000 * i,
        "inventory_count": 100,
        "metadata": {"category": "demo"}
    }
    products.append(prod)

print("Seeding products...")
sb.table("products").insert(products).execute()

# sample tier for first product
if products:
    tier = {
        "product_id": products[0]["product_id"],
        "min_quantity": 50,
        "price_cents": products[0]["base_price_cents"] - 100,
    }
    try:
        sb.table("product_tiers").insert(tier).execute()
        print("Inserted a sample tier for product", products[0]["product_id"])
    except Exception:
        pass

print("Seeding complete.")
