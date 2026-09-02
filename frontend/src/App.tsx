import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import LoginDemo from './pages/LoginDemo'
import Catalog from './pages/Catalog'
import AppLayout from './layouts/AppLayout'

export default function App(){
  return (
    <Routes>
      <Route path="/" element={<Landing/>} />
      <Route path="/login" element={<LoginDemo/>} />

      <Route path="/app" element={<AppLayout/>}>
        <Route index element={<Navigate to="catalog" replace />} />
        <Route path="catalog" element={<Catalog/>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
