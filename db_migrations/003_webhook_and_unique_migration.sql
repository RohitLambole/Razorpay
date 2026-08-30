-- Migration: create raw_webhooks table and add UNIQUE constraint for payments idempotency

BEGIN;

-- raw_webhooks table for storing incoming webhook payloads
CREATE TABLE IF NOT EXISTS raw_webhooks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source text NOT NULL,
  payload jsonb NOT NULL,
  received_at timestamptz DEFAULT now()
);

-- add unique constraint to payments to prevent duplicate idempotency inserts
ALTER TABLE payments
  ADD CONSTRAINT IF NOT EXISTS uq_payments_merchant_idempotency UNIQUE (merchant_id, idempotency_key);

COMMIT;
