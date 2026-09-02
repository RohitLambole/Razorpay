import React, {useState} from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { getCatalog } from '../api/catalog'
import { useDemoAuth } from '../hooks/useDemoAuth'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import { createQuote } from '../api/quotes'
import { formatINR } from '../utils/currency'

export default function QuoteCreate(){
  const { merchantId, userName } = useDemoAuth()
  const qc = useQueryClient()
  const { data: products } = useQuery(['catalog', merchantId], ()=>getCatalog(merchantId))

  // prefill from agent
  const prefill = typeof window !== 'undefined' ? localStorage.getItem('agent_prefill') : null
  const parsed = prefill ? JSON.parse(prefill) : null

  const [items, setItems] = useState<any[]>( parsed ? [{product_id: parsed.product_id, quantity: parsed.qty}] : [])
  const [discount, setDiscount] = useState<number>(0)
  const [creating, setCreating] = useState(false)
  const [created, setCreated] = useState<any>(null)

  function addItem(pid:string){
    setItems(prev=>[...prev, {product_id: pid, quantity:1}])
  }

  function updateQty(idx:number, q:number){
    setItems(prev=> prev.map((it,i)=> i===idx? {...it, quantity:q}: it))
  }

  async function submit(){
    setCreating(true)
    try{
      const payload = {
        merchant_id: merchantId,
        created_by: userName || 'demo-agent',
        requested_discount_percent: discount,
        items
      }
      const resp = await createQuote(payload)
      // store locally for detail viewing because no list endpoint
      const store = JSON.parse(localStorage.getItem('created_quotes')||'[]')
      store.unshift({...resp, payload})
      localStorage.setItem('created_quotes', JSON.stringify(store))
      setCreated(resp)
      // clear agent prefill
      localStorage.removeItem('agent_prefill')
    }catch(e:any){
      alert('Failed: '+e.message)
    }finally{setCreating(false)}
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Create Quote</h2>
      <div className="mt-4 grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <div className="bg-white p-4 border rounded">
            <h3 className="font-medium">Items</h3>
            <div className="mt-3 space-y-2">
              {items.map((it, idx)=> (
                <div key={idx} className="flex items-center gap-3">
                  <select value={it.product_id} onChange={(e)=>{
                    const newId = e.target.value
                    setItems(prev=> prev.map((p,i)=> i===idx? {...p, product_id:newId}: p))
                  }} className="border rounded px-2 py-1">
                    {products?.map((p:any)=>(<option key={p.product_id} value={p.product_id}>{p.name || p.product_id}</option>))}
                  </select>
                  <Input type="number" value={it.quantity} onChange={(e)=>updateQty(idx, Number(e.target.value))} style={{width:80}} />
                </div>
              ))}
              <div className="mt-2">
                <select onChange={(e)=> addItem(e.target.value)} className="border rounded px-2 py-1">
                  <option value="">Add product...</option>
                  {products?.map((p:any)=>(<option key={p.product_id} value={p.product_id}>{p.name || p.product_id}</option>))}
                </select>
              </div>
            </div>
          </div>

          <div className="mt-4 bg-white p-4 border rounded">
            <h3 className="font-medium">Requested Discount</h3>
            <div className="mt-2 flex items-center gap-4">
              <input type="range" min={0} max={50} value={discount} onChange={(e)=>setDiscount(Number(e.target.value))} />
              <div className="font-medium">{discount}%</div>
            </div>
            <div className="mt-2 text-sm text-gray-600">Policy: ≤20% auto-approve, &lt;=40% requires approval, &gt;40% rejected by policy.</div>
          </div>

          <div className="mt-4">
            <Button onClick={submit} disabled={creating || items.length===0}>{creating? 'Creating...':'Create Quote'}</Button>
          </div>

          {created && (
            <div className="mt-4 p-4 bg-white border rounded">
              <div>Quote created: <strong>{created.quote_id}</strong></div>
              <div>Status: {created.status}</div>
              <div>Final: {formatINR(created.final_amount_cents)}</div>
              <div className="mt-2"><a className="text-indigo-600" href={`/app/quotes/${created.quote_id}`}>View quote</a></div>
            </div>
          )}
        </div>

        <div>
          <div className="bg-white p-4 border rounded">
            <h4 className="font-medium">Summary</h4>
            <div className="mt-3 text-sm text-gray-600">Quick price preview based on selected items.</div>
            <div className="mt-3">
              {items.map((it, i)=>{
                const p = products?.find((x:any)=>x.product_id===it.product_id)
                const price = p? p.base_price_cents: 0
                const subtotal = price * it.quantity
                return <div key={i} className="flex justify-between text-sm"><div>{p?.name||it.product_id} x {it.quantity}</div><div>{formatINR(subtotal)}</div></div>
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
