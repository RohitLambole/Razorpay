import { apiGet } from './client'
import type { Product } from '../types/product'

export async function getCatalog(merchantId: string): Promise<Product[]>{
  const q = `?merchant_id=${merchantId}`
  const data = await apiGet(`/catalog/${q}`)
  return data
}
