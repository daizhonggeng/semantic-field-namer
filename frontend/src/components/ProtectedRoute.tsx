import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../app/AuthContext'

export function ProtectedRoute() {
  const { token, loading } = useAuth()

  if (loading) {
    return <div style={{ padding: 48 }}>Loading...</div>
  }
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
