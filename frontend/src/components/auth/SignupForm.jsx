import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { signup, extractApiError } from '@/api/auth'
import { AuthShell } from './AuthShell'

export function SignupForm() {
  usePageTitle('Sign up')
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isPrivate, setIsPrivate] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isLoading) return
    setError(null)
    setIsLoading(true)
    try {
      await signup({ email, username, password, isPrivate })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 1500)
    } catch (err) {
      setError(extractApiError(err, 'Sign up failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthShell>
      <h1 className="h3 fw-bold mb-4">Sign up</h1>

      <form onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="alert alert-danger py-2" role="alert">
            {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success py-2" role="alert">
            Account created. Check your email to verify, then log in.
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
          <label htmlFor="username" className="form-label fw-medium">
            Username
          </label>
          <input
            id="username"
            type="text"
            className="form-control"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="username"
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
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="new-password"
          />
        </div>

        <div className="form-check mb-4">
          <input
            id="isPrivate"
            type="checkbox"
            className="form-check-input"
            checked={isPrivate}
            onChange={(e) => setIsPrivate(e.target.checked)}
            disabled={isLoading}
          />
          <label htmlFor="isPrivate" className="form-check-label">
            Make my account private
          </label>
        </div>

        <button type="submit" className="btn btn-dark w-100 mb-4" disabled={isLoading}>
          {isLoading ? 'Creating account...' : 'Sign up'}
        </button>
      </form>

      <div className="text-center text-secondary small">
        Already have an account?{' '}
        <Link to="/login" className="text-dark fw-semibold text-decoration-none">
          Log in
        </Link>
      </div>
    </AuthShell>
  )
}
