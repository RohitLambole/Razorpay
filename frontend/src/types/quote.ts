export type QuoteItem = {
  product_id: string
  quantity: number
}

export type CreateQuotePayload = {
  merchant_id: string
  created_by: string
  requested_discount_percent?: number
  items: QuoteItem[]
}

export type CreateQuoteResponse = {
  quote_id: string
  status: string
  final_amount_cents: number
}

export type ApproveRequest = {
  approver_id: string
  approve: boolean
}
