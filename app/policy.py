from typing import Dict, Any

# Simple policy engine: discount cap 20% auto, >20 and <=40 requires approval, >40 reject.
DISCOUNT_AUTO_PASS_PERCENT = 20.0
DISCOUNT_MAX_ALLOW_PERCENT = 40.0


def evaluate_discount(subtotal_cents: int, requested_discount_percent: float) -> Dict[str, Any]:
    """
    Returns:
      {
        "result": "pass" | "requires_approval" | "fail",
        "effective_discount_percent": float,
        "rationale": {...}
      }
    """
    rationale = {"subtotal_cents": subtotal_cents, "requested_discount_percent": requested_discount_percent}
    if requested_discount_percent <= DISCOUNT_AUTO_PASS_PERCENT:
        return {"result": "pass", "effective_discount_percent": requested_discount_percent, "rationale": rationale}
    if requested_discount_percent <= DISCOUNT_MAX_ALLOW_PERCENT:
        return {"result": "requires_approval", "effective_discount_percent": requested_discount_percent, "rationale": rationale}
    return {"result": "fail", "effective_discount_percent": DISCOUNT_MAX_ALLOW_PERCENT, "rationale": rationale}