-- Migration: add inventory_reservations table and payments.idempotency_key

BEGIN;

-- create reservations table
CREATE TABLE IF NOT EXISTS inventory_reservations (
  reservation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id uuid REFERENCES products(product_id) ON DELETE CASCADE,
  quantity integer NOT NULL,
  quote_id uuid,
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- add idempotency_key column to payments if not exists
ALTER TABLE payments
  ADD COLUMN IF NOT EXISTS idempotency_key text;

-- add index for idempotency
CREATE INDEX IF NOT EXISTS idx_payments_idempotency ON payments (merchant_id, idempotency_key);

COMMIT;
