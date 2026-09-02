import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCatalog } from '../api/catalog'
import { useDemoAuth } from '../hooks/useDemoAuth'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import { generateIdempotencyKey } from '../utils/idempotency'
import { createPayment } from '../api/payments'

export default function Payments(){
  const { merchantId } = useDemoAuth()
  const { data: products } = useQuery(['catalog', merchantId], ()=>getCatalog(merchantId))
  const [quoteId, setQuoteId] = useState('')
  const [creating, setCreating] = useState(false)
  const [result, setResult] = useState<any>(null)

  async function handleCreate(){
    setCreating(true)
    try{
      const idempotency_key = generateIdempotencyKey(quoteId)
      const resp = await createPayment({quote_id: quoteId, idempotency_key})
      setResult(resp)
    }catch(e:any){
      setResult({error: e.message})
    }finally{setCreating(false)}
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Payments</h2>
      <div className="mt-4 grid grid-cols-1 gap-4 max-w-xl">
        <div>
          <label className="text-sm">Quote ID</label>
          <Input value={quoteId} onChange={(e)=>setQuoteId(e.target.value)} placeholder="Paste quote_id" />
        </div>
        <div>
          <Button onClick={handleCreate} disabled={!quoteId || creating}>{creating? 'Creating...':'Create Payment'}</Button>
        </div>
        {result && (
          <div className="mt-4 p-4 bg-white border rounded">
            <pre className="text-sm">{JSON.stringify(result, null, 2)}</pre>
            {/* if payment_link.short_url present show CTA */}
            {result?.payment_link?.short_url && (
              <div className="mt-3">
                <a className="px-4 py-2 bg-indigo-600 text-white rounded" href={result.payment_link.short_url} target="_blank" rel="noreferrer">Continue to payment</a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
