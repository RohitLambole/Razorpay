import React from 'react'

export default function Landing(){
  return (
    <div className="min-h-screen flex flex-col">
      <header className="py-6 px-8 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-sky-400 rounded-md" />
          <h1 className="text-2xl font-semibold">Agentic Commerce</h1>
        </div>
        <div>
          <a href="/login" className="text-sm font-medium text-indigo-600">Demo Login</a>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-5xl w-full grid grid-cols-2 gap-10 items-center">
          <div>
            <h2 className="text-4xl font-extrabold leading-tight">Commerce that understands what you want.</h2>
            <p className="mt-4 text-gray-600">Agentic Commerce lets intelligent agents discover products, generate intelligent quotes, obtain approvals, and initiate secure payments — all with auditable traces and merchant controls.</p>
            <div className="mt-6 flex gap-4">
              <a href="/login" className="px-6 py-3 bg-indigo-600 text-white rounded-md shadow">Try demo</a>
              <a href="#how" className="px-6 py-3 border rounded-md">How it works</a>
            </div>

            <section id="how" className="mt-10">
              <ol className="space-y-4">
                <li className="flex items-start gap-4"><div className="w-8 h-8 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center">1</div><div><strong>Intent</strong> — Describe what you need.</div></li>
                <li className="flex items-start gap-4"><div className="w-8 h-8 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center">2</div><div><strong>Discovery</strong> — Agent finds matching products.</div></li>
                <li className="flex items-start gap-4"><div className="w-8 h-8 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center">3</div><div><strong>Quote</strong> — Intelligent pricing with approval flows.</div></li>
                <li className="flex items-start gap-4"><div className="w-8 h-8 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center">4</div><div><strong>Payment</strong> — Secure link-based payments via Razorpay.</div></li>
              </ol>
            </section>
          </div>
          <div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="font-semibold">Live preview</h3>
              <div className="mt-4 space-y-3">
                <div className="p-4 border rounded">Agent: "Find 5 units of Demo Product 3"</div>
                <div className="p-4 border rounded">Agent: Suggests Demo Product 3 — price ₹100 each</div>
                <div className="p-4 border rounded">Quote: subtotal ₹500 → requested discount 20% → final ₹400</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="py-6 text-center text-sm text-gray-500">Agentic Commerce — Demo</footer>
    </div>
  )
}
