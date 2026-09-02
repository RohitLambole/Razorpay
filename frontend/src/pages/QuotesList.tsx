import React from 'react'

export default function QuotesList(){
  const stored = JSON.parse(localStorage.getItem('created_quotes')||'[]')
  return (
    <div>
      <h2 className="text-xl font-semibold">Quotes (local)</h2>
      <p className="text-sm text-gray-600">This page shows quotes you created in this browser session. The backend currently does not expose a quote-listing endpoint; to list quotes across users, a backend GET /quotes?merchant_id=... endpoint would be required.</p>
      <div className="mt-4 space-y-3">
        {stored.length === 0 && <div className="text-sm text-gray-500">No quotes created yet.</div>}
        {stored.map((q:any)=> (
          <div key={q.quote_id} className="p-3 border rounded bg-white flex justify-between items-center">
            <div>
              <div className="font-medium">{q.quote_id}</div>
              <div className="text-sm text-gray-500">Status: {q.status}</div>
            </div>
            <div>
              <a className="text-indigo-600" href={`/app/quotes/${q.quote_id}`}>View</a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
