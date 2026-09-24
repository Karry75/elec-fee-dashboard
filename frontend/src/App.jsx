import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import MainBoard from './pages/MainBoard.jsx'
import ElecBoard from './pages/ElecBoard.jsx'
import Merchant from './pages/Merchant.jsx'
import Expense from './pages/Expense.jsx'
import Scan from './pages/Scan.jsx'
import Pending from './pages/Pending.jsx'
import Cancel from './pages/Cancel.jsx'

export default function App() {
  return (
    <Routes>
      {/* Scan page is mobile-first and rendered without the admin sidebar */}
      <Route path="/scan" element={<Scan />} />
      <Route element={<Layout />}>
        <Route path="/" element={<MainBoard />} />
        <Route path="/board" element={<ElecBoard />} />
        <Route path="/merchant" element={<Merchant />} />
        <Route path="/expense" element={<Expense />} />
        <Route path="/pending" element={<Pending />} />
        <Route path="/cancel" element={<Cancel />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
