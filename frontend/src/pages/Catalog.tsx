import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCatalog } from '../api/catalog'
import { useDemoAuth } from '../hooks/useDemoAuth'

export default function Catalog(){
  const { merchantId } = useDemoAuth()
  const { data, isLoading, error } = useQuery(['catalog', merchantId], ()=>getCatalog(merchantId))

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold">Catalog</h2>
      {isLoading && <div className="mt-4">Loading...</div>}
      {error && <div className="mt-4 text-red-600">Failed to load catalog</div>}
      <div className="mt-4 grid grid-cols-3 gap-4">
        {data && data.map((p:any)=> (
          <div key={p.product_id} className="border rounded p-4 bg-white">
            <h3 className="font-medium">{p.name || p.product_id}</h3>
            <div className="text-sm text-gray-600">SKU: {p.sku}</div>
            <div className="mt-2 font-semibold">₹{(p.base_price_cents/100).toFixed(2)}</div>
            <div className="mt-3"><button className="px-3 py-1 bg-indigo-600 text-white rounded">Add</button></div>
          </div>
        ))}
      </div>
    </div>
  )
}
