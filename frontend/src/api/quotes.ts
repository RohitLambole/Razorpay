import { apiPost } from './client'
import type { CreateQuotePayload, CreateQuoteResponse, ApproveRequest } from '../types/quote'

export async function createQuote(payload: CreateQuotePayload): Promise<CreateQuoteResponse>{
  return apiPost('/quotes/', payload)
}

export async function approveQuote(quoteId: string, req: ApproveRequest){
  return apiPost(`/quotes/${quoteId}/approve`, req)
}
