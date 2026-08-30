import pytest
from app import policy


def test_evaluate_discount_auto_pass():
    r = policy.evaluate_discount(100000, 20.0)
    assert r["result"] == "pass"


def test_evaluate_discount_requires_approval():
    r = policy.evaluate_discount(100000, 30.0)
    assert r["result"] == "requires_approval"


def test_evaluate_discount_fail():
    r = policy.evaluate_discount(100000, 50.0)
    assert r["result"] == "fail"
