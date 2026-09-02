import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import LoginDemo from './pages/LoginDemo'
import Catalog from './pages/Catalog'
import AppLayout from './layouts/AppLayout'
import QuoteCreate from './pages/QuoteCreate'
import QuotesList from './pages/QuotesList'
import QuoteDetail from './pages/QuoteDetail'
import Payments from './pages/Payments'
import Agent from './pages/Agent'

export default function App(){
  return (
    <Routes>
      <Route path="/" element={<Landing/>} />
      <Route path="/login" element={<LoginDemo/>} />

      <Route path="/app" element={<AppLayout/>}>
        <Route index element={<Navigate to="catalog" replace />} />
        <Route path="catalog" element={<Catalog/>} />
        <Route path="quote/create" element={<QuoteCreate/>} />
        <Route path="quotes" element={<QuotesList/>} />
        <Route path="quotes/:quoteId" element={<QuoteDetail/>} />
        <Route path="payments" element={<Payments/>} />
        <Route path="agent" element={<Agent/>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
