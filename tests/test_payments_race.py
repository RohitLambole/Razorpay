import json
import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.main import app
from app import db
from app.routers import payments as payments_router

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
        # provide a fake quote when selecting from quotes
        if self.table == "quotes":
            return SimpleNamespace(data=[{"quote_id": "q1", "merchant_id": "m1", "final_amount_cents": 10000}])
        if self.table == "quote_items":
            return SimpleNamespace(data=[{"product_id": "p1", "quantity": 2}])
        return SimpleNamespace(data=[])


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    # monkeypatch db.supabase.table to return FakeQuery
    class FakeSupabase:
        def table(self, name):
            return FakeQuery(name)

    monkeypatch.setattr(db, "supabase", FakeSupabase())


def test_race_returns_existing_payment(monkeypatch):
    # Simulate initial idempotency lookup returns None, second lookup returns existing winner
    call_state = {"get_calls": 0}

    def get_payment_by_idempotency(merchant_id, key):
        if call_state["get_calls"] == 0:
            call_state["get_calls"] += 1
            return None
        return {"payment_id": "p-winner", "status": "created", "razorpay_payment_link_id": "pl-winner"}

    monkeypatch.setattr(db, "get_payment_by_idempotency", get_payment_by_idempotency)

    # Reserve inventory: no-op
    monkeypatch.setattr(db, "reserve_inventory_for_quote", lambda quote_id, items, ttl_minutes=15: [{"reservation_id": "r1"}])

    # Razorpay call returns normally
    monkeypatch.setattr(payments_router, "create_order_and_payment_link", lambda amount: {"order": {"id": "ord1"}, "payment_link": {"id": "pl1", "short_url": "https://rzp.link/pl1"}})

    # Simulate db.create_payment raising a unique-constraint exception (Postgres SQLSTATE 23505)
    class FakeUniqueViolation(Exception):
        pass

    fake_exc = FakeUniqueViolation('duplicate key value violates unique constraint "uq_payments_merchant_idempotency"')
    # attach attributes that robust detection logic may look for
    setattr(fake_exc, "code", "23505")
    setattr(fake_exc, "constraint", "uq_payments_merchant_idempotency")

    def raise_unique(payment):
        raise fake_exc

    monkeypatch.setattr(db, "create_payment", raise_unique)

    # Spy on audit events so losing request does not create one
    audit = {"count": 0}
    monkeypatch.setattr(db, "create_audit_event", lambda e: audit.__setitem__("count", audit["count"] + 1))

    resp = client.post("/payments/create", json={"quote_id": "q1", "idempotency_key": "idem-123"})
    # Implementation should recover and return existing payment
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body.get("payment_id") == "p-winner"
    assert audit["count"] == 0


def test_unrelated_db_error_is_not_treated_as_idempotency_conflict(monkeypatch):
    # get_payment_by_idempotency returns None initially
    get_calls = {"count": 0}

    def get_payment_by_idempotency(merchant_id, key):
        get_calls["count"] += 1
        return None

    monkeypatch.setattr(db, "get_payment_by_idempotency", get_payment_by_idempotency)

    # Reserve inventory: no-op
    monkeypatch.setattr(db, "reserve_inventory_for_quote", lambda quote_id, items, ttl_minutes=15: [{"reservation_id": "r1"}])

    # Razorpay call returns normally
    monkeypatch.setattr(payments_router, "create_order_and_payment_link", lambda amount: {"order": {"id": "ord1"}, "payment_link": {"id": "pl1", "short_url": "https://rzp.link/pl1"}})

    # Simulate an unrelated DB exception
    def raise_unrelated(payment):
        raise Exception("could not connect to database: connection reset")

    monkeypatch.setattr(db, "create_payment", raise_unrelated)

    # Spy on audit events
    audit = {"count": 0}
    monkeypatch.setattr(db, "create_audit_event", lambda e: audit.__setitem__("count", audit["count"] + 1))

    resp = client.post("/payments/create", json={"quote_id": "q1", "idempotency_key": "idem-999"})
    assert resp.status_code == 500
    # get_payment_by_idempotency should have been called only once (the initial check), not for recovery
    assert get_calls["count"] == 1
    assert audit["count"] == 0
