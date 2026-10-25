import { Navigate, Route, Routes } from 'react-router-dom'
import ChatTestPage from '../pages/ChatTestPage'
import ProductsPage from '../pages/ProductsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/products" replace />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/chat" element={<ChatTestPage />} />
    </Routes>
  )
}
