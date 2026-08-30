from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class QuoteItemIn(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class CreateQuote(BaseModel):
    merchant_id: str
    created_by: Optional[str] = "agent"
    items: List[QuoteItemIn]


class Quote(BaseModel):
    quote_id: str
    status: str
    subtotal_cents: int
    discount_cents: int
    final_amount_cents: int
    created_at: Optional[datetime]


class ApproveRequest(BaseModel):
    approver_id: str
    approve: bool


class PaymentCreateRequest(BaseModel):
    quote_id: str
    idempotency_key: str