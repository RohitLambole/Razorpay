import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { useDemoAuth } from '../hooks/useDemoAuth'

function Sidebar(){
  return (
    <div className="w-64 bg-gray-50 border-r p-4">
      <h3 className="font-bold text-lg">Agentic</h3>
      <nav className="mt-6 space-y-2">
        <Link to="/app/catalog" className="block px-3 py-2 rounded hover:bg-gray-100">Catalog</Link>
        <Link to="/app/quotes" className="block px-3 py-2 rounded hover:bg-gray-100">Quotes</Link>
        <Link to="/app/payments" className="block px-3 py-2 rounded hover:bg-gray-100">Payments</Link>
        <Link to="/app/agent" className="block px-3 py-2 rounded hover:bg-gray-100">Agent</Link>
      </nav>
    </div>
  )
}

export default function AppLayout(){
  const { userName } = useDemoAuth()
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1">
        <header className="flex justify-between items-center p-4 border-b bg-white">
          <div>Welcome{userName?`, ${userName}`:''}</div>
          <div className="text-sm text-gray-500">Demo mode</div>
        </header>
        <main className="p-6 bg-gray-100 min-h-[calc(100vh-64px)]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
