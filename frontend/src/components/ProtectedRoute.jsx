import { Navigate } from 'react-router'

function ProtectedRoute({ children }) {
  const accessToken = localStorage.getItem('accessToken')

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute