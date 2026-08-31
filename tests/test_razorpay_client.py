from types import SimpleNamespace
import pytest
from app.utils import razorpay_client
import builtins

def test_create_order_and_payment_link_payload(monkeypatch):
    # Arrange: fake order.create and payment_link.create
    fake_order = {"id": "ord_test_123", "amount": 1000}
    def fake_order_create(data):
        assert data["amount"] == 1000
        return fake_order

    captured = {}
    def fake_payment_link_create(payload):
        # capture payload for assertions
        captured.update(payload)
        # return a fake payment_link object
        return {"id": "pl_test_123", "short_url": "https://rzp.link/pl_test_123", "payload_received": payload}

    # monkeypatch the razorpay client methods
    monkeypatch.setattr(razorpay_client._client.order, "create", fake_order_create)
    monkeypatch.setattr(razorpay_client._client.payment_link, "create", fake_payment_link_create)

    # Act
    result = razorpay_client.create_order_and_payment_link(1000, currency="INR", idempotency_key="idem-1")

    # Assert returned structure
    assert "order" in result and result["order"]["id"] == "ord_test_123"
    assert "payment_link" in result and result["payment_link"]["id"] == "pl_test_123"

    # Assert payload fields sent to payment_link.create are supported
    assert captured.get("amount") == 1000
    assert captured.get("currency") == "INR"
    assert captured.get("reference_id") == "ord_test_123"
    # Should not be using unsupported field 'notifications'
    assert "notifications" not in captured
    # The correct field name is 'notify'
    assert "notify" in captured
    # Also ensure we are not sending 'order_id'
    assert "order_id" not in captured