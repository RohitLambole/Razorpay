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


class FakeQuery:
    def __init__(self, table):
        self.table = table
        self._filters = {}

    def insert(self, payload):
        # pretend to insert
        return self

    def update(self, payload):
        return self

    def eq(self, k, v):
        self._filters[k] = v
        return self

    def execute(self):
        return SimpleNamespace(data=[{}])


def test_verify_webhook_signature_and_route(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)

    # patch db.supabase.table used in webhook handler
    class FakeSupabase:
        def table(self, name):
            return FakeQuery(name)

    monkeypatch.setattr(db, "supabase", FakeSupabase())

    payload = {"event": "payment.link.paid", "payload": {"payment": {"entity": {"payment_link_id": "pl1"}}}}
    body = json.dumps(payload).encode()
    sig = sign_body(secret, body)

    headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    resp = client.post("/webhooks/razorpay", data=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
