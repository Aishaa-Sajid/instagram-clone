import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { login, extractApiError } from '@/api/auth'
import { AuthShell } from './AuthShell'

export function LoginForm() {
  usePageTitle('Log in')
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isLoading) return
    setError(null)
    setIsLoading(true)
    try {
      await login({ email, password })
      const from = location.state?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (err) {
      setError(extractApiError(err, 'Invalid credentials'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthShell>
      <h1 className="h3 fw-bold mb-4">Log in</h1>

      <form onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="alert alert-danger py-2" role="alert">
            {error}
          </div>
        )}

        <div className="mb-3">
          <label htmlFor="email" className="form-label fw-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="form-control"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="email"
          />
        </div>

        <div className="mb-3">
          <label htmlFor="password" className="form-label fw-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="form-control"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="current-password"
          />
        </div>

        <div className="form-check mb-4">
          <input id="remember" type="checkbox" className="form-check-input" />
          <label htmlFor="remember" className="form-check-label">
            Remember me
          </label>
        </div>

        <button type="submit" className="btn btn-dark w-100 mb-4" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Log in'}
        </button>
      </form>

      <div className="text-center mb-3">
        <Link to="/forgot-password" className="text-dark fw-medium text-decoration-none">
          Forgot your password?
        </Link>
      </div>

      <div className="text-center text-secondary small">
        Don&apos;t have an account?{' '}
        <Link to="/signup" className="text-dark fw-semibold text-decoration-none">
          Sign up
        </Link>
      </div>
    </AuthShell>
  )
}
