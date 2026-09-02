import { apiPost } from './client'
import type { CreatePaymentRequest, CreatePaymentResponse } from '../types/payment'

export async function createPayment(req: CreatePaymentRequest): Promise<CreatePaymentResponse>{
  return apiPost('/payments/create', req)
}
