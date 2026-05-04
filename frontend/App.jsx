import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import { isAuthenticated } from './lib/auth'

function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <h1 className="text-2xl font-semibold">Logged in. Feed coming soon.</h1>
    </div>
  )
}

function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/accounts/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/accounts/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Home />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/accounts/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
