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


# LLM Action schemas
class ActionParamsComputeQuote(BaseModel):
    merchant_id: str
    items: List[dict]


class ActionParamsAskApproval(BaseModel):
    quote_id: str
    reason: str


class ActionParamsCreateOrder(BaseModel):
    quote_id: str
    idempotency_key: str


class LLMAction(BaseModel):
    action: str
    params: dict
    explain: Optional[str]


# Specific typed action unions (optional helpers)
class ComputeQuoteAction(LLMAction):
    action: str = "compute_quote"
    params: ActionParamsComputeQuote


class AskApprovalAction(LLMAction):
    action: str = "ask_approval"
    params: ActionParamsAskApproval


class CreateOrderAction(LLMAction):
    action: str = "create_order"
    params: ActionParamsCreateOrder
