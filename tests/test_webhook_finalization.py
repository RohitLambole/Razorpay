import os
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.main import app
from app import db

client = TestClient(app)


def sign_body(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class DummyPayment:
    def __init__(self, payment_id, merchant_id, quote_id):
        self.payment_id = payment_id
        self.merchant_id = merchant_id
        self.quote_id = quote_id


class DummySupabase:
    def table(self, name):
        return SimpleNamespace(insert=lambda payload: SimpleNamespace(execute=lambda: None), delete=lambda *args, **kwargs: SimpleNamespace(execute=lambda: None))


def test_webhook_paid_finalizes_reservations(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)

    # fake payment row lookup
    payment_row = {"payment_id": "p1", "merchant_id": "m1", "quote_id": "q1"}
    monkeypatch.setattr(db, "get_payment_by_link", lambda pl: payment_row)

    called = {"update_payment": False, "finalize": False, "update_quote": False, "audit": False, "policy": False}

    monkeypatch.setattr(db, "update_payment", lambda pid, updates: called.update({"update_payment": True}))
    monkeypatch.setattr(db, "finalize_reservations", lambda qid: called.update({"finalize": True}))
    monkeypatch.setattr(db, "update_quote", lambda qid, u: called.update({"update_quote": True}))
    monkeypatch.setattr(db, "create_audit_event", lambda e: called.update({"audit": True}))
    monkeypatch.setattr(db, "insert_policy_event", lambda e: called.update({"policy": True}))

    payload = {"event": "payment.link.paid", "payload": {"payment": {"entity": {"payment_link_id": "pl1"}}}}
    body = json.dumps(payload).encode()
    sig = sign_body(secret, body)

    headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    resp = client.post("/webhooks/razorpay", data=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
    assert called["update_payment"] is True
    assert called["finalize"] is True
    assert called["update_quote"] is True
    assert called["audit"] is True
    assert called["policy"] is True


def test_webhook_expired_releases_reservations(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)

    payment_row = {"payment_id": "p2", "merchant_id": "m1", "quote_id": "q2"}
    monkeypatch.setattr(db, "get_payment_by_link", lambda pl: payment_row)

    called = {"update_payment": False, "release": False, "update_quote": False, "audit": False}
    monkeypatch.setattr(db, "update_payment", lambda pid, updates: called.update({"update_payment": True}))
    monkeypatch.setattr(db, "release_reservations_by_quote", lambda qid: called.update({"release": True}))
    monkeypatch.setattr(db, "update_quote", lambda qid, u: called.update({"update_quote": True}))
    monkeypatch.setattr(db, "create_audit_event", lambda e: called.update({"audit": True}))

    payload = {"event": "payment.link.expired", "payload": {"payment": {"entity": {"payment_link_id": "pl-exp"}}}}
    body = json.dumps(payload).encode()
    sig = sign_body(secret, body)

    headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    resp = client.post("/webhooks/razorpay", data=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
    assert called["update_payment"] is True
    assert called["release"] is True
    assert called["update_quote"] is True
    assert called["audit"] is True
