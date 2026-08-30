import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from main import app
from app.routers import payments as payments_router
from app import db

client = TestClient(app)


class FakeQuery:
    def __init__(self, table):
        self.table = table
        self._filters = {}

    def select(self, *args, **kwargs):
        return self

    def eq(self, k, v):
        self._filters[k] = v
        return self

    def limit(self, n):
        return self

    def execute(self):
        # return different fixtures based on table and filters
        if self.table == "quotes":
            if self._filters.get("quote_id") == "q1":
                return SimpleNamespace(data=[{"quote_id": "q1", "merchant_id": "m1", "final_amount_cents": 10000}])
            return SimpleNamespace(data=[])
        if self.table == "quote_items":
            return SimpleNamespace(data=[{"product_id": "p1", "quantity": 2}])
        if self.table == "payments":
            return SimpleNamespace(data=[])
        return SimpleNamespace(data=[])


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    # monkeypatch db.supabase.table to return FakeQuery
    class FakeSupabase:
        def table(self, name):
            return FakeQuery(name)

    monkeypatch.setattr(db, "supabase", FakeSupabase())


def test_create_payment_idempotent(monkeypatch):
    # Simulate no existing payment
    monkeypatch.setattr(db, "get_payment_by_idempotency", lambda merchant_id, key: None)

    # Simulate reserve_inventory_for_quote succeeds
    monkeypatch.setattr(db, "reserve_inventory_for_quote", lambda quote_id, items, ttl_minutes=15: [{"reservation_id": "r1"}])

    # Patch razorpay client
    monkeypatch.setattr(payments_router, "create_order_and_payment_link", lambda amount: {"order": {"id": "ord1"}, "payment_link": {"id": "pl1", "short_url": "https://rzp.link/pl1"}})

    # Patch db.create_payment and audit
    monkeypatch.setattr(db, "create_payment", lambda payment: payment)
    monkeypatch.setattr(db, "create_audit_event", lambda event: event)

    resp = client.post("/payments/create", json={"quote_id": "q1", "idempotency_key": "key-123"})
    assert resp.status_code == 201
    body = resp.json()
    assert "payment_id" in body
    assert "payment_link" in body


def test_create_payment_existing_idempotency(monkeypatch):
    # Simulate existing payment returned
    monkeypatch.setattr(db, "get_payment_by_idempotency", lambda merchant_id, key: {"payment_id": "p-existing", "status": "created", "razorpay_payment_link_id": "pl1"})

    # Ensure reserve_inventory_for_quote is not called (we don't patch it so if called it would error)

    resp = client.post("/payments/create", json={"quote_id": "q1", "idempotency_key": "key-exists"})
    assert resp.status_code == 200 or resp.status_code == 201
    body = resp.json()
    # it should return existing payment details
    assert body.get("payment_id") == "p-existing"
