import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from main import app
from app import db

client = TestClient(app)


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    # stub out DB persistence operations except fetch_product (we override per test)
    monkeypatch.setattr(db, "insert_quote_items", lambda items: None)
    monkeypatch.setattr(db, "create_audit_event", lambda e: None)
    monkeypatch.setattr(db, "insert_policy_event", lambda e: None)
    # We'll monkeypatch fetch_product and persist_quote inside tests as needed.


def test_create_quote_approved_records_requested_discount(monkeypatch):
    # Arrange: product price 1000
    monkeypatch.setattr(db, "fetch_product", lambda pid: {"product_id": "p10", "sku": "SKU-10", "base_price_cents": 1000, "inventory_count": 10})

    persisted = {}

    def fake_persist_quote(payload):
        persisted.update(payload)
        return payload

    monkeypatch.setattr(db, "persist_quote", fake_persist_quote)

    payload = {
        "merchant_id": "m1",
        "created_by": "agent",
        "requested_discount_percent": 10.0,
        "items": [{"product_id": "p10", "quantity": 1}]
    }

    resp = client.post("/quotes/", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "approved"
    # subtotal 1000 -> discount 10% -> 100 -> final 900
    assert body["final_amount_cents"] == 900
    assert persisted.get("requested_discount_percent") == 10.0


def test_create_quote_pending_approval_records_requested_discount(monkeypatch):
    monkeypatch.setattr(db, "fetch_product", lambda pid: {"product_id": "p30", "sku": "SKU-30", "base_price_cents": 2000, "inventory_count": 10})

    persisted = {}
    monkeypatch.setattr(db, "persist_quote", lambda payload: persisted.update(payload) or payload)

    payload = {
        "merchant_id": "m1",
        "created_by": "agent",
        "requested_discount_percent": 30.0,
        "items": [{"product_id": "p30", "quantity": 2}]
    }

    resp = client.post("/quotes/", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending_approval"
    # subtotal 4000, discount 30% -> 1200 -> final 2800
    assert body["final_amount_cents"] == 2800
    assert persisted.get("requested_discount_percent") == 30.0


def test_create_quote_rejected_for_50_percent(monkeypatch):
    monkeypatch.setattr(db, "fetch_product", lambda pid: {"product_id": "p50", "sku": "SKU-50", "base_price_cents": 500, "inventory_count": 10})

    pers_calls = {"count": 0}
    monkeypatch.setattr(db, "persist_quote", lambda payload: pers_calls.__setitem__("count", pers_calls["count"] + 1))

    payload = {
        "merchant_id": "m1",
        "created_by": "agent",
        "requested_discount_percent": 50.0,
        "items": [{"product_id": "p50", "quantity": 4}]
    }

    resp = client.post("/quotes/", json=payload)
    assert resp.status_code == 403
    assert pers_calls["count"] == 0


def test_negative_requested_discount_is_invalid(monkeypatch):
    # Negative discount should be rejected by pydantic validation -> 422
    monkeypatch.setattr(db, "fetch_product", lambda pid: {"product_id": "pneg", "sku": "SKU-N", "base_price_cents": 1000, "inventory_count": 10})

    payload = {
        "merchant_id": "m1",
        "created_by": "agent",
        "requested_discount_percent": -5.0,
        "items": [{"product_id": "pneg", "quantity": 1}]
    }

    resp = client.post("/quotes/", json=payload)
    assert resp.status_code == 422
