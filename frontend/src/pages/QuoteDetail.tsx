import React from 'react'
import { useParams } from 'react-router-dom'
import { formatINR } from '../utils/currency'
import Button from '../components/ui/Button'
import { approveQuote } from '../api/quotes'
import { useDemoAuth } from '../hooks/useDemoAuth'

export default function QuoteDetail(){
  const { quoteId } = useParams()
  const { merchantId } = useDemoAuth()

  // Try to find created quote in localStorage
  const stored = JSON.parse(localStorage.getItem('created_quotes')||'[]')
  const quote = stored.find((q:any)=> q.quote_id === quoteId)

  async function handleApprove(){
    try{
      await approveQuote(quoteId!, {approver_id: 'demo-approver', approve: true})
      alert('Approved (server requested). Refresh to update. Note: backend update requires list/detail endpoints to re-query.')
    }catch(e:any){
      alert('Approve failed: '+e.message)
    }
  }

  if(!quote){
    return <div className="p-4 bg-white border rounded">Quote not found locally. This app currently stores created quotes in your browser session. If you created this quote elsewhere, the backend lacks a quote-detail API to fetch arbitrary quotes.</div>
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Quote {quote.quote_id}</h2>
      <div className="mt-4 bg-white p-4 border rounded">
        <div>Status: <strong>{quote.status}</strong></div>
        <div className="mt-2">Final amount: <strong>{formatINR(quote.final_amount_cents)}</strong></div>
        <div className="mt-2">Requested discount: {quote.payload.requested_discount_percent}%</div>
        <div className="mt-4">
          {quote.status === 'pending_approval' && (
            <Button onClick={handleApprove}>Approve (demo)</Button>
          )}
          {quote.status === 'approved' && (
            <div className="text-green-600">Quote approved — you can create a payment from the Payments screen.</div>
          )}
        </div>
      </div>
    </div>
  )
}
