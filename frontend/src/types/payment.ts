export type CreatePaymentRequest = {
  quote_id: string
  idempotency_key: string
}

export type CreatePaymentResponse = {
  payment_id: string
  status: string
  razorpay_payment_link_id?: string
  payment_link?: { id?: string, short_url?: string }
}
