import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCatalog } from '../api/catalog'
import { useDemoAuth } from '../hooks/useDemoAuth'
import Button from '../components/ui/Button'

export default function Agent(){
  const { merchantId } = useDemoAuth()
  const { data: products } = useQuery(['catalog', merchantId], ()=>getCatalog(merchantId))

  return (
    <div>
      <h2 className="text-xl font-semibold">Agent Workspace (Demo)</h2>
      <p className="mt-2 text-sm text-gray-600">Use the guided agent to discover products and create quotes. OpenAI is server-side; this is a demo/guided UX that uses real catalog and quote APIs.</p>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white p-4 border rounded">
          <h3 className="font-semibold">Instruction (example)</h3>
          <div className="mt-2 text-sm text-gray-700">Try: "Find 5 units of Demo Product 3 and request best discount"</div>
          {/* Guided UI: pick product */}
          <div className="mt-4">
            <h4 className="font-medium">Catalog preview</h4>
            <div className="mt-3 space-y-2">
              {products?.slice(0,5).map((p:any)=> (
                <div key={p.product_id} className="p-3 border rounded flex justify-between items-center">
                  <div>
                    <div className="font-medium">{p.name || p.product_id}</div>
                    <div className="text-sm text-gray-500">₹{(p.base_price_cents/100).toFixed(2)}</div>
                  </div>
                  <div>
                    <Button onClick={()=>{
                      // navigate to quote create with product prefilled via localStorage
                      localStorage.setItem('agent_prefill', JSON.stringify({product_id: p.product_id, qty: 1}))
                      window.location.href = '/app/quote/create'
                    }}>Use</Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="bg-white p-4 border rounded">
          <h4 className="font-medium">Actions</h4>
          <div className="mt-3">
            <div className="text-sm text-gray-500">This demo agent suggests products and drives you to create a real quote.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
